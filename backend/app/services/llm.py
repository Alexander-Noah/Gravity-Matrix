from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from app.core.config import settings
from app.models.project import Project
from app.schemas.screenplay import ScreenplayDocument


DETAIL_LEVELS = {"brief", "standard", "detailed"}
FAST_LOCAL_ANALYSIS_CHAR_LIMIT = 12_000
AI_CHAPTER_PROMPT_CHAR_LIMIT = 1_600
OMITTED_REASONS = {
    "brief": "已省略非关键细节、重复心理描写和背景解释。",
    "standard": "已压缩支线细节和重复背景说明，保留主要场景、冲突和关键对白。",
    "detailed": "尽量保留原文主要场景和对白，仅压缩重复说明和难以剧本化的背景叙述。",
}

logger = logging.getLogger(__name__)


class AIParseError(RuntimeError):
    """Raised when AI parsing or validation fails."""


@dataclass(frozen=True)
class LLMResult:
    provider: str
    content: dict[str, Any]
    fallback_reason: str | None = None


def analyze_project(project: Project) -> LLMResult:
    _require_llm_config()
    source_chars = sum(len(chapter.content or "") for chapter in project.chapters)
    logger.info(
        "AI analysis started project_id=%s text_chars=%s chapters=%s real_ai=%s mock_fallback=%s",
        getattr(project, "id", None),
        source_chars,
        len(project.chapters),
        True,
        False,
    )

    if source_chars > FAST_LOCAL_ANALYSIS_CHAR_LIMIT:
        fallback_reason = "小说正文较长，已使用本地快速解析，避免 AI 长时间等待。"
        content = _local_project_analysis(project)
    else:
        result = _call_deepseek(
            _project_analysis_prompt(project),
            timeout_seconds=min(settings.llm_timeout_seconds, 12),
        )
        if _is_valid_project_analysis(result):
            content = _normalize_project_analysis(result)
            fallback_reason = None
        else:
            fallback_reason = "AI 返回超时或格式不完整，已使用本地快速解析兜底。"
            content = _local_project_analysis(project)

    if fallback_reason:
        logger.warning(
            "AI analysis fallback project_id=%s reason=%s",
            getattr(project, "id", None),
            fallback_reason,
        )

    chapter_results = content["chapter_analyses"]
    scene_count = sum(len(item.get("analysis", {}).get("events", []) or []) for item in chapter_results)
    logger.info(
        "AI analysis completed project_id=%s characters=%s locations=%s scenes=%s mock_fallback=%s",
        getattr(project, "id", None),
        len(content["characters"]),
        len(content["locations"]),
        scene_count,
        fallback_reason is not None,
    )
    return LLMResult(provider=settings.llm_provider, content=content, fallback_reason=fallback_reason)


def generate_screenplay(project: Project, analysis: dict[str, Any] | None = None) -> LLMResult:
    _require_llm_config()
    generation_settings = _project_generation_settings(project)
    detail_level = _detail_level(generation_settings)
    if analysis is None:
        raise AIParseError("AI 解析失败，请重试：请先完成第 2 步 AI 解析。")
    source_analysis = analysis
    if not _is_valid_global_analysis(source_analysis):
        raise AIParseError("AI 解析失败，请重试：缺少可用的人物或地点解析结果。")
    logger.info(
        "AI screenplay generation started project_id=%s detail_level=%s analysis_characters=%s analysis_locations=%s mock_fallback=%s",
        getattr(project, "id", None),
        detail_level,
        len(source_analysis.get("characters", []) or []),
        len(source_analysis.get("locations", []) or []),
        False,
    )

    result = _call_deepseek(_screenplay_prompt(project, source_analysis, generation_settings, detail_level))
    if not isinstance(result, dict):
        raise AIParseError("AI 解析失败，请重试：剧本生成结果不是有效 JSON。")

    errors = _validate_screenplay_result(result)
    if errors:
        raise AIParseError("AI 解析失败，请重试：" + "；".join(errors))

    scene_count = sum(len(chapter.get("scenes", []) or []) for chapter in result.get("script", {}).get("chapters", []) or [])
    logger.info(
        "AI screenplay generation completed project_id=%s scenes=%s mock_fallback=%s",
        getattr(project, "id", None),
        scene_count,
        False,
    )
    return LLMResult(provider=settings.llm_provider, content=result)


def _require_llm_config() -> None:
    if not (settings.llm_api_key and settings.llm_base_url and settings.llm_model):
        raise AIParseError("AI 服务未配置，请检查 API Key 或模型配置")


def _call_deepseek(prompt: str, timeout_seconds: int | None = None) -> dict[str, Any] | None:
    try:
        client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            timeout=timeout_seconds or settings.llm_timeout_seconds,
        )
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "你是小说结构化解析器。严格返回 JSON，不要输出解释、Markdown 或代码块。",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        content = response.choices[0].message.content
        if not content:
            return None
        parsed = _parse_json_object(content)
    except Exception as exc:
        logger.warning("LLM call failed: %s", exc)
        return None
    return parsed if isinstance(parsed, dict) else None


def _parse_json_object(content: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    cleaned = content.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end <= start:
        return None

    try:
        parsed = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _project_analysis_prompt(project: Project) -> str:
    template = {
        "chapter_analyses": [
            {
                "chapter_number": 1,
                "source_title": "章节标题",
                "analysis": {
                    "chapter_title": "章节标题",
                    "characters": [
                        {"name": "人物名", "aliases": [], "role": "角色", "description": "", "evidence": ""}
                    ],
                    "locations": [{"name": "地点名", "description": "", "evidence": ""}],
                    "organizations": [{"name": "组织名", "description": "", "evidence": ""}],
                    "events": [
                        {
                            "title": "事件标题",
                            "summary": "事件摘要",
                            "characters": ["人物名"],
                            "location": "地点名",
                            "evidence": "",
                        }
                    ],
                    "dialogues": [
                        {
                            "speaker": "人物名",
                            "line": "对白",
                            "line_type": "dialogue",
                            "emotion": "neutral",
                            "evidence": "",
                        }
                    ],
                },
            }
        ],
        "characters": [{"id": "char_001", "name": "人物名", "aliases": [], "role": "角色", "description": ""}],
        "locations": [{"id": "loc_001", "name": "地点名", "description": ""}],
        "organizations": [{"id": "org_001", "name": "组织名", "description": ""}],
        "alias_map": [{"alias": "别名", "canonical": "人物名", "evidence": "", "confidence": 0.95}],
        "themes": [],
        "conflicts": [],
    }
    chapters = [
        {
            "number": chapter.number,
            "title": chapter.title,
            "content": _prompt_chapter_text(chapter.content),
        }
        for chapter in project.chapters
    ]
    return "\n".join(
        [
            "你是小说结构化解析器。",
            "请一次性完成整本小说的结构化解析，避免逐章多轮往返。",
            "必须严格返回 JSON 对象，不要输出解释、Markdown 或代码块。",
            "",
            "要求：",
            "1. chapter_analyses 必须包含每个输入章节的解析。",
            "2. characters 和 locations 是全局合并后的实体，必须带 id 和 name。",
            "3. 不要把动作短语、地点、组织、普通名词识别成人物。",
            "4. 对白 line_type 只能是 dialogue、monologue 或 narration。",
            "5. 无法确认说话人时 speaker 为 null。",
            "",
            "返回 JSON 必须符合这个结构：",
            json.dumps(template, ensure_ascii=False),
            "",
            f"小说标题：{project.title}",
            f"作者：{project.author or '未知'}",
            "章节：",
            json.dumps(chapters, ensure_ascii=False),
        ]
    )


def _prompt_chapter_text(text: str) -> str:
    compact = re.sub(r"\s+", "\n", text or "").strip()
    if len(compact) <= AI_CHAPTER_PROMPT_CHAR_LIMIT:
        return compact
    head_length = int(AI_CHAPTER_PROMPT_CHAR_LIMIT * 0.75)
    tail_length = AI_CHAPTER_PROMPT_CHAR_LIMIT - head_length
    return f"{compact[:head_length]}\n...[中间内容已压缩]...\n{compact[-tail_length:]}"


def _chapter_analysis_prompt(chapter_number: int, chapter_title: str, chapter_text: str) -> str:
    template = {
        "chapter_title": "",
        "characters": [
            {
                "name": "",
                "aliases": [],
                "role": "",
                "description": "",
                "evidence": "",
            }
        ],
        "locations": [
            {
                "name": "",
                "description": "",
                "evidence": "",
            }
        ],
        "organizations": [
            {
                "name": "",
                "description": "",
                "evidence": "",
            }
        ],
        "events": [
            {
                "title": "",
                "summary": "",
                "characters": [],
                "location": "",
                "evidence": "",
            }
        ],
        "dialogues": [
            {
                "speaker": "",
                "line": "",
                "line_type": "dialogue",
                "emotion": "",
                "evidence": "",
            }
        ],
    }
    return "\n".join(
        [
            "你是小说结构化解析器。",
            "",
            "请从当前章节文本中识别人物、地点、组织、剧情事件和对白。",
            "",
            "要求：",
            "1. 只识别真实人物，不要把动作短语、地点、组织、普通名词识别成人物。",
            "2. 如果出现“陈某反驳道”“中年男人回道”“少女淡淡道”这类表达，请理解真正说话人，不要把动作词并入人物名。",
            "3. 地点、组织、人物必须区分清楚。",
            "4. 如果同一人物有多个称呼，请放入 aliases。",
            "5. 对白尽量保留原文。",
            "6. 心理活动标记为 monologue。",
            "7. 旁白叙述标记为 narration。",
            "8. 不确定说话人时 speaker 为 null。",
            "9. 严格返回 JSON，不要输出解释。",
            "",
            "返回 JSON 必须符合这个结构：",
            json.dumps(template, ensure_ascii=False),
            "",
            f"章节编号：{chapter_number}",
            f"章节标题：{chapter_title}",
            "章节文本：",
            chapter_text,
        ]
    )


def _global_merge_prompt(project: Project, chapter_results: list[dict[str, Any]]) -> str:
    template = {
        "characters": [
            {
                "id": "char_001",
                "name": "",
                "aliases": [],
                "role": "",
                "description": "",
            }
        ],
        "locations": [
            {
                "id": "loc_001",
                "name": "",
                "description": "",
            }
        ],
        "organizations": [
            {
                "id": "org_001",
                "name": "",
                "description": "",
            }
        ],
        "alias_map": [
            {
                "alias": "",
                "canonical": "",
                "evidence": "",
                "confidence": 0.95,
            }
        ],
        "themes": [],
        "conflicts": [],
    }
    return "\n".join(
        [
            "请对所有章节解析结果做全局实体合并。",
            "要求：",
            "1. 合并同一人物的不同称呼。",
            "2. 合并同一地点的不同称呼。",
            "3. 不允许 characters 和 locations 重复。",
            "4. 不允许把地点、组织、普通物品放进 characters。",
            "5. 不允许写死任何当前测试小说的人名和地点，只能依据输入证据。",
            "6. 严格返回 JSON，不要输出解释。",
            "",
            "返回 JSON 必须符合这个结构：",
            json.dumps(template, ensure_ascii=False),
            "",
            f"小说标题：{project.title}",
            f"作者：{project.author or '未知'}",
            "章节解析结果：",
            json.dumps(chapter_results, ensure_ascii=False),
        ]
    )


def _screenplay_prompt(
    project: Project,
    analysis: dict[str, Any],
    generation_settings: dict[str, Any],
    detail_level: str,
) -> str:
    template = _template_profile(generation_settings.get("templateId"))
    screenplay_template = _screenplay_json_template(project, generation_settings, detail_level)
    return "\n".join(
        [
            "请基于全局 characters、locations 和章节解析结果生成剧本结构。",
            "后端不会替你识别人名、地点、场景或对白归属，所以你必须在本次输出中保证引用正确。",
            "",
            "生成要求：",
            "1. 顶层必须是 JSON 对象，包含 script 字段；不要输出 YAML、Markdown 或解释。",
            "2. scene title 由你总结，不要直接截断原文。",
            "3. scene.characters 必须来自全局 characters 的 id。",
            "4. scene.location_id 必须来自全局 locations 的 id。",
            "5. dialogue.speaker_id 必须来自全局 characters 的 id，无法确认则为 null，speaker_name 为“旁白”。",
            "6. 尽量使用原文真实对白。",
            "7. 心理描写可以转为 monologue。",
            "8. 旁白叙述可以转为 narration。",
            "9. 不要生成模板化假对白。",
            f"10. detail_level={detail_level}；brief 为概要剧本，standard 为标准剧本，detailed 为详细剧本。",
            "",
            f"模板：{template['name']} target_format={template['target_format']}",
            f"生成设置：{json.dumps(generation_settings, ensure_ascii=False)}",
            "",
            "返回 JSON 必须符合这个结构：",
            json.dumps(screenplay_template, ensure_ascii=False),
            "",
            "全局解析结果：",
            json.dumps(_analysis_for_prompt(analysis), ensure_ascii=False),
            "",
            "原文章节：",
            json.dumps(_chapters_for_prompt(project), ensure_ascii=False),
        ]
    )


def _screenplay_json_template(
    project: Project,
    generation_settings: dict[str, Any] | None = None,
    detail_level: str = "standard",
) -> dict[str, Any]:
    template = _template_profile((generation_settings or {}).get("templateId"))
    return {
        "script": {
            "schema_version": "1.0",
            "metadata": {
                "title": project.title,
                "original_novel": project.title,
                "author": project.author,
                "language": "zh-CN",
                "target_format": template["target_format"],
                "template_id": template["id"],
                "script_type": (generation_settings or {}).get("scriptType") or template["script_type"],
                "adaptation_style": (generation_settings or {}).get("adaptationStyle"),
                "total_chapters": len(project.chapters),
                "adaptation_mode": detail_level,
                "omitted_reason": OMITTED_REASONS[detail_level],
                "coverage": {
                    "source_chapters": len(project.chapters),
                    "generated_scenes": 0,
                    "preserved_dialogues": 0,
                    "adaptation_mode": detail_level,
                    "omitted_reason": OMITTED_REASONS[detail_level],
                },
            },
            "characters": [],
            "locations": [],
            "organizations": [],
            "chapters": [
                {
                    "id": "ch_001",
                    "title": "章节标题",
                    "source_chapter_numbers": [1],
                    "summary": "章节摘要",
                    "scenes": [
                        {
                            "id": "sc_001_001",
                            "title": "场景标题",
                            "location_id": "loc_001",
                            "time": "时间",
                            "characters": ["char_001"],
                            "synopsis": "场景概要",
                            "source_range": {
                                "chapter": 1,
                                "start_hint": "原文起始短句",
                                "end_hint": "原文结束短句",
                            },
                            "stage_directions": ["舞台或镜头调度"],
                            "dialogue": [
                                {
                                    "speaker_id": "char_001",
                                    "speaker_name": "人物名",
                                    "line": "原文对白或改编对白",
                                    "emotion": "neutral",
                                    "line_type": "dialogue",
                                }
                            ],
                        }
                    ],
                }
            ],
            "adaptation_notes": {
                "themes": [],
                "conflicts": [],
                "omissions": [OMITTED_REASONS[detail_level]],
                "template_rules": template["rules"],
            },
        }
    }


def _is_valid_chapter_analysis(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    required_lists = ("characters", "locations", "events", "dialogues")
    if not all(isinstance(data.get(key), list) for key in required_lists):
        return False
    for line in data.get("dialogues", []):
        if not isinstance(line, dict):
            return False
        if line.get("line_type") not in {"dialogue", "monologue", "narration"}:
            return False
    return True


def _is_valid_global_analysis(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    characters = data.get("characters")
    locations = data.get("locations")
    if not isinstance(characters, list) or not isinstance(locations, list):
        return False
    if not characters or not locations:
        return False
    if not all(isinstance(item, dict) and item.get("id") and item.get("name") for item in characters):
        return False
    if not all(isinstance(item, dict) and item.get("id") and item.get("name") for item in locations):
        return False
    character_names = {item["name"] for item in characters}
    location_names = {item["name"] for item in locations}
    return character_names.isdisjoint(location_names)


def _is_valid_project_analysis(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    chapter_analyses = data.get("chapter_analyses")
    if not isinstance(chapter_analyses, list) or not chapter_analyses:
        return False
    for item in chapter_analyses:
        if not isinstance(item, dict) or not _is_valid_chapter_analysis(item.get("analysis")):
            return False
    return _is_valid_global_analysis(data)


def _normalize_project_analysis(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": "ai",
        "chapter_analyses": data.get("chapter_analyses", []),
        "characters": data.get("characters", []),
        "locations": data.get("locations", []),
        "organizations": data.get("organizations", []),
        "alias_map": data.get("alias_map", []),
        "candidate_aliases": data.get("alias_map", []),
        "themes": data.get("themes", []),
        "conflicts": data.get("conflicts", []),
    }


def _local_project_analysis(project: Project) -> dict[str, Any]:
    chapter_analyses = []
    character_names: list[str] = []
    location_names: list[str] = []
    organizations: list[dict[str, Any]] = []

    for chapter in project.chapters:
        analysis = _local_chapter_analysis(chapter.number, chapter.title, chapter.content)
        chapter_analyses.append(
            {
                "chapter_number": chapter.number,
                "source_title": chapter.title,
                "analysis": analysis,
            }
        )
        character_names.extend(item["name"] for item in analysis["characters"])
        location_names.extend(item["name"] for item in analysis["locations"])
        organizations.extend(analysis.get("organizations", []))

    characters = [
        {
            "id": f"char_{index:03d}",
            "name": name,
            "aliases": [],
            "role": "角色",
            "description": "本地快速解析识别的人物。",
        }
        for index, name in enumerate(_unique(character_names) or ["旁白"], start=1)
    ]
    locations = [
        {
            "id": f"loc_{index:03d}",
            "name": name,
            "description": "本地快速解析识别的地点。",
        }
        for index, name in enumerate(_unique(location_names) or ["未明确地点"], start=1)
    ]
    return {
        "source": "local_fallback",
        "chapter_analyses": chapter_analyses,
        "characters": characters,
        "locations": locations,
        "organizations": [
            {
                "id": f"org_{index:03d}",
                "name": item["name"],
                "description": item.get("description") or "本地快速解析识别的组织。",
            }
            for index, item in enumerate(_unique_dicts(organizations, "name"), start=1)
        ],
        "alias_map": [],
        "candidate_aliases": [],
        "themes": ["小说改编", "人物冲突"],
        "conflicts": ["主角目标与外部阻碍之间的冲突"],
    }


def _local_chapter_analysis(chapter_number: int, title: str, content: str) -> dict[str, Any]:
    speakers = _extract_speakers(content)
    fallback_names = _extract_likely_names(content)
    characters = _unique(speakers + fallback_names)[:12]
    locations = _extract_locations(content)[:8]
    dialogues = _extract_dialogues(content)
    summary = _compact_text(content, 90)
    event_characters = characters[:4]
    event_location = locations[0] if locations else "未明确地点"
    return {
        "chapter_title": title,
        "characters": [
            {
                "name": name,
                "aliases": [],
                "role": "角色",
                "description": f"第 {chapter_number} 章出现的人物。",
                "evidence": name,
            }
            for name in characters
        ],
        "locations": [
            {
                "name": location,
                "description": f"第 {chapter_number} 章出现的地点。",
                "evidence": location,
            }
            for location in locations
        ],
        "organizations": [],
        "events": [
            {
                "title": title,
                "summary": summary,
                "characters": event_characters,
                "location": event_location,
                "evidence": _compact_text(content, 40),
            }
        ],
        "dialogues": dialogues,
    }


def _extract_dialogues(text: str) -> list[dict[str, Any]]:
    dialogues = []
    patterns = [
        re.compile(r"(?P<speaker>[\u4e00-\u9fffA-Za-z0-9_]{1,8})(?:说道|说|道|问道|答道|喊道|喝道|低声道|沉声道|笑道|怒道)[:：]?[“\"](?P<line>[^”\"]{1,120})[”\"]"),
        re.compile(r"[“\"](?P<line>[^”\"]{1,120})[”\"](?P<speaker>[\u4e00-\u9fffA-Za-z0-9_]{1,8})(?:说道|说|道|问道|答道|喊道|喝道|低声道|沉声道|笑道|怒道)"),
    ]
    for pattern in patterns:
        for match in pattern.finditer(text):
            speaker = _clean_name(match.group("speaker"))
            line = match.group("line").strip()
            if not speaker or not line:
                continue
            dialogues.append(
                {
                    "speaker": speaker,
                    "line": line,
                    "line_type": "dialogue",
                    "emotion": "neutral",
                    "evidence": line[:40],
                }
            )
    if not dialogues:
        dialogues.append(
            {
                "speaker": None,
                "line": _compact_text(text, 80),
                "line_type": "narration",
                "emotion": "neutral",
                "evidence": _compact_text(text, 40),
            }
        )
    return dialogues[:20]


def _extract_speakers(text: str) -> list[str]:
    names = []
    for pattern in [
        r"([\u4e00-\u9fffA-Za-z0-9_]{1,8})(?:说道|说|道|问道|答道|喊道|喝道|低声道|沉声道|笑道|怒道)",
        r"[“\"][^”\"]{1,120}[”\"]([\u4e00-\u9fffA-Za-z0-9_]{1,8})(?:说道|说|道|问道|答道|喊道|喝道|低声道|沉声道|笑道|怒道)",
    ]:
        names.extend(_clean_name(match) for match in re.findall(pattern, text))
    return [name for name in names if name]


def _extract_likely_names(text: str) -> list[str]:
    candidates = re.findall(r"[\u4e00-\u9fff]{2,4}", text)
    stop_words = {
        "第一章",
        "第二章",
        "第三章",
        "第四章",
        "第五章",
        "第六章",
        "一个",
        "他们",
        "我们",
        "这里",
        "那里",
        "没有",
        "什么",
        "时候",
        "自己",
        "众人",
    }
    names = []
    for item in candidates:
        if item in stop_words or item.startswith("第"):
            continue
        if any(suffix in item for suffix in ("府", "街", "城", "院", "监", "司", "堂", "桥", "河")):
            continue
        names.append(item)
    return names[:12]


def _extract_locations(text: str) -> list[str]:
    locations = []
    for match in re.findall(r"[\u4e00-\u9fff]{2,8}(?:府|街|城|院|监|司|堂|桥|河|客栈|书院|衙门|监牢|皇宫|山|门)", text):
        if not match.startswith("第"):
            locations.append(match)
    return _unique(locations)


def _clean_name(value: str | None) -> str | None:
    if not value:
        return None
    name = re.sub(r"[，。！？、：；“”\"'（）()\s]", "", value)
    name = re.sub(r"^(?:忽然|只见|却见|这时|随后|于是|但是|因为|如果|那个|这个)", "", name)
    if len(name) < 2 or len(name) > 8:
        return None
    if any(word in name for word in ("众人", "声音", "时候", "什么", "这里", "那里")):
        return None
    return name


def _compact_text(text: str, limit: int) -> str:
    compact = re.sub(r"\s+", "", text or "")
    return compact[:limit] if compact else "本章围绕主要人物与事件展开。"


def _unique(values: list[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _unique_dicts(values: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    result = []
    seen = set()
    for value in values:
        marker = value.get(key)
        if marker and marker not in seen:
            seen.add(marker)
            result.append(value)
    return result


def _validate_screenplay_result(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        document = ScreenplayDocument.model_validate(data)
    except (ValidationError, ValueError) as exc:
        return [f"剧本 Schema 校验失败：{exc}"]

    if not document.script.characters:
        errors.append("characters 不能为空。")
    if not document.script.locations:
        errors.append("locations 不能为空。")

    character_ids = {character.id for character in document.script.characters}
    location_ids = {location.id for location in document.script.locations}
    for chapter in document.script.chapters:
        for scene in chapter.scenes:
            if scene.location_id not in location_ids:
                errors.append(f"scene {scene.id} 的 location_id 不存在。")
            for character_id in scene.characters:
                if character_id not in character_ids:
                    errors.append(f"scene {scene.id} 引用了不存在的人物 {character_id}。")
            for line in scene.dialogue:
                if line.speaker_id is not None and line.speaker_id not in character_ids:
                    errors.append(f"scene {scene.id} 的对白引用了不存在的 speaker_id {line.speaker_id}。")
    return errors


def _project_generation_settings(project: Project) -> dict[str, Any]:
    raw = getattr(project, "generation_settings_json", None)
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _detail_level(settings_data: dict[str, Any]) -> str:
    value = str(settings_data.get("detail_level") or settings_data.get("detailLevel") or "standard")
    return value if value in DETAIL_LEVELS else "standard"


def _template_profile(template_id: str | None) -> dict[str, Any]:
    profiles = {
        "tv-drama": {
            "id": "tv-drama",
            "name": "影视剧剧本模板",
            "target_format": "screenplay",
            "script_type": "影视剧",
            "rules": ["由 AI 完成场景拆分", "由 AI 完成对白归属", "由后端校验引用关系"],
        },
        "short-drama": {
            "id": "short-drama",
            "name": "短剧剧本模板",
            "target_format": "short_drama",
            "script_type": "短剧",
            "rules": ["由 AI 强化冲突和钩子", "由 AI 保留关键对白", "由后端校验引用关系"],
        },
        "stage-play": {
            "id": "stage-play",
            "name": "话剧剧本模板",
            "target_format": "stage_play",
            "script_type": "话剧",
            "rules": ["由 AI 生成舞台调度", "由 AI 处理入场退场", "由后端校验引用关系"],
        },
        "storyboard": {
            "id": "storyboard",
            "name": "分镜剧本模板",
            "target_format": "storyboard",
            "script_type": "分镜剧本",
            "rules": ["由 AI 生成镜头化场景", "由 AI 标注画面重点", "由后端校验引用关系"],
        },
        "audio-drama": {
            "id": "audio-drama",
            "name": "广播剧剧本模板",
            "target_format": "audio_drama",
            "script_type": "广播剧",
            "rules": ["由 AI 强化声音调度", "由 AI 区分旁白和对白", "由后端校验引用关系"],
        },
    }
    return profiles.get(template_id or "tv-drama", profiles["tv-drama"])


def _analysis_for_prompt(analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "characters": analysis.get("characters", []),
        "locations": analysis.get("locations", []),
        "organizations": analysis.get("organizations", []),
        "alias_map": analysis.get("alias_map") or analysis.get("candidate_aliases", []),
        "chapter_analyses": analysis.get("chapter_analyses", []),
        "themes": analysis.get("themes", []),
        "conflicts": analysis.get("conflicts", []),
    }


def _chapters_for_prompt(project: Project) -> list[dict[str, Any]]:
    return [
        {
            "number": chapter.number,
            "title": chapter.title,
            "content": chapter.content,
        }
        for chapter in project.chapters
    ]

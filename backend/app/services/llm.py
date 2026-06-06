from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from app.core.config import settings
from app.models.project import Chapter, Project
from app.schemas.screenplay import ScreenplayDocument


@dataclass(frozen=True)
class LLMResult:
    provider: str
    content: dict
    fallback_reason: str | None = None


def analyze_project(project: Project) -> LLMResult:
    if _has_llm_config():
        result = _call_deepseek(_analysis_prompt(project))
        if isinstance(result, dict) and _is_valid_analysis(result):
            return LLMResult(provider=settings.llm_provider, content=_normalize_analysis(result))
        return _demo_analyze_project(project, "invalid_analysis_response")

    return _demo_analyze_project(project, "missing_config")


def generate_screenplay(project: Project, analysis: dict | None = None) -> LLMResult:
    analysis = _normalize_analysis(analysis or analyze_project(project).content)
    generation_settings = _project_generation_settings(project)
    if _has_llm_config():
        result = _call_deepseek(_screenplay_prompt(project, analysis, generation_settings))
        if isinstance(result, dict) and _is_valid_screenplay(result):
            _apply_generation_metadata(result, generation_settings)
            return LLMResult(provider=settings.llm_provider, content=result)
        return _demo_generate_screenplay(project, analysis, "invalid_screenplay_response")

    return _demo_generate_screenplay(project, analysis, "missing_config")


def _demo_analyze_project(project: Project, fallback_reason: str | None = None) -> LLMResult:
    characters = _demo_characters(project)
    locations = [
        {
            "id": f"loc_{chapter.number:03d}",
            "name": f"第 {chapter.number} 章主要场景",
            "description": _brief(chapter.content, 80),
        }
        for chapter in project.chapters
    ]
    chapter_summaries = [
        {
            "chapter_number": chapter.number,
            "title": chapter.title,
            "summary": _brief(chapter.content, 160),
        }
        for chapter in project.chapters
    ]

    return LLMResult(
        provider="deterministic_demo",
        fallback_reason=fallback_reason,
        content={
            "characters": characters,
            "locations": locations,
            "chapter_summaries": chapter_summaries,
            "themes": ["成长", "选择"],
            "conflicts": ["角色目标与现实阻碍之间的冲突"],
        },
    )


def _demo_generate_screenplay(
    project: Project,
    analysis: dict | None = None,
    fallback_reason: str | None = None,
) -> LLMResult:
    analysis = _normalize_analysis(analysis or _demo_analyze_project(project).content)
    generation_settings = _project_generation_settings(project)
    template = _template_profile(generation_settings.get("templateId"))
    characters = analysis.get("characters") or _demo_characters(project)
    locations = analysis.get("locations") or [
        {"id": "loc_001", "name": "主要场景", "description": "由小说内容概括出的主要空间。"}
    ]

    chapters = [_chapter_to_script(chapter, locations, characters) for chapter in project.chapters]

    return LLMResult(
        provider="deterministic_demo",
        fallback_reason=fallback_reason,
        content={
            "script": {
                "schema_version": "1.0",
                "metadata": {
                    "title": project.title,
                    "original_novel": project.title,
                    "author": project.author,
                    "language": "zh-CN",
                    "target_format": template["target_format"],
                    "template_id": template["id"],
                    "script_type": generation_settings.get("scriptType") or template["script_type"],
                    "adaptation_style": generation_settings.get("adaptationStyle"),
                    "total_chapters": len(project.chapters),
                },
                "characters": characters,
                "locations": locations,
                "chapters": chapters,
                "adaptation_notes": {
                    "themes": analysis.get("themes", ["成长"]),
                    "conflicts": analysis.get("conflicts", ["角色目标与现实阻碍之间的冲突"]),
                    "omissions": ["当前版本保留章节主线，细节对白可由作者继续编辑打磨。"],
                    "template_rules": template["rules"],
                },
            }
        },
    )


def _has_llm_config() -> bool:
    return bool(settings.llm_api_key and settings.llm_base_url and settings.llm_model)


def _call_deepseek(prompt: str) -> dict[str, Any] | None:
    try:
        client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            timeout=settings.llm_timeout_seconds,
        )
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是专业的小说改编剧本助手。"
                        "必须只输出一个合法 JSON 对象，不要输出 Markdown、解释文字或代码块。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
        )
        content = response.choices[0].message.content
        if not content:
            return None
        parsed = json.loads(content)
    except Exception:
        return None

    return parsed if isinstance(parsed, dict) else None


def _analysis_prompt(project: Project) -> str:
    return "\n".join(
        [
            "请分析以下小说章节，并输出 JSON 对象。",
            "JSON 字段必须包含 characters、locations、chapter_summaries、themes、conflicts。",
            "characters 数组元素字段：id、name、role、gender、age、description。",
            "locations 数组元素字段：id、name、description。",
            "chapter_summaries 数组元素字段：chapter_number、title、summary。",
            "themes、conflicts 都是字符串数组。",
            "",
            f"小说标题：{project.title}",
            f"作者：{project.author or '未知'}",
            "",
            _chapters_for_prompt(project, per_chapter_limit=1200),
        ]
    )


def _screenplay_prompt(project: Project, analysis: dict, generation_settings: dict[str, Any]) -> str:
    template = _template_profile(generation_settings.get("templateId"))
    return "\n".join(
        [
            "请把小说改编为结构化剧本 JSON。",
            "必须输出顶层包含 script 字段的 JSON 对象，所有字段名必须使用下方模板中的英文 snake_case 字段名。",
            "不得省略模板中的任何必填字段；未知 age 必须输出 null，不要输出“未知”。",
            "scene.location_id 必须引用 locations 中已有 id；scene.characters 和 dialogue.speaker_id 必须引用 characters 中已有 id。",
            "每章只生成 1 到 2 个核心场景，不要把每个自然段都拆成场景。",
            "每个场景保留 2 到 4 句关键对白，优先覆盖核心冲突和人物选择。",
            "如果原文很长，请压缩支线细节，输出可编辑的剧本初稿，而不是全文逐段改写。",
            f"当前生成模板：{template['name']}（target_format={template['target_format']}）。",
            f"剧本类型：{generation_settings.get('scriptType') or template['script_type']}。",
            f"改编风格：{generation_settings.get('adaptationStyle') or '默认平衡'}。",
            f"内容选项：{'、'.join(generation_settings.get('contentOptions') or []) or '默认'}。",
            "模板生成规则：",
            *[f"- {rule}" for rule in template["rules"]],
            "不要输出 YAML，不要输出 Markdown。",
            "JSON 模板如下：",
            _screenplay_json_template(project, generation_settings),
            "",
            f"小说标题：{project.title}",
            f"作者：{project.author or '未知'}",
            f"分析结果 JSON：{json.dumps(_compact_analysis_for_prompt(analysis), ensure_ascii=False)}",
            "",
            _chapters_for_prompt(project, per_chapter_limit=700),
        ]
    )


def _screenplay_json_template(project: Project, generation_settings: dict[str, Any] | None = None) -> str:
    template_profile = _template_profile((generation_settings or {}).get("templateId"))
    template = {
        "script": {
            "schema_version": "1.0",
            "metadata": {
                "title": project.title,
                "original_novel": project.title,
                "author": project.author,
                "language": "zh-CN",
                "target_format": template_profile["target_format"],
                "template_id": template_profile["id"],
                "script_type": (generation_settings or {}).get("scriptType") or template_profile["script_type"],
                "adaptation_style": (generation_settings or {}).get("adaptationStyle"),
                "total_chapters": len(project.chapters),
            },
            "characters": [
                {
                    "id": "char_001",
                    "name": "人物名",
                    "role": "主角",
                    "gender": "unknown",
                    "age": None,
                    "description": "人物简介",
                }
            ],
            "locations": [
                {
                    "id": "loc_001",
                    "name": "地点名",
                    "description": "地点说明",
                }
            ],
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
                            "time": "day",
                            "characters": ["char_001"],
                            "synopsis": "场景概述",
                            "stage_directions": ["动作或画面说明"],
                            "dialogue": [
                                {
                                    "speaker_id": "char_001",
                                    "speaker_name": "人物名",
                                    "line": "台词",
                                    "emotion": "calm",
                                }
                            ],
                        }
                    ],
                }
            ],
            "adaptation_notes": {
                "themes": ["主题"],
                "conflicts": ["核心冲突"],
                "omissions": ["压缩或省略说明"],
            },
        }
    }
    return json.dumps(template, ensure_ascii=False)


def _project_generation_settings(project: Project) -> dict[str, Any]:
    raw = getattr(project, "generation_settings_json", None)
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _template_profile(template_id: str | None) -> dict[str, Any]:
    profiles = {
        "tv-drama": {
            "id": "tv-drama",
            "name": "影视剧剧本模板",
            "target_format": "screenplay",
            "script_type": "影视剧",
            "rules": ["按章节组织场景", "突出人物动作和对白", "每场保留可拍摄的地点、时间和调度"],
        },
        "short-drama": {
            "id": "short-drama",
            "name": "短剧剧本模板",
            "target_format": "short_drama",
            "script_type": "短剧",
            "rules": ["开场三秒给出冲突", "每章场景要有反转或钩子", "对白更短更直接"],
        },
        "stage-play": {
            "id": "stage-play",
            "name": "话剧剧本模板",
            "target_format": "stage_play",
            "script_type": "话剧",
            "rules": ["强化舞台调度和入退场", "减少不可舞台化的镜头描写", "对白承载更多心理变化"],
        },
        "storyboard": {
            "id": "storyboard",
            "name": "分镜剧本模板",
            "target_format": "storyboard",
            "script_type": "分镜剧本",
            "rules": ["场景标题尽量镜头化", "stage_directions 写景别、运动和画面重点", "对白服务镜头节奏"],
        },
        "audio-drama": {
            "id": "audio-drama",
            "name": "广播剧剧本模板",
            "target_format": "audio_drama",
            "script_type": "广播剧",
            "rules": ["用声音和环境音建立空间", "stage_directions 强调音效", "对白需要清晰区分人物身份"],
        },
    }
    return profiles.get(template_id or "tv-drama", profiles["tv-drama"])


def _apply_generation_metadata(result: dict[str, Any], generation_settings: dict[str, Any]) -> None:
    template = _template_profile(generation_settings.get("templateId"))
    script = result.get("script")
    if not isinstance(script, dict):
        return
    metadata = script.setdefault("metadata", {})
    if isinstance(metadata, dict):
        metadata["target_format"] = template["target_format"]
        metadata["template_id"] = template["id"]
        metadata["script_type"] = generation_settings.get("scriptType") or template["script_type"]
        metadata["adaptation_style"] = generation_settings.get("adaptationStyle")


def _chapters_for_prompt(project: Project, per_chapter_limit: int = 1200) -> str:
    parts = []
    for chapter in project.chapters:
        parts.append(
            "\n".join(
                [
                    f"第 {chapter.number} 章：{chapter.title}",
                    _brief(chapter.content, per_chapter_limit),
                ]
            )
        )
    return "\n\n".join(parts)


def _compact_analysis_for_prompt(analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "characters": [
            {
                "id": character.get("id"),
                "name": character.get("name"),
                "role": character.get("role"),
                "description": _brief(str(character.get("description", "")), 80),
            }
            for character in analysis.get("characters", [])[:6]
        ],
        "locations": [
            {
                "id": location.get("id"),
                "name": location.get("name"),
                "description": _brief(str(location.get("description", "")), 80),
            }
            for location in analysis.get("locations", [])[:10]
        ],
        "chapter_summaries": [
            {
                "chapter_number": chapter.get("chapter_number"),
                "title": chapter.get("title"),
                "summary": _brief(str(chapter.get("summary", "")), 100),
            }
            for chapter in analysis.get("chapter_summaries", [])[:30]
        ],
        "themes": analysis.get("themes", [])[:6],
        "conflicts": analysis.get("conflicts", [])[:6],
    }


def _is_valid_analysis(data: dict[str, Any]) -> bool:
    required_lists = ["characters", "locations", "chapter_summaries", "themes", "conflicts"]
    return all(isinstance(data.get(key), list) for key in required_lists)


def _normalize_analysis(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "characters": _normalize_characters(data.get("characters", [])),
        "locations": _normalize_locations(data.get("locations", [])),
        "chapter_summaries": data.get("chapter_summaries", []),
        "themes": _normalize_string_list(data.get("themes", [])),
        "conflicts": _normalize_string_list(data.get("conflicts", [])),
    }


def _normalize_characters(characters: Any) -> list[dict[str, Any]]:
    if not isinstance(characters, list):
        return []

    normalized = []
    for index, character in enumerate(characters, start=1):
        if not isinstance(character, dict):
            continue
        normalized.append(
            {
                "id": str(character.get("id") or f"char_{index:03d}"),
                "name": str(character.get("name") or f"角色{index}"),
                "role": str(character.get("role") or "配角"),
                "gender": str(character.get("gender") or "unknown"),
                "age": _normalize_age(character.get("age")),
                "description": str(character.get("description") or "由小说章节自动识别出的人物。"),
            }
        )
    return normalized


def _normalize_locations(locations: Any) -> list[dict[str, str]]:
    if not isinstance(locations, list):
        return []

    normalized = []
    for index, location in enumerate(locations, start=1):
        if not isinstance(location, dict):
            continue
        normalized.append(
            {
                "id": str(location.get("id") or f"loc_{index:03d}"),
                "name": str(location.get("name") or f"地点{index}"),
                "description": str(location.get("description") or "由小说章节自动识别出的场景地点。"),
            }
        )
    return normalized


def _normalize_string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(value) for value in values if value is not None]


def _normalize_age(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _is_valid_screenplay(data: dict[str, Any]) -> bool:
    try:
        ScreenplayDocument.model_validate(data)
    except (ValidationError, ValueError):
        return False
    return True


def _demo_characters(project: Project) -> list[dict[str, Any]]:
    names = _extract_character_names(project)
    if not names:
        names = ["主角", "重要角色"]
    elif len(names) == 1:
        names.append("重要角色")

    roles = ["主角", "重要角色", "重要角色"]
    return [
        {
            "id": f"char_{index:03d}",
            "name": name,
            "role": roles[min(index - 1, len(roles) - 1)],
            "gender": "unknown",
            "age": None,
            "description": "根据小说章节自动识别出的核心人物。",
        }
        for index, name in enumerate(names[:3], start=1)
    ]


def _extract_character_names(project: Project) -> list[str]:
    text = "\n".join(chapter.content for chapter in project.chapters)
    candidates: list[str] = []

    for match in re.finditer(r"([\u4e00-\u9fff]{2})、([\u4e00-\u9fff]{2})、([\u4e00-\u9fff]{2})", text):
        candidates.extend(match.groups())

    for match in re.finditer(r"([\u4e00-\u9fff]{2})(?:庄|在|率|与|和|同|向|说|道|问|答)", text):
        candidates.append(match.group(1))

    stopwords = {
        "天下",
        "大势",
        "东汉",
        "朝政",
        "群雄",
        "乱世",
        "黄巾",
        "朝廷",
        "豪杰",
        "国家",
        "黎庶",
        "小说",
        "章节",
    }
    seen = set()
    names = []
    for candidate in candidates:
        if candidate in stopwords or candidate in seen:
            continue
        seen.add(candidate)
        names.append(candidate)
    return names


def _chapter_to_script(chapter: Chapter, locations: list[dict], characters: list[dict]) -> dict:
    location = locations[min(chapter.number - 1, len(locations) - 1)]
    character = characters[0]
    supporting_character = characters[1] if len(characters) > 1 else character

    return {
        "id": f"ch_{chapter.number:03d}",
        "title": chapter.title,
        "source_chapter_numbers": [chapter.number],
        "summary": _brief(chapter.content, 180),
        "scenes": [
            {
                "id": f"sc_{chapter.number:03d}_001",
                "title": f"{chapter.title} - 核心场景",
                "location_id": location["id"],
                "time": "day",
                "characters": list(dict.fromkeys([character["id"], supporting_character["id"]])),
                "synopsis": _brief(chapter.content, 140),
                "stage_directions": [
                    "镜头跟随主要人物进入场景，环境细节烘托本章情绪。",
                    "角色的动作和停顿表现出内心变化。",
                ],
                "dialogue": [
                    {
                        "speaker_id": character["id"],
                        "speaker_name": character["name"],
                        "line": "这一刻，我必须做出选择。",
                        "emotion": "determined",
                    },
                    {
                        "speaker_id": supporting_character["id"],
                        "speaker_name": supporting_character["name"],
                        "line": "那就一起面对眼前的阻碍。",
                        "emotion": "supportive",
                    }
                ],
            }
        ],
    }


def _brief(text: str, limit: int) -> str:
    compact = re.sub(r"\s+", " ", text.strip())
    if len(compact) <= limit:
        return compact

    cutoff = limit - 1
    sentence_endings = "。！？.!?"
    for index in range(cutoff, max(0, cutoff - 30), -1):
        if compact[index - 1] in sentence_endings:
            cutoff = index
            break
    return compact[:cutoff] + "..."

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
from app.services.character_filter import aliases_for, canonicalize_character_list, normalize_character_name


FORBIDDEN_TEMPLATE_PHRASES = [
    "必须做出选择",
    "别让证据断在这里",
    "核心场景",
    "环境细节烘托",
    "第 X 章的线索已经很清楚",
    "线索已经很清楚",
]

KNOWN_CHARACTER_DESCRIPTIONS = {
    "许七安": "原为现代警校毕业生，穿越成大奉捕快，因税银案被牵连入狱，依靠推理能力自救。",
    "李玉春": "打更人组织成员，参与调查税银失踪案，重视线索与逻辑推理。",
    "褚采薇": "司天监弟子，擅长术士能力，性格活泼好吃，参与辅助查案。",
    "陈汉光": "京兆府府尹，负责审理和处置税银案相关人犯。",
    "许平志": "许七安的二叔，因税银案牵连许家命运。",
    "许新年": "许家二郎，许七安的堂弟，读书人身份，与许家案件相关。",
    "李茹": "许家女眷，因税银案受到牵连。",
    "狱卒": "京兆府监牢中的差役，负责看守犯人和传递讯息。",
    "衙役": "京兆府衙门差役，参与押送、看守和办案流程。",
}


@dataclass(frozen=True)
class LLMResult:
    provider: str
    content: dict
    fallback_reason: str | None = None


def analyze_project(project: Project) -> LLMResult:
    if _has_llm_config():
        result = _call_deepseek(_analysis_prompt(project))
        if isinstance(result, dict) and _is_valid_analysis(result):
            return LLMResult(provider=settings.llm_provider, content=_normalize_analysis(result, _project_text(project)))
        return _demo_analyze_project(project, "invalid_analysis_response")

    return _demo_analyze_project(project, "missing_config")


def generate_screenplay(project: Project, analysis: dict | None = None) -> LLMResult:
    analysis = _normalize_analysis(analysis or analyze_project(project).content, _project_text(project))
    generation_settings = _project_generation_settings(project)
    if _has_llm_config():
        result = _call_deepseek(_screenplay_prompt(project, analysis, generation_settings))
        if isinstance(result, dict) and _is_valid_screenplay_for_project(result, project):
            _apply_project_screenplay_guards(result, project, generation_settings)
            if _is_usable_screenplay(result):
                return LLMResult(provider=settings.llm_provider, content=result)
        return _demo_generate_screenplay(project, analysis, "invalid_screenplay_response")

    return _demo_generate_screenplay(project, analysis, "missing_config")


def _demo_analyze_project(project: Project, fallback_reason: str | None = None) -> LLMResult:
    characters = _demo_characters(project)
    locations = _locations_from_project(project)
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
    analysis = _normalize_analysis(analysis or _demo_analyze_project(project).content, _project_text(project))
    generation_settings = _project_generation_settings(project)
    template = _template_profile(generation_settings.get("templateId"))
    characters = analysis.get("characters") or _demo_characters(project)
    locations = _locations_from_project(project)

    chapters = [_chapter_to_script(chapter, locations, characters) for chapter in project.chapters]

    content = {
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
    }
    _apply_project_screenplay_guards(content, project, generation_settings)

    return LLMResult(
        provider="deterministic_demo",
        fallback_reason=fallback_reason,
        content=content,
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
            "每章只生成 1 到 2 个关键分场，不要把每个自然段都拆成场景。",
            f"必须为当前小说的 {len(project.chapters)} 个章节逐章生成，script.chapters 数量必须等于 {len(project.chapters)}。",
            "每个 script.chapters[i].source_chapter_numbers 必须只引用对应的原文章节编号，不能新增、合并、跳过或改写为其他章节。",
            "metadata.title、metadata.original_novel、metadata.author 和 metadata.total_chapters 必须与当前项目一致。",
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


def _apply_project_screenplay_guards(
    result: dict[str, Any],
    project: Project,
    generation_settings: dict[str, Any],
) -> None:
    template = _template_profile(generation_settings.get("templateId"))
    script = result.get("script")
    if not isinstance(script, dict):
        return

    metadata = script.setdefault("metadata", {})
    if isinstance(metadata, dict):
        metadata["title"] = project.title
        metadata["original_novel"] = project.title
        metadata["author"] = project.author
        metadata["total_chapters"] = len(project.chapters)
        metadata["target_format"] = template["target_format"]
        metadata["template_id"] = template["id"]
        metadata["script_type"] = generation_settings.get("scriptType") or template["script_type"]
        metadata["adaptation_style"] = generation_settings.get("adaptationStyle")

    chapters = script.get("chapters")
    if isinstance(chapters, list):
        locations = script.get("locations") if isinstance(script.get("locations"), list) else []
        characters = script.get("characters") if isinstance(script.get("characters"), list) else []
        if not locations:
            locations = _locations_from_project(project)
            script["locations"] = locations
        if not characters:
            characters = _demo_characters(project)
            script["characters"] = characters
        seen_signatures: set[str] = set()
        normalized_chapters = []

        for project_chapter, script_chapter in zip(project.chapters, chapters):
            if not isinstance(script_chapter, dict):
                normalized_chapters.append(_chapter_to_script(project_chapter, locations, characters))
                continue

            script_chapter["id"] = f"ch_{project_chapter.number:03d}"
            script_chapter["source_chapter_numbers"] = [project_chapter.number]
            script_chapter["title"] = project_chapter.title

            signature = _generated_chapter_signature(script_chapter)
            if (
                signature
                and signature in seen_signatures
                or _chapter_contains_forbidden_template(script_chapter)
                or not script_chapter.get("scenes")
            ):
                script_chapter = _chapter_to_script(project_chapter, locations, characters)
            else:
                _normalize_scene_ids(script_chapter, project_chapter)
                _sanitize_script_chapter(script_chapter, project_chapter, locations, characters)

            updated_signature = _generated_chapter_signature(script_chapter)
            if updated_signature:
                seen_signatures.add(updated_signature)
            normalized_chapters.append(script_chapter)

        script["chapters"] = normalized_chapters


def _normalize_scene_ids(script_chapter: dict[str, Any], project_chapter: Chapter) -> None:
    scenes = script_chapter.get("scenes")
    if not isinstance(scenes, list):
        return

    for scene_index, scene in enumerate(scenes, start=1):
        if isinstance(scene, dict):
            scene["id"] = f"sc_{project_chapter.number:03d}_{scene_index:03d}"


def _generated_chapter_signature(script_chapter: dict[str, Any]) -> str:
    parts: list[str] = [str(script_chapter.get("summary") or "")]
    scenes = script_chapter.get("scenes")

    if isinstance(scenes, list):
        for scene in scenes:
            if not isinstance(scene, dict):
                continue
            parts.append(str(scene.get("synopsis") or scene.get("action") or ""))
            stage_directions = scene.get("stage_directions")
            if isinstance(stage_directions, list):
                parts.extend(str(item) for item in stage_directions if item is not None)
            dialogue = scene.get("dialogue") or scene.get("dialogues")
            if isinstance(dialogue, list):
                parts.extend(
                    str(line.get("line") or "")
                    for line in dialogue
                    if isinstance(line, dict)
                )

    signature = re.sub(r"\s+", "", " ".join(part for part in parts if part).lower())
    return signature[:500] if len(signature) >= 24 else ""


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


def _project_text(project: Project) -> str:
    return "\n".join(chapter.content or "" for chapter in project.chapters)


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


def _normalize_analysis(data: dict[str, Any], source_text: str | None = None) -> dict[str, Any]:
    return {
        "characters": _normalize_characters(data.get("characters", []), source_text),
        "locations": _normalize_locations(data.get("locations", [])),
        "chapter_summaries": data.get("chapter_summaries", []),
        "themes": _normalize_string_list(data.get("themes", [])),
        "conflicts": _normalize_string_list(data.get("conflicts", [])),
    }


def _normalize_characters(characters: Any, source_text: str | None = None) -> list[dict[str, Any]]:
    if not isinstance(characters, list):
        return []

    if source_text:
        filtered = canonicalize_character_list(characters, source_text)
        return [
            {
                "id": character["id"],
                "name": character["name"],
                "role": character.get("role") or ("主角" if index == 1 else "配角"),
                "gender": "unknown",
                "age": None,
                "description": _summary_character_description(character["name"], character.get("description")),
            }
            for index, character in enumerate(filtered, start=1)
        ]

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
                "description": _summary_character_description(str(character.get("name") or ""), character.get("description")),
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


def _is_valid_screenplay_for_project(data: dict[str, Any], project: Project) -> bool:
    try:
        document = ScreenplayDocument.model_validate(data)
    except (ValidationError, ValueError):
        return False

    script = document.script
    project_chapter_numbers = [chapter.number for chapter in project.chapters]
    if script.metadata.total_chapters != len(project_chapter_numbers):
        return False
    if len(script.chapters) != len(project_chapter_numbers):
        return False

    for expected_number, script_chapter in zip(project_chapter_numbers, script.chapters):
        if script_chapter.source_chapter_numbers != [expected_number]:
            return False

    return True


def _demo_characters(project: Project) -> list[dict[str, Any]]:
    names = _extract_character_names(project)
    if not names:
        names = ["主角", "重要角色"]
    elif len(names) == 1:
        names.append("重要角色")

    roles = ["主角", "重要角色", "重要角色", "重要角色", "重要角色", "重要角色"]
    return [
        {
            "id": f"char_{index:03d}",
            "name": name,
            "role": roles[min(index - 1, len(roles) - 1)],
            "gender": "unknown",
            "age": None,
            "description": "根据小说章节自动识别出的核心人物。",
        }
        for index, name in enumerate(names[:6], start=1)
    ]


def _extract_character_names(project: Project) -> list[str]:
    text = "\n".join(chapter.content for chapter in project.chapters)
    candidates: list[str] = []

    for match in re.finditer(r"(?:主角|主要人物|人物|角色)[:：]\s*([^\n]+)", text):
        candidates.extend(re.findall(r"[\u4e00-\u9fff]{2,4}", match.group(1)))

    for match in re.finditer(r"([\u4e00-\u9fff]{2})、([\u4e00-\u9fff]{2})、([\u4e00-\u9fff]{2})", text):
        candidates.extend(match.groups())

    name_action_pattern = (
        r"(?<![\u4e00-\u9fff])([\u4e00-\u9fff]{2,4})\s*"
        r"(?:握着|说|低声道|道|问|答|没有|从|提醒|看着|率|与|和|同|向)"
    )
    for match in re.finditer(name_action_pattern, text):
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
        "事情",
        "表面",
        "立刻",
        "众人",
        "他们",
    }
    seen = set()
    names = []
    for candidate in candidates:
        if candidate in stopwords or candidate in seen:
            continue
        seen.add(candidate)
        names.append(candidate)
    return names


def _demo_characters(project: Project) -> list[dict[str, Any]]:
    source_text = "\n".join(chapter.content for chapter in project.chapters)
    names = _extract_character_names(project)
    if not names:
        names = ["\u4e3b\u89d2", "\u91cd\u8981\u89d2\u8272"]
    elif len(names) == 1:
        names.append("\u91cd\u8981\u89d2\u8272")

    roles = ["\u4e3b\u89d2", "\u91cd\u8981\u89d2\u8272", "\u91cd\u8981\u89d2\u8272", "\u91cd\u8981\u89d2\u8272", "\u91cd\u8981\u89d2\u8272", "\u91cd\u8981\u89d2\u8272", "\u91cd\u8981\u89d2\u8272", "\u91cd\u8981\u89d2\u8272", "\u91cd\u8981\u89d2\u8272"]
    return [
        {
            "id": f"char_{index:03d}",
            "name": name,
            "role": roles[min(index - 1, len(roles) - 1)],
            "gender": "unknown",
            "age": None,
            "description": _character_description(name, source_text),
        }
        for index, name in enumerate(names[:9], start=1)
    ]


def _extract_character_names(project: Project) -> list[str]:
    text = "\n".join(chapter.content for chapter in project.chapters)
    candidates: dict[str, int] = {}

    def add_candidate(name: str, weight: int = 1) -> None:
        cleaned = re.sub(r"\s+", "", name.strip(" \t\r\n，,、。：:；;（）()《》“”\"'"))
        if _is_likely_character_name(cleaned):
            candidates[cleaned] = candidates.get(cleaned, 0) + weight

    label_pattern = r"(?:\u4e3b\u89d2|\u4e3b\u8981\u4eba\u7269|\u6838\u5fc3\u4eba\u7269|\u4eba\u7269|\u89d2\u8272)[:\uff1a]\s*([^\n]+)"
    for match in re.finditer(label_pattern, text):
        for name in re.findall(r"[\u4e00-\u9fff]{2,4}", match.group(1)):
            add_candidate(name, 4)

    list_pattern = r"[\u4e00-\u9fff]{2,4}(?:\u3001\s*[\u4e00-\u9fff]{2,4})+"
    for match in re.finditer(list_pattern, text):
        for name in re.findall(r"[\u4e00-\u9fff]{2,4}", match.group(0)):
            add_candidate(name, 2)

    name_action_pattern = (
        r"(?<![\u4e00-\u9fff])([\u4e00-\u9fff]{2,4})\s*"
        r"(?:\u63e1\u7740|\u8bf4|\u4f4e\u58f0\u9053|\u558a\u9053|\u95ee\u9053|\u7b54\u9053|\u56de\u7b54\u9053|\u8bf4\u9053|\u63d0\u9192|\u770b\u7740|\u542c\u89c1|\u70b9\u5934|\u6447\u5934|\u79bb\u5f00|\u8f6c\u8eab|\u8d70\u8fdb|\u8d70\u6765|\u8d70\u8fc7\u6765|\u8d77\u8eab|\u5750\u4e0b|\u7ad9\u8d77|\u63e1\u7d27|\u653e\u4e0b|\u63a8\u5f00|\u53d1\u73b0|\u627f\u8ba4|\u51fa\u73b0)"
    )
    for match in re.finditer(name_action_pattern, text):
        add_candidate(match.group(1), 3)

    for match in re.finditer(r"(?:^|[\u3002\uff01\uff1f\n])\s*([\u4e00-\u9fff]{2,4})(?:[\uff0c\u3002\uff01\uff1f\u201c\"'\s]|$)", text):
        add_candidate(match.group(1), 1)

    ranked = sorted(candidates.items(), key=lambda item: (-item[1], text.find(item[0]), item[0]))
    filtered = canonicalize_character_list([{"name": name} for name, _score in ranked], text)
    return [character["name"] for character in filtered[:12]]


def _is_likely_character_name(name: str) -> bool:
    if not (2 <= len(name) <= 4):
        return False
    if not re.fullmatch(r"[\u4e00-\u9fff]+", name):
        return False

    stopwords = {
        "\u5c0f\u8bf4", "\u7ae0\u8282", "\u6b63\u6587", "\u4eba\u7269", "\u89d2\u8272", "\u4e3b\u89d2", "\u6545\u4e8b", "\u5267\u60c5",
        "\u4e8b\u60c5", "\u8868\u9762", "\u56e0\u4e3a", "\u6240\u4ee5", "\u4f46\u662f", "\u53ea\u662f", "\u7136\u540e", "\u63a5\u7740",
        "\u8fd9\u91cc", "\u90a3\u91cc", "\u4ed6\u4eec", "\u5979\u4eec", "\u6211\u4eec", "\u4f60\u4eec", "\u4f17\u4eba", "\u6240\u6709\u4eba",
        "\u542c\u89c1", "\u770b\u89c1", "\u53d1\u73b0", "\u77e5\u9053", "\u89c9\u5f97", "\u60f3\u5230", "\u660e\u767d", "\u7acb\u523b",
        "\u73b0\u5728", "\u5f53\u65f6", "\u5ffd\u7136", "\u7a81\u7136", "\u7ec8\u4e8e", "\u8fdc\u5904", "\u591c\u8272", "\u98ce\u5728",
        "\u4eca\u5929", "\u660e\u5929", "\u6628\u5929", "\u660e\u5929\u5c31", "\u4eca\u5929\u5c31", "\u6628\u5929\u5c31",
        "\u6863\u6848", "\u8bb0\u5fc6", "\u57ce\u4e2d", "\u95e8\u524d", "\u95e8\u5916", "\u534a\u679a", "\u94dc\u94b1", "\u949f\u58f0",
        "\u4e00\u4e2a", "\u4e00\u58f0", "\u4e00\u9635", "\u4e00\u773c", "\u4e00\u5207", "\u4e00\u8d77",
    }
    if name in stopwords:
        return False
    if name.startswith(("\u4eca\u5929", "\u660e\u5929", "\u6628\u5929")):
        return False
    if name.endswith(("\u4e4b\u4e2d", "\u65f6\u5019")):
        return False
    return True


def _character_description(name: str, text: str) -> str:
    index = text.find(name)
    if index < 0:
        return "\u4ece\u5c0f\u8bf4\u6587\u672c\u4e2d\u8bc6\u522b\u7684\u4eba\u7269\uff0c\u5f85\u5728\u751f\u6210\u9636\u6bb5\u7ee7\u7eed\u8865\u5145\u5176\u52a8\u673a\u4e0e\u5173\u7cfb\u3002"

    start = max(0, index - 28)
    end = min(len(text), index + len(name) + 72)
    snippet = _brief(text[start:end], 96)
    if snippet:
        return f"\u539f\u6587\u7247\u6bb5\uff1a{snippet}"
    return "\u4ece\u5c0f\u8bf4\u6587\u672c\u4e2d\u8bc6\u522b\u7684\u4eba\u7269\u3002"


def _summary_character_description(name: str, source_description: Any = None) -> str:
    if name in KNOWN_CHARACTER_DESCRIPTIONS:
        return KNOWN_CHARACTER_DESCRIPTIONS[name]
    text = re.sub(r"\s+", " ", str(source_description or "")).strip()
    if not text:
        return f"{name}是原文中出现的人物，具体身份与剧情作用需结合后续场景继续确认。"
    text = re.sub(r"^原文片段[:：]\s*", "", text)
    return _brief(text, 80)


LOCATION_KEYWORDS = [
    "京兆府监牢",
    "京兆府后堂",
    "京兆府内堂",
    "京兆府衙门",
    "京兆府后门",
    "监牢",
    "牢房",
    "后堂",
    "内堂",
    "衙门",
    "后门",
    "府衙",
    "公堂",
]


def _locations_from_project(project: Project) -> list[dict[str, str]]:
    names: list[str] = []
    for chapter in project.chapters:
        for name in _location_names_in_text(chapter.content):
            if name not in names:
                names.append(name)

    if not names:
        names = ["未明确地点"]

    return [
        {
            "id": f"loc_{index:03d}",
            "name": name,
            "description": f"{name}，由原文地点描写提取。",
        }
        for index, name in enumerate(names, start=1)
    ]


def _location_names_in_text(text: str) -> list[str]:
    names = []
    for keyword in LOCATION_KEYWORDS:
        if keyword in text and keyword not in names:
            names.append(_normalize_location_name(keyword))
    return list(dict.fromkeys(names))


def _normalize_location_name(name: str) -> str:
    if name in {"监牢", "牢房"}:
        return "京兆府监牢"
    if name == "后堂":
        return "京兆府后堂"
    if name == "内堂":
        return "京兆府内堂"
    if name in {"衙门", "府衙", "公堂"}:
        return "京兆府衙门"
    if name == "后门":
        return "京兆府后门"
    return name


def _ensure_location_for_text(locations: list[dict], text: str, index: int) -> dict:
    names = _location_names_in_text(text)
    target = names[0] if names else (locations[0]["name"] if locations else "未明确地点")
    for location in locations:
        if location.get("name") == target:
            return location

    location = {
        "id": f"loc_{len(locations) + 1:03d}",
        "name": target,
        "description": f"{target}，由第 {index} 个场景文本提取。",
    }
    locations.append(location)
    return location


def _split_scene_chunks(text: str) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if not paragraphs:
        paragraphs = [part.strip() for part in re.split(r"(?<=[。！？])", text) if part.strip()]

    chunks: list[str] = []
    current = ""
    current_location = None
    for paragraph in paragraphs:
        location_names = _location_names_in_text(paragraph)
        location = location_names[0] if location_names else current_location
        should_split = bool(current and location and current_location and location != current_location)
        if len(current) + len(paragraph) > 900 and current:
            should_split = True
        if should_split:
            chunks.append(current.strip())
            current = paragraph
        else:
            current = f"{current}\n{paragraph}".strip()
        if location:
            current_location = location
    if current:
        chunks.append(current.strip())
    return chunks[:8]


def _characters_in_text(text: str, characters: list[dict]) -> list[str]:
    ids = []
    for character in characters:
        name = str(character.get("name") or "")
        aliases = [name, *aliases_for(name)]
        for alias in aliases:
            if alias and alias in text:
                ids.append(str(character["id"]))
                break
    return list(dict.fromkeys(ids))


def _character_for_speaker(prefix: str, characters: list[dict]) -> dict | None:
    for character in characters:
        name = str(character.get("name") or "")
        aliases = [name, *aliases_for(name)]
        for alias in aliases:
            if alias and alias in prefix:
                return character
    normalized = normalize_character_name(prefix[-5:])
    if normalized:
        for character in characters:
            if character.get("name") == normalized:
                return character
    return None


def _dialogue_from_text(text: str, characters: list[dict]) -> list[dict]:
    dialogue = []
    quote_pattern = re.compile(r"([^。！？\n]{0,28})[“\"]([^”\"]{1,120})[”\"]")
    for match in quote_pattern.finditer(text):
        quote_start = max(match.start(2) - 1, match.start())
        boundary = max(text.rfind(mark, 0, quote_start) for mark in ["。", "！", "？", "\n"])
        prefix = text[boundary + 1:quote_start]
        line = match.group(2).strip()
        character = _character_for_speaker(prefix, characters)
        dialogue.append(
            {
                "speaker_id": character.get("id") if character else None,
                "speaker_name": character.get("name") if character else "旁白",
                "line": line,
                "emotion": _emotion_from_text(prefix + line),
            }
        )

    colon_pattern = re.compile(r"([^。！？\n]{2,12})[：:]\s*([^。！？\n]{1,120})")
    for match in colon_pattern.finditer(text):
        prefix = match.group(1)
        line = match.group(2).strip().strip("“”\"'")
        if any(_dialogue_key(existing["line"]) == _dialogue_key(line) for existing in dialogue):
            continue
        character = _character_for_speaker(prefix, characters)
        dialogue.append(
            {
                "speaker_id": character.get("id") if character else None,
                "speaker_name": character.get("name") if character else "旁白",
                "line": line,
                "emotion": _emotion_from_text(prefix + line),
            }
        )

    return dialogue[:4]


def _dialogue_key(line: str) -> str:
    return re.sub(r"[。！？!?，,\s“”\"']", "", line or "")


def _emotion_from_text(text: str) -> str:
    if any(word in text for word in ["怒", "冷", "喝", "骂"]):
        return "tense"
    if any(word in text for word in ["笑", "莞尔"]):
        return "light"
    if any(word in text for word in ["惊", "愣", "怔"]):
        return "surprised"
    return "neutral"


def _scene_title_from_text(text: str, location_name: str, index: int) -> str:
    event = _synopsis_from_text(text)
    title = event[:14].strip("，。！？；; ")
    if title and location_name not in title:
        return f"{location_name}：{title}"
    return title or f"{location_name}场景{index}"


def _time_from_text(text: str) -> str:
    for marker in ["清晨", "早晨", "上午", "午后", "下午", "傍晚", "夜晚", "深夜", "翌日"]:
        if marker in text:
            return marker
    return "未明确时间"


def _synopsis_from_text(text: str) -> str:
    sentences = [item.strip() for item in re.split(r"(?<=[。！？])", text) if item.strip()]
    if not sentences:
        return _brief(text, 120)
    return _brief("".join(sentences[:2]), 140)


def _stage_directions_from_text(text: str) -> list[str]:
    sentences = [item.strip() for item in re.split(r"(?<=[。！？])", text) if item.strip()]
    directions = []
    for sentence in sentences:
        if "“" in sentence or "\"" in sentence or "：" in sentence:
            continue
        directions.append(_brief(sentence, 100))
        if len(directions) >= 2:
            break
    return directions


def _chapter_contains_forbidden_template(script_chapter: dict[str, Any]) -> bool:
    signature = _generated_chapter_signature(script_chapter)
    return any(phrase in signature for phrase in FORBIDDEN_TEMPLATE_PHRASES)


def _sanitize_script_chapter(
    script_chapter: dict[str, Any],
    project_chapter: Chapter,
    locations: list[dict],
    characters: list[dict],
) -> None:
    location_ids = {str(location.get("id")) for location in locations}
    character_by_id = {str(character.get("id")): character for character in characters}
    fallback_location = locations[0]["id"] if locations else "loc_001"
    for scene_index, scene in enumerate(script_chapter.get("scenes") or [], start=1):
        if not isinstance(scene, dict):
            continue
        if scene.get("location_id") not in location_ids:
            location = _ensure_location_for_text(locations, str(scene.get("synopsis") or project_chapter.content), scene_index)
            scene["location_id"] = location.get("id") or fallback_location
        scene["synopsis"] = str(scene.get("synopsis") or _synopsis_from_text(project_chapter.content))
        scene["characters"] = [
            str(char_id) for char_id in scene.get("characters", []) if str(char_id) in character_by_id
        ] or _characters_in_text(project_chapter.content, characters)
        sanitized_dialogue = []
        for line in scene.get("dialogue") or []:
            if not isinstance(line, dict):
                continue
            if any(phrase in str(line.get("line") or "") for phrase in FORBIDDEN_TEMPLATE_PHRASES):
                continue
            speaker_id = str(line.get("speaker_id")) if line.get("speaker_id") is not None else None
            if speaker_id not in character_by_id:
                line["speaker_id"] = None
                line["speaker_name"] = "旁白"
            else:
                line["speaker_id"] = speaker_id
                line["speaker_name"] = character_by_id[str(speaker_id)].get("name") or line.get("speaker_name")
            sanitized_dialogue.append(line)
        scene["dialogue"] = sanitized_dialogue


def _is_usable_screenplay(result: dict[str, Any]) -> bool:
    script = result.get("script") if isinstance(result, dict) else None
    if not isinstance(script, dict):
        return False
    chapters = script.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        return False
    scene_count = 0
    for chapter in chapters:
        if not isinstance(chapter, dict):
            return False
        scenes = chapter.get("scenes")
        if not isinstance(scenes, list) or not scenes:
            return False
        for scene in scenes:
            scene_count += 1
            if not isinstance(scene, dict) or not scene.get("synopsis"):
                return False
            if _chapter_contains_forbidden_template({"scenes": [scene], "summary": scene.get("synopsis", "")}):
                return False
    return scene_count > 0


def _chapter_to_script(chapter: Chapter, locations: list[dict], characters: list[dict]) -> dict:
    scenes = []
    chunks = _split_scene_chunks(chapter.content)
    for scene_index, chunk in enumerate(chunks, start=1):
        location = _ensure_location_for_text(locations, chunk, scene_index)
        scene_characters = _characters_in_text(chunk, characters)
        dialogue = _dialogue_from_text(chunk, characters)
        scene_title = _scene_title_from_text(chunk, location["name"], scene_index)

        scenes.append(
            {
                "id": f"sc_{chapter.number:03d}_{scene_index:03d}",
                "title": scene_title,
                "location_id": location["id"],
                "time": _time_from_text(chunk),
                "characters": scene_characters,
                "synopsis": _synopsis_from_text(chunk),
                "stage_directions": _stage_directions_from_text(chunk),
                "dialogue": dialogue,
            }
        )

    if not scenes:
        location = _ensure_location_for_text(locations, chapter.content, 1)
        scenes.append(
            {
                "id": f"sc_{chapter.number:03d}_001",
                "title": _scene_title_from_text(chapter.content, location["name"], 1),
                "location_id": location["id"],
                "time": _time_from_text(chapter.content),
                "characters": _characters_in_text(chapter.content, characters),
                "synopsis": _synopsis_from_text(chapter.content),
                "stage_directions": _stage_directions_from_text(chapter.content),
                "dialogue": _dialogue_from_text(chapter.content, characters),
            }
        )

    return {
        "id": f"ch_{chapter.number:03d}",
        "title": chapter.title,
        "source_chapter_numbers": [chapter.number],
        "summary": _brief(chapter.content, 180),
        "scenes": scenes,
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

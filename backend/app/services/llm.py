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
            "name": _chapter_location_name(chapter),
            "description": _brief(chapter.content, 96),
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
            "themes": _demo_themes(project),
            "conflicts": _demo_conflicts(project),
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

    roles = ["主角", "重要角色", "重要角色", "重要角色", "重要角色", "重要角色"]
    return [
        {
            "id": f"char_{index:03d}",
            "name": name,
            "role": roles[min(index - 1, len(roles) - 1)],
            "gender": "unknown",
            "age": None,
            "description": _character_description(project, name, index),
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


def _chapter_to_script(chapter: Chapter, locations: list[dict], characters: list[dict]) -> dict:
    location = locations[min(chapter.number - 1, len(locations) - 1)]
    chapter_characters = _chapter_characters(chapter, characters)
    scene_characters = chapter_characters[:3] or characters[:2]
    if len(scene_characters) == 1:
        scene_characters.append(characters[1] if len(characters) > 1 else scene_characters[0])
    synopsis = _chapter_synopsis(chapter)
    directions = _stage_directions(chapter, location)
    dialogue = _chapter_dialogue(chapter, scene_characters)

    return {
        "id": f"ch_{chapter.number:03d}",
        "title": chapter.title,
        "source_chapter_numbers": [chapter.number],
        "summary": synopsis,
        "scenes": [
            {
                "id": f"sc_{chapter.number:03d}_001",
                "title": _scene_title(chapter, location),
                "location_id": location["id"],
                "time": _scene_time(chapter.content),
                "characters": [character["id"] for character in scene_characters],
                "synopsis": synopsis,
                "stage_directions": directions,
                "dialogue": dialogue,
            }
        ],
    }


def _chapter_location_name(chapter: Chapter) -> str:
    location_pattern = re.compile(r"([\u4e00-\u9fff]{1,8}(?:城|府|宫|殿|门|山|河|江|营|寨|村|镇|街|院|房|屋|楼|阁|厅|店|站|场|桥|路|关|州|郡|县|塔|湖|岛|巷|码头))")
    match = location_pattern.search(f"{chapter.title}\n{chapter.content}")
    if match:
        return match.group(1)
    return f"第 {chapter.number} 章主要场景"


def _demo_themes(project: Project) -> list[str]:
    text = "\n".join(chapter.content for chapter in project.chapters)
    rules = [
        ("乱世抉择", ["乱世", "战", "兵", "敌", "黄巾"]),
        ("结义与信任", ["结义", "兄弟", "同心", "信任", "约定"]),
        ("秘密追寻", ["秘密", "线索", "真相", "旧照片", "玉牌"]),
        ("成长试炼", ["第一次", "试炼", "成长", "终于", "选择"]),
        ("情感裂痕", ["误会", "离开", "愤怒", "沉默", "眼泪"]),
    ]
    themes = [name for name, keywords in rules if any(keyword in text for keyword in keywords)]
    return themes[:4] or ["人物选择", "关系变化"]


def _demo_conflicts(project: Project) -> list[str]:
    conflicts = []
    for chapter in project.chapters[:6]:
        sentence = _first_sentence(chapter.content, ["战", "怒", "逃", "拒", "危", "逼", "秘密", "真相", "误会", "断裂", "阻碍"])
        if sentence:
            conflicts.append(f"{chapter.title}：{sentence}")
    return conflicts or ["人物目标与现实压力之间的冲突"]


def _character_description(project: Project, name: str, index: int) -> str:
    text = "\n".join(chapter.content for chapter in project.chapters)
    position = text.find(name)
    if position >= 0:
        start = max(0, position - 22)
        end = min(len(text), position + len(name) + 58)
        return _brief(text[start:end], 92)
    if index == 1:
        return "推动主线选择的人物，承担主要行动和情绪变化。"
    return "与主角形成关系压力或行动支援的重要人物。"


def _chapter_characters(chapter: Chapter, characters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    appeared = [character for character in characters if character["name"] in chapter.content or character["name"] in chapter.title]
    if appeared:
        return appeared
    return characters


def _chapter_synopsis(chapter: Chapter) -> str:
    sentence = _first_sentence(chapter.content, ["战", "约定", "秘密", "真相", "选择", "相识", "离开", "危", "破", "冲突"])
    return sentence or _brief(chapter.content, 150)


def _stage_directions(chapter: Chapter, location: dict[str, Any]) -> list[str]:
    opening = _brief(chapter.content, 72)
    tension = _first_sentence(chapter.content, ["沉默", "风", "夜", "雨", "钟声", "怒", "停顿", "推到", "握着"])
    directions = [
        f"{location['name']}中，人物围绕“{_brief(opening, 38)}”展开行动。",
        f"场面调度保留《{chapter.title}》的核心事件，让冲突集中在人物选择上。",
    ]
    if tension and tension != opening:
        directions.insert(1, f"环境细节压低节奏：{_brief(tension, 54)}")
    return directions


def _chapter_dialogue(chapter: Chapter, characters: list[dict[str, Any]]) -> list[dict[str, str]]:
    quoted_lines = re.findall(r"[“\"]([^”\"]{4,60})[”\"]", chapter.content)
    key_sentences = _sentences(chapter.content)
    first = characters[0]
    second = characters[1] if len(characters) > 1 else first
    third = characters[2] if len(characters) > 2 else first
    lines = []
    if quoted_lines:
        for index, line in enumerate(quoted_lines[:3]):
            speaker = characters[index % len(characters)]
            lines.append(_dialogue_line(speaker, line, "focused"))
    else:
        lines.append(_dialogue_line(first, _line_from_sentence(key_sentences, 0, "这件事不能再拖下去了。"), "determined"))
        lines.append(_dialogue_line(second, _line_from_sentence(key_sentences, 1, "先看清局势，再决定怎么走。"), "cautious"))
        if third["id"] != first["id"]:
            lines.append(_dialogue_line(third, _line_from_sentence(key_sentences, 2, "我会盯住最危险的那一处。"), "alert"))
    return lines[:4]


def _dialogue_line(character: dict[str, Any], line: str, emotion: str) -> dict[str, str]:
    return {
        "speaker_id": character["id"],
        "speaker_name": character["name"],
        "line": _brief(line.strip(" ，。！？!?"), 64),
        "emotion": emotion,
    }


def _line_from_sentence(sentences: list[str], index: int, fallback: str) -> str:
    if index < len(sentences):
        sentence = sentences[index]
        if len(sentence) <= 18:
            return sentence
        return f"{sentence[:18]}，这就是我们要处理的事。"
    return fallback


def _scene_title(chapter: Chapter, location: dict[str, Any]) -> str:
    clean_title = re.sub(r"^\s*第[\d一二三四五六七八九十百千万零〇两]+[章节回卷幕部集]\s*", "", chapter.title).strip()
    return f"{location['name']}的{clean_title or '转折'}"


def _scene_time(text: str) -> str:
    if any(word in text for word in ["夜", "黄昏", "灯", "月"]):
        return "night"
    if any(word in text for word in ["清晨", "黎明", "晨"]):
        return "morning"
    return "day"


def _first_sentence(text: str, keywords: list[str]) -> str | None:
    for sentence in _sentences(text):
        if any(keyword in sentence for keyword in keywords):
            return _brief(sentence, 120)
    return None


def _sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"[。！？!?]\s*", text) if sentence.strip()]


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

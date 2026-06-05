from __future__ import annotations

import json
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


def analyze_project(project: Project) -> LLMResult:
    if _has_llm_config():
        prompt = _analysis_prompt(project)
        result = _call_openai_compatible(prompt)
        if isinstance(result, dict) and _is_valid_analysis(result):
            return LLMResult(provider=settings.llm_provider, content=result)

    return _demo_analyze_project(project)


def generate_screenplay(project: Project, analysis: dict | None = None) -> LLMResult:
    analysis = analysis or analyze_project(project).content
    if _has_llm_config():
        prompt = _screenplay_prompt(project, analysis)
        result = _call_openai_compatible(prompt)
        if isinstance(result, dict) and _is_valid_screenplay(result):
            return LLMResult(provider=settings.llm_provider, content=result)

    return _demo_generate_screenplay(project, analysis)


def _demo_analyze_project(project: Project) -> LLMResult:
    characters = [
        {
            "id": "char_001",
            "name": project.author or "主角",
            "role": "主角",
            "gender": "unknown",
            "age": None,
            "description": "根据小说章节自动识别出的核心人物。",
        }
    ]
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
        content={
            "characters": characters,
            "locations": locations,
            "chapter_summaries": chapter_summaries,
            "themes": ["成长", "选择"],
            "conflicts": ["角色目标与现实阻碍之间的冲突"],
        },
    )


def _demo_generate_screenplay(project: Project, analysis: dict | None = None) -> LLMResult:
    analysis = analysis or _demo_analyze_project(project).content
    characters = analysis.get("characters") or [
        {
            "id": "char_001",
            "name": project.author or "主角",
            "role": "主角",
            "gender": "unknown",
            "age": None,
            "description": "小说中的核心人物。",
        }
    ]
    locations = analysis.get("locations") or [
        {"id": "loc_001", "name": "主要场景", "description": "由小说内容概括出的主要空间。"}
    ]

    chapters = [_chapter_to_script(chapter, locations, characters) for chapter in project.chapters]

    return LLMResult(
        provider="deterministic_demo",
        content={
            "script": {
                "schema_version": "1.0",
                "metadata": {
                    "title": project.title,
                    "original_novel": project.title,
                    "author": project.author,
                    "language": "zh-CN",
                    "target_format": "screenplay",
                    "total_chapters": len(project.chapters),
                },
                "characters": characters,
                "locations": locations,
                "chapters": chapters,
                "adaptation_notes": {
                    "themes": analysis.get("themes", ["成长"]),
                    "conflicts": analysis.get("conflicts", ["角色目标与现实阻碍之间的冲突"]),
                    "omissions": ["当前版本保留章节主线，细节对白可由作者继续编辑打磨。"],
                },
            }
        },
    )


def _has_llm_config() -> bool:
    return bool(settings.llm_api_key and settings.llm_base_url and settings.llm_model)


def _call_openai_compatible(prompt: str) -> dict[str, Any] | None:
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
            _chapters_for_prompt(project),
        ]
    )


def _screenplay_prompt(project: Project, analysis: dict) -> str:
    return "\n".join(
        [
            "请把小说改编为结构化剧本 JSON。",
            "必须输出顶层包含 script 字段的 JSON 对象，并严格匹配以下结构：",
            "script.schema_version, script.metadata, script.characters, script.locations,",
            "script.chapters, script.adaptation_notes。",
            "每个 chapter 至少包含一个 scene；scene.location_id 必须引用 locations 中已有 id；",
            "scene.characters 和 dialogue.speaker_id 必须引用 characters 中已有 id。",
            "不要输出 YAML，不要输出 Markdown。",
            "",
            f"小说标题：{project.title}",
            f"作者：{project.author or '未知'}",
            f"分析结果 JSON：{json.dumps(analysis, ensure_ascii=False)}",
            "",
            _chapters_for_prompt(project),
        ]
    )


def _chapters_for_prompt(project: Project) -> str:
    parts = []
    for chapter in project.chapters:
        parts.append(
            "\n".join(
                [
                    f"第 {chapter.number} 章：{chapter.title}",
                    _brief(chapter.content, 2500),
                ]
            )
        )
    return "\n\n".join(parts)


def _is_valid_analysis(data: dict[str, Any]) -> bool:
    required_lists = ["characters", "locations", "chapter_summaries", "themes", "conflicts"]
    return all(isinstance(data.get(key), list) for key in required_lists)


def _is_valid_screenplay(data: dict[str, Any]) -> bool:
    try:
        ScreenplayDocument.model_validate(data)
    except (ValidationError, ValueError):
        return False
    return True


def _chapter_to_script(chapter: Chapter, locations: list[dict], characters: list[dict]) -> dict:
    location = locations[min(chapter.number - 1, len(locations) - 1)]
    character = characters[0]

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
                "characters": [character["id"]],
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
                    }
                ],
            }
        ],
    }


def _brief(text: str, limit: int) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "..."

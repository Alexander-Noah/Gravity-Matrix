from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.models.project import Chapter, Project


@dataclass(frozen=True)
class LLMResult:
    provider: str
    content: dict


def analyze_project(project: Project) -> LLMResult:
    # The deterministic fallback keeps the demo runnable before API keys are configured.
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
        provider=_provider_label(),
        content={
            "characters": characters,
            "locations": locations,
            "chapter_summaries": chapter_summaries,
            "themes": ["成长", "选择"],
            "conflicts": ["角色目标与现实阻碍之间的冲突"],
        },
    )


def generate_screenplay(project: Project, analysis: dict | None = None) -> LLMResult:
    analysis = analysis or analyze_project(project).content
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
        provider=_provider_label(),
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


def _provider_label() -> str:
    if settings.llm_api_key and settings.llm_base_url and settings.llm_model:
        return settings.llm_provider
    return "deterministic_demo"


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

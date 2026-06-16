import json
import re

import yaml
from pydantic import TypeAdapter

from app.schemas.novel_script import CharacterRead, SceneContentRead, SceneRead
from app.services import mock_ai_client
from app.services.character_filter import (
    canonicalize_character_list,
    filter_scene_character_names,
    normalize_speaker,
)


def clean_text(content: str) -> str:
    text = content.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_chapters(content: str) -> list[dict]:
    cleaned = clean_text(content)
    pattern = re.compile(r"(?m)^\s*((?:第[\u4e00-\u9fa5\d〇零一二三四五六七八九十百千万两]+[章节回幕卷部集]).*)$")
    matches = list(pattern.finditer(cleaned))
    if not matches:
        return [{"title": "第一章", "content": cleaned}]

    chapters = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(cleaned)
        title = match.group(1).strip()
        body = cleaned[start:end].strip()
        if body:
            chapters.append({"title": title, "content": body})
    return chapters or [{"title": "第一章", "content": cleaned}]


def extract_characters(content: str) -> list[CharacterRead]:
    raw = mock_ai_client.extract_characters_json(content)
    parsed = _parse_json_object(raw, "characters")
    filtered = canonicalize_character_list(parsed.get("characters", []), content)
    return TypeAdapter(list[CharacterRead]).validate_python(filtered)


def extract_scenes(chapters: list[dict], characters: list[dict]) -> list[SceneRead]:
    raw = mock_ai_client.extract_scenes_json(chapters, characters)
    parsed = _parse_json_object(raw, "scenes")
    scenes = []
    for scene in parsed.get("scenes", []):
        if isinstance(scene, dict):
            scene = dict(scene)
            scene["characters"] = filter_scene_character_names(scene.get("characters") or [], characters)
            scenes.append(scene)
    return TypeAdapter(list[SceneRead]).validate_python(scenes)


def generate_scene_content(scene: dict, characters: list[dict]) -> list[SceneContentRead]:
    raw = mock_ai_client.generate_scene_content_json(scene, characters)
    parsed = _parse_json_object(raw, "content")
    content = []
    for item in parsed.get("content", []):
        if not isinstance(item, dict):
            continue
        item = dict(item)
        if item.get("type") == "dialogue":
            speaker = normalize_speaker(item.get("speaker"), characters)
            item["speaker"] = speaker or "\u65c1\u767d"
            if speaker is None:
                item["need_review"] = True
                item["confidence"] = min(float(item.get("confidence") or 0.5), 0.6)
        content.append(item)
    return TypeAdapter(list[SceneContentRead]).validate_python(content)


def build_yaml(title: str, characters: list[dict], scenes: list[dict]) -> str:
    chapters: list[dict] = []
    chapter_by_title: dict[str, dict] = {}
    for scene in scenes:
        chapter_title = scene.get("chapter") or "第一章"
        chapter = chapter_by_title.get(chapter_title)
        if chapter is None:
            chapter = {
                "id": f"ch_{len(chapters) + 1:03d}",
                "title": chapter_title,
                "scenes": [],
            }
            chapter_by_title[chapter_title] = chapter
            chapters.append(chapter)

        chapter["scenes"].append(
            {
                "id": scene["id"],
                "title": scene.get("title", ""),
                "location": scene.get("location", ""),
                "time": scene.get("time", ""),
                "atmosphere": scene.get("atmosphere", ""),
                "characters": scene.get("characters", []),
                "summary": scene.get("summary", ""),
                "source_text": scene.get("source_text", ""),
                "content": scene.get("content", []),
            }
        )

    data = {
        "script": {
            "schema_version": "novel-script-v1",
            "title": title,
            "characters": characters,
            "chapters": chapters,
        }
    }
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def _parse_json_object(raw: str, required_key: str) -> dict:
    parsed = json.loads(raw)
    if not isinstance(parsed, dict) or required_key not in parsed:
        raise ValueError(f"AI JSON must contain {required_key}.")
    return parsed

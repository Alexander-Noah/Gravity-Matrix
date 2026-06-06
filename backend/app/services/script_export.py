from __future__ import annotations

import yaml
from pydantic import ValidationError

from app.schemas.screenplay import ScreenplayDocument


def screenplay_yaml_to_markdown(yaml_text: str) -> str:
    document = _parse_screenplay(yaml_text)
    script = document.script
    lines = [
        f"# {script.metadata.title}",
        "",
        f"- 原著：{script.metadata.original_novel}",
        f"- 作者：{script.metadata.author or '未知'}",
        f"- 章节数：{script.metadata.total_chapters}",
        "",
        "## 人物",
        "",
    ]

    for character in script.characters:
        lines.append(f"- **{character.name}**（{character.role}）：{character.description}")

    lines.extend(["", "## 正文", ""])
    for chapter in script.chapters:
        lines.extend([f"### {chapter.title}", "", chapter.summary, ""])
        for scene in chapter.scenes:
            lines.extend([f"#### {scene.title}", ""])
            location_name = _location_name(document, scene.location_id)
            lines.append(f"- 场景：{location_name}")
            lines.append(f"- 时间：{scene.time}")
            lines.append(f"- 出场人物：{_scene_character_names(document, scene.characters)}")
            lines.extend(["", scene.synopsis, ""])
            for direction in scene.stage_directions:
                lines.append(f"> {direction}")
            if scene.stage_directions:
                lines.append("")
            for dialogue in scene.dialogue:
                lines.append(f"**{dialogue.speaker_name}**：{dialogue.line}")
            lines.append("")

    return "\n".join(lines).strip() + "\n"


def screenplay_yaml_to_txt(yaml_text: str) -> str:
    document = _parse_screenplay(yaml_text)
    script = document.script
    lines = [
        script.metadata.title,
        f"原著：{script.metadata.original_novel}",
        f"作者：{script.metadata.author or '未知'}",
        "",
        "人物",
    ]

    for character in script.characters:
        lines.append(f"{character.name}（{character.role}）：{character.description}")

    lines.extend(["", "正文", ""])
    for chapter in script.chapters:
        lines.extend([chapter.title, chapter.summary, ""])
        for scene in chapter.scenes:
            location_name = _location_name(document, scene.location_id)
            lines.append(scene.title)
            lines.append(f"{location_name} / {scene.time}")
            lines.append(f"出场人物：{_scene_character_names(document, scene.characters)}")
            lines.append(scene.synopsis)
            for direction in scene.stage_directions:
                lines.append(f"[动作] {direction}")
            for dialogue in scene.dialogue:
                lines.append(f"{dialogue.speaker_name}：{dialogue.line}")
            lines.append("")

    return "\n".join(lines).strip() + "\n"


def _parse_screenplay(yaml_text: str) -> ScreenplayDocument:
    try:
        parsed = yaml.safe_load(yaml_text)
        return ScreenplayDocument.model_validate(parsed)
    except (yaml.YAMLError, ValidationError, ValueError, TypeError) as exc:
        raise ValueError("已保存剧本 YAML 无法转换。") from exc


def _location_name(document: ScreenplayDocument, location_id: str) -> str:
    for location in document.script.locations:
        if location.id == location_id:
            return location.name
    return location_id


def _scene_character_names(document: ScreenplayDocument, character_ids: list[str]) -> str:
    name_by_id = {character.id: character.name for character in document.script.characters}
    return "、".join(name_by_id.get(character_id, character_id) for character_id in character_ids)

from __future__ import annotations

import json
from typing import Iterable

import yaml
from pydantic import ValidationError

from app.schemas.screenplay import ConflictNote, ScreenplayDocument


GENDER_LABELS = {
    "male": "男",
    "female": "女",
    "unknown": "未知",
}

EMOTION_LABELS = {
    "neutral": "平静",
    "calm": "平静",
    "angry": "愤怒",
    "fear": "恐惧",
    "sad": "悲伤",
    "happy": "高兴",
    "surprised": "惊讶",
    "urgent": "急切",
    "confused": "疑惑",
}


def screenplay_yaml_to_chinese_markdown(yaml_text: str) -> str:
    document = _parse_screenplay(yaml_text)
    script = document.script
    metadata = script.metadata
    character_names = _character_names(document)
    location_names = _location_names(document)

    lines = [
        f"# {metadata.title}",
        "",
        "## 基本信息",
        "",
        f"- 剧本标题：{metadata.title}",
        f"- 原著：{metadata.original_novel}",
        f"- 作者：{metadata.author or '未知'}",
        f"- 剧本类型：{metadata.script_type or _format_label(metadata.target_format)}",
        f"- 改编方式：{metadata.adaptation_style or metadata.adaptation_mode}",
        f"- 章节数量：{metadata.total_chapters}",
        "",
        "## 人物表",
        "",
        "| 人物 | 身份 | 性别 | 年龄 | 说明 |",
        "| --- | --- | --- | --- | --- |",
    ]

    for character in script.characters:
        gender = GENDER_LABELS.get(character.gender, character.gender or "未知")
        age = str(character.age) if character.age is not None else "未知"
        lines.append(
            f"| {_cell(character.name)} | {_cell(character.role)} | {_cell(gender)} | "
            f"{_cell(age)} | {_cell(character.description)} |"
        )

    lines.extend(["", "## 地点表", "", "| 地点 | 说明 |", "| --- | --- |"])
    for location in script.locations:
        lines.append(f"| {_cell(location.name)} | {_cell(location.description)} |")

    lines.extend(["", "## 剧本正文", ""])
    for chapter in script.chapters:
        lines.extend([f"### {chapter.title}", "", "#### 章节摘要", "", chapter.summary or "暂无摘要", ""])

        for scene in chapter.scenes:
            location = location_names.get(scene.location_id, "未知地点")
            scene_characters = _names_from_ids(scene.characters, character_names)
            lines.extend([
                f"#### 场景：{scene.title}",
                "",
                f"- 地点：{location}",
                f"- 时间：{scene.time}",
                f"- 出场人物：{scene_characters or '暂无'}",
                "",
                "##### 场景说明",
                "",
                scene.synopsis or "暂无说明",
                "",
            ])

            if scene.stage_directions:
                lines.extend(["##### 舞台调度", ""])
                lines.extend(f"- {direction}" for direction in scene.stage_directions)
                lines.append("")

            if scene.dialogue:
                lines.extend(["##### 对白", ""])
                for dialogue in scene.dialogue:
                    speaker = _dialogue_speaker_name(dialogue.speaker_id, dialogue.speaker_name, character_names)
                    emotion = EMOTION_LABELS.get(dialogue.emotion, dialogue.emotion or "平静")
                    lines.append(f"- **{speaker}**（情绪：{emotion}）：{dialogue.line}")
                lines.append("")

    lines.extend(["## 改编说明", ""])
    if script.adaptation_notes.themes:
        lines.extend(["### 主题", ""])
        lines.extend(f"- {theme}" for theme in script.adaptation_notes.themes)
        lines.append("")

    if script.adaptation_notes.conflicts:
        lines.extend(["### 核心冲突", ""])
        lines.extend(_conflict_lines(script.adaptation_notes.conflicts, character_names))
        lines.append("")

    if script.adaptation_notes.omissions:
        lines.extend(["### 压缩说明", ""])
        lines.extend(f"- {omission}" for omission in script.adaptation_notes.omissions)
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def screenplay_yaml_to_json_text(yaml_text: str) -> str:
    document = _parse_screenplay(yaml_text)
    return json.dumps(document.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n"


def screenplay_yaml_to_markdown(yaml_text: str) -> str:
    return screenplay_yaml_to_chinese_markdown(yaml_text)


def screenplay_yaml_to_txt(yaml_text: str) -> str:
    markdown = screenplay_yaml_to_chinese_markdown(yaml_text)
    text = markdown.replace("#", "").replace("| --- | --- | --- | --- | --- |", "")
    text = text.replace("| --- | --- |", "")
    return "\n".join(line.strip(" |") for line in text.splitlines()).strip() + "\n"


def _parse_screenplay(yaml_text: str) -> ScreenplayDocument:
    try:
        parsed = yaml.safe_load(yaml_text)
        return ScreenplayDocument.model_validate(parsed)
    except (yaml.YAMLError, ValidationError, ValueError, TypeError) as exc:
        raise ValueError("已保存剧本无法转换，请先完成格式校验。") from exc


def _character_names(document: ScreenplayDocument) -> dict[str, str]:
    return {character.id: character.name for character in document.script.characters}


def _location_names(document: ScreenplayDocument) -> dict[str, str]:
    return {location.id: location.name for location in document.script.locations}


def _names_from_ids(ids: Iterable[str], name_by_id: dict[str, str]) -> str:
    return "、".join(name_by_id.get(item_id, "未知人物") for item_id in ids)


def _dialogue_speaker_name(speaker_id: str | None, speaker_name: str, name_by_id: dict[str, str]) -> str:
    if speaker_id and speaker_id in name_by_id:
        return name_by_id[speaker_id]
    return speaker_name or "人物"


def _conflict_lines(conflicts: list[str | ConflictNote], name_by_id: dict[str, str]) -> list[str]:
    lines: list[str] = []
    for conflict in conflicts:
        if isinstance(conflict, str):
            lines.append(f"- {conflict}")
            continue

        characters = _names_from_ids(conflict.characters, name_by_id)
        suffix = f"（涉及：{characters}）" if characters else ""
        lines.append(f"- **{conflict.type}**：{conflict.description}{suffix}")
    return lines


def _format_label(target_format: str) -> str:
    labels = {
        "screenplay": "影视剧",
        "short_drama": "短剧",
        "stage_play": "话剧",
        "storyboard": "分镜",
        "audio_drama": "广播剧",
    }
    return labels.get(target_format, target_format or "未设置")


def _cell(value: object) -> str:
    return str(value or "").replace("|", "｜").replace("\n", " ")

from typing import Any

import yaml


ALLOWED_CONTENT_TYPES = {"dialogue", "action", "narration", "inner_voice"}


def validate_script_yaml(yaml_text: str) -> tuple[bool, list[str]]:
    errors: list[str] = []
    try:
        parsed = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        return False, [f"YAML parse error: {exc}"]

    if not isinstance(parsed, dict):
        return False, ["YAML root must be an object."]

    script = parsed.get("script")
    if not isinstance(script, dict):
        return False, ["Missing script object."]

    scenes = _collect_scenes(script)
    if not scenes:
        errors.append("script must contain at least one scene.")

    for scene_index, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            errors.append(f"scene #{scene_index} must be an object.")
            continue

        scene_id = scene.get("id")
        if not scene_id:
            errors.append(f"scene #{scene_index} must have id.")

        contents = scene.get("content", [])
        if not isinstance(contents, list):
            errors.append(f"scene {scene_id or scene_index} content must be a list.")
            continue

        for item_index, item in enumerate(contents, start=1):
            _validate_content_item(item, f"scene {scene_id or scene_index} content #{item_index}", errors)

    return not errors, errors


def _collect_scenes(script: dict[str, Any]) -> list[Any]:
    direct_scenes = script.get("scenes")
    if isinstance(direct_scenes, list):
        return direct_scenes

    scenes: list[Any] = []
    for chapter in script.get("chapters", []) or []:
        if isinstance(chapter, dict) and isinstance(chapter.get("scenes"), list):
            scenes.extend(chapter["scenes"])
    return scenes


def _validate_content_item(item: Any, path: str, errors: list[str]) -> None:
    if not isinstance(item, dict):
        errors.append(f"{path} must be an object.")
        return

    item_type = item.get("type")
    if item_type not in ALLOWED_CONTENT_TYPES:
        errors.append(f"{path} type must be one of dialogue/action/narration/inner_voice.")

    if item_type == "dialogue":
        speaker = item.get("speaker")
        if not isinstance(speaker, str) or not speaker.strip():
            errors.append(f"{path} dialogue must have speaker. Use unknown if uncertain.")
        if not isinstance(item.get("text"), str) or not item["text"].strip():
            errors.append(f"{path} dialogue must have text.")

    if item_type in ALLOWED_CONTENT_TYPES:
        source_text = item.get("source_text")
        if not isinstance(source_text, str) or not source_text.strip():
            errors.append(f"{path} must keep source_text.")

from __future__ import annotations

from typing import Any


def normalize_character_name(name: str) -> str | None:
    cleaned = str(name or "").strip()
    return cleaned or None


def is_valid_character_name(name: str, text: str | None = None) -> bool:
    return bool(normalize_character_name(name))


def isValidCharacterName(name: str) -> bool:
    return is_valid_character_name(name)


def has_character_evidence(canonical: str, text: str) -> bool:
    return bool(normalize_character_name(canonical))


def aliases_for(canonical: str, character_pool: list[dict[str, Any]] | None = None) -> list[str]:
    aliases = [canonical] if canonical else []
    if character_pool:
        for character in character_pool:
            if character.get("name") != canonical:
                continue
            aliases.extend(str(item) for item in character.get("aliases", []) or [] if item)
            break
    return list(dict.fromkeys(aliases))


def canonicalize_character_list(characters: list[Any], text: str = "") -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for item in characters:
        if isinstance(item, dict):
            name = normalize_character_name(item.get("name") or item.get("canonicalName") or "")
            aliases = [str(alias).strip() for alias in item.get("aliases", []) or [] if str(alias).strip()]
            role = str(item.get("role") or "")
            description = str(item.get("description") or item.get("evidence") or "")
            is_confirmed = bool(item.get("is_confirmed", False))
        else:
            name = normalize_character_name(str(item))
            aliases = []
            role = ""
            description = ""
            is_confirmed = False
        if not name or name in seen_names:
            continue
        seen_names.add(name)
        result.append(
            {
                "id": f"char_{len(result) + 1:03d}",
                "name": name,
                "aliases": [alias for alias in dict.fromkeys(aliases) if alias != name],
                "role": role,
                "description": description,
                "is_confirmed": is_confirmed,
            }
        )
    return result


def filter_scene_character_names(names: list[str], character_pool: list[dict[str, Any]]) -> list[str]:
    pool = {str(item.get("name")) for item in character_pool if item.get("name")}
    alias_to_name = {
        str(alias): str(item.get("name"))
        for item in character_pool
        for alias in (item.get("aliases", []) or [])
        if item.get("name") and alias
    }
    result = []
    for name in names:
        cleaned = normalize_character_name(name)
        canonical = alias_to_name.get(cleaned or "", cleaned)
        if canonical in pool and canonical not in result:
            result.append(canonical)
    return result


def normalize_speaker(speaker: str | None, character_pool: list[dict[str, Any]]) -> str | None:
    cleaned = normalize_character_name(speaker or "")
    if not cleaned:
        return None
    for item in character_pool:
        name = str(item.get("name") or "")
        aliases = {str(alias) for alias in item.get("aliases", []) or []}
        if cleaned == name or cleaned in aliases:
            return name
    return None

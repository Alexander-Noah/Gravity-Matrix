import re
from collections import Counter
from typing import Any


ALIAS_TO_CANONICAL = {
    "\u9648\u5e9c\u5c39": "\u9648\u6c49\u5149",
    "\u9648\u6c49\u5149": "\u9648\u6c49\u5149",
    "\u9ec4\u88d9\u5c11\u5973": "\u891a\u91c7\u8587",
    "\u91c7\u8587": "\u891a\u91c7\u8587",
    "\u891a\u91c7\u8587": "\u891a\u91c7\u8587",
    "\u4e8c\u53d4": "\u8bb8\u5e73\u5fd7",
    "\u8bb8\u5e73\u5fd7": "\u8bb8\u5e73\u5fd7",
    "\u8bb8\u5bb6\u4e8c\u90ce": "\u8bb8\u65b0\u5e74",
    "\u8bb8\u65b0\u5e74": "\u8bb8\u65b0\u5e74",
}

CANONICAL_ALIAS_GROUPS = {
    "\u9648\u6c49\u5149": ["\u9648\u5e9c\u5c39", "\u9648\u6c49\u5149"],
    "\u891a\u91c7\u8587": ["\u9ec4\u88d9\u5c11\u5973", "\u91c7\u8587", "\u891a\u91c7\u8587"],
    "\u8bb8\u5e73\u5fd7": ["\u4e8c\u53d4", "\u8bb8\u5e73\u5fd7"],
    "\u8bb8\u65b0\u5e74": ["\u8bb8\u5bb6\u4e8c\u90ce", "\u8bb8\u65b0\u5e74"],
}

STOP_NAMES = {
    "\u53ef\u4ee5", "\u4f60\u8bf4", "\u4ed6\u8bf4", "\u5979\u8bf4", "\u6211\u8bf4", "\u8fd9\u91cc", "\u7136\u540e",
    "\u8fd9\u65f6", "\u4ec0\u4e48", "\u81ea\u5df1", "\u6ca1\u6709", "\u5df2\u7ecf", "\u60f3\u5230\u8fd9\u91cc",
    "\u987f\u4e86\u987f", "\u4ed6\u4eec", "\u5979\u4eec", "\u6211\u4eec", "\u4f60\u4eec", "\u4f17\u4eba",
    "\u90a3\u4eba", "\u6b64\u4eba", "\u4e00\u4eba", "\u7537\u4eba", "\u5973\u4eba", "\u5c11\u5973",
    "\u8fd9\u4e2a", "\u90a3\u4e2a", "\u4e00\u4e2a", "\u4e00\u58f0", "\u4e00\u773c", "\u4e00\u9635",
    "\u7acb\u523b", "\u5ffd\u7136", "\u7a81\u7136", "\u63a5\u7740", "\u4e8e\u662f", "\u56e0\u4e3a",
    "\u6240\u4ee5", "\u4f46\u662f", "\u53ea\u662f", "\u5f53\u7136", "\u5176\u5b9e", "\u539f\u6765",
    "\u4e0d\u8fc7", "\u8fd8\u662f", "\u5e76\u4e14", "\u800c\u4e14", "\u5982\u679c", "\u53ea\u89c1",
}

ACTION_SUFFIXES = [
    "\u987f\u4e86\u987f", "\u611f\u89c9", "\u70b9\u5934", "\u6447\u5934", "\u56de\u7b54", "\u4f4e\u58f0",
    "\u5410", "\u77a5", "\u70b9", "\u8bf4", "\u9053", "\u95ee", "\u7b11", "\u558a", "\u53eb", "\u770b",
    "\u671b", "\u60f3", "\u8d70", "\u5750", "\u7ad9", "\u542c", "\u63a5", "\u62ac", "\u8f6c", "\u62ff",
]

ACTION_WORDS = {
    "\u611f\u89c9", "\u60f3\u5230", "\u987f\u4e86\u987f", "\u6ca1\u6709", "\u5df2\u7ecf", "\u53ef\u4ee5",
    "\u8bf4", "\u9053", "\u95ee", "\u7b54", "\u558a", "\u53eb", "\u770b", "\u671b", "\u77a5", "\u5410",
    "\u70b9", "\u7b11", "\u54ed", "\u8d70", "\u5750", "\u7ad9", "\u542c", "\u63a5", "\u62ac", "\u8f6c",
    "\u63e1", "\u63a8", "\u62c9", "\u653e", "\u62ff", "\u79bb\u5f00", "\u8d70\u8fdb", "\u8d77\u8eab",
}

IDENTITY_WORDS = {
    "\u5e9c\u5c39", "\u5c11\u5973", "\u4e8c\u53d4", "\u4e8c\u90ce", "\u5927\u90ce", "\u59d1\u5a18",
    "\u516c\u5b50", "\u5927\u4eba", "\u592b\u4eba", "\u5c0f\u59d0", "\u5148\u751f", "\u6355\u5934",
    "\u4e66\u751f", "\u8001\u7237", "\u5927\u54e5", "\u7236\u4eb2", "\u6bcd\u4eb2", "\u4e3b\u89d2",
}


def normalize_character_name(name: str) -> str | None:
    cleaned = re.sub(r"\s+", "", str(name or ""))
    cleaned = cleaned.strip("\u3000 \t\r\n\uff0c\u3001\u3002\uff1a:\uff1b;\uff01!\uff1f?\uff08\uff09()<>\u300a\u300b\"'")
    if not cleaned:
        return None

    if cleaned in ALIAS_TO_CANONICAL:
        return ALIAS_TO_CANONICAL[cleaned]

    for suffix in sorted(ACTION_SUFFIXES, key=len, reverse=True):
        if cleaned.endswith(suffix) and len(cleaned) > len(suffix):
            cleaned = cleaned[: -len(suffix)]
            break

    return ALIAS_TO_CANONICAL.get(cleaned, cleaned)


def is_valid_character_name(name: str, text: str | None = None) -> bool:
    canonical = normalize_character_name(name)
    if not canonical:
        return False
    if not (2 <= len(canonical) <= 5):
        return False
    if not re.fullmatch(r"[\u4e00-\u9fff]{2,5}", canonical):
        return False
    if canonical in STOP_NAMES:
        return False
    if canonical in {"unknown", "\u65c1\u767d"}:
        return False
    if any(word in canonical for word in ACTION_WORDS):
        return False
    if text is None:
        return True
    return has_character_evidence(canonical, text)


def isValidCharacterName(name: str) -> bool:
    return is_valid_character_name(name)


def has_character_evidence(canonical: str, text: str) -> bool:
    aliases = aliases_for(canonical)
    mentions = sum(text.count(alias) for alias in aliases)
    if mentions >= 2:
        return True
    if any(alias in IDENTITY_WORDS or any(word in alias for word in IDENTITY_WORDS) for alias in aliases):
        return True
    identity_pattern = r"(?:%s)(?:\u662f|\u4e3a|\u4e43|\uff0c|\u8fd9\u4f4d|\u90a3\u4f4d)?.{0,8}(?:%s)" % (
        "|".join(re.escape(alias) for alias in aliases),
        "|".join(re.escape(word) for word in IDENTITY_WORDS),
    )
    return re.search(identity_pattern, text) is not None


def aliases_for(canonical: str) -> list[str]:
    aliases = CANONICAL_ALIAS_GROUPS.get(canonical, [canonical])
    return list(dict.fromkeys([*aliases, canonical]))


def canonicalize_character_list(characters: list[Any], text: str) -> list[dict[str, Any]]:
    scores: Counter[str] = Counter()
    descriptions: dict[str, str] = {}
    roles: dict[str, str] = {}
    extra_aliases: dict[str, list[str]] = {}

    for item in characters:
        if isinstance(item, dict):
            raw_name = str(item.get("name") or item.get("canonicalName") or "")
            role = str(item.get("role") or "")
            description = str(item.get("evidence") or item.get("description") or "")
        else:
            raw_name = str(item)
            role = ""
            description = ""

        canonical = normalize_character_name(raw_name)
        if not canonical or not is_valid_character_name(canonical, text):
            continue
        aliases = aliases_for(canonical)
        if isinstance(item, dict) and isinstance(item.get("aliases"), list):
            for alias in item["aliases"]:
                alias_text = str(alias).strip()
                normalized_alias = normalize_character_name(alias_text)
                if normalized_alias == canonical:
                    alias_value = alias_text
                else:
                    alias_value = normalized_alias or alias_text
                if (
                    2 <= len(alias_value) <= 5
                    and re.fullmatch(r"[\u4e00-\u9fff]{2,5}", alias_value)
                    and alias_value not in STOP_NAMES
                    and not any(word in alias_value for word in ACTION_WORDS)
                ):
                    aliases.append(alias_value)
                    extra_aliases.setdefault(canonical, []).append(alias_value)

        scores[canonical] += max(1, sum(text.count(alias) for alias in set(aliases)))
        roles.setdefault(canonical, role)
        descriptions.setdefault(canonical, description)

    for alias, canonical in ALIAS_TO_CANONICAL.items():
        if alias in text and is_valid_character_name(canonical, text):
            scores[canonical] += text.count(alias) + 3

    ordered = sorted(scores, key=lambda name: (-scores[name], text.find(aliases_for(name)[0]), name))
    result = []
    for index, canonical in enumerate(ordered, start=1):
        alias_values = [
            alias
            for alias in dict.fromkeys([*aliases_for(canonical), *extra_aliases.get(canonical, [])])
            if alias != canonical
        ]
        result.append(
            {
                "id": f"char_{index:03d}",
                "name": canonical,
                "aliases": alias_values,
                "role": roles.get(canonical) or ("\u4e3b\u89d2" if index == 1 else "\u89d2\u8272"),
                "description": descriptions.get(canonical) or f"\u4ece\u539f\u6587\u4e2d\u8bc6\u522b\u5230\u7684\u4eba\u7269\uff1a{canonical}",
                "is_confirmed": False,
            }
        )
    return result


def filter_scene_character_names(names: list[str], character_pool: list[dict[str, Any]]) -> list[str]:
    pool = {str(item.get("name")) for item in character_pool if item.get("name")}
    result = []
    for name in names:
        canonical = normalize_character_name(str(name))
        if canonical in pool and canonical not in result:
            result.append(canonical)
    return result


def normalize_speaker(speaker: str | None, character_pool: list[dict[str, Any]]) -> str | None:
    canonical = normalize_character_name(speaker or "")
    pool = {str(item.get("name")) for item in character_pool if item.get("name")}
    return canonical if canonical in pool else None

from typing import Any

import yaml
from pydantic import ValidationError

from app.schemas.screenplay import ScreenplayDocument


def dump_screenplay_yaml(data: dict[str, Any]) -> str:
    document = ScreenplayDocument.model_validate(data)
    return yaml.safe_dump(
        document.model_dump(mode="json"),
        allow_unicode=True,
        sort_keys=False,
    )


def validate_screenplay_yaml(yaml_text: str) -> tuple[bool, list[str]]:
    try:
        parsed = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        return False, [f"YAML 解析失败：{exc}"]

    if not isinstance(parsed, dict):
        return False, ["YAML 顶层必须是对象，并包含 script 字段。"]

    try:
        ScreenplayDocument.model_validate(parsed)
    except ValidationError as exc:
        return False, [error["msg"] for error in exc.errors()]
    except ValueError as exc:
        return False, [str(exc)]

    return True, []

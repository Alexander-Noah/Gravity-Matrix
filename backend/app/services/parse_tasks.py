from __future__ import annotations

import json
import logging
import re
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.db.session import SessionLocal
from app.models.project import Project
from app.services.frontend_data import get_novel_source_project_payload
from app.services import llm as llm_service


CHUNK_TARGET_CHARS = 3000
CHUNK_OVERLAP_CHARS = 200
CHUNK_MAX_ATTEMPTS = 3
CHUNK_LLM_TIMEOUT_SECONDS = 30

logger = logging.getLogger(__name__)


@dataclass
class ParseTask:
    id: str
    status: str = "pending"
    progress: int = 0
    message: str = "等待开始"
    source_text: str | None = None
    source_file_id: str | None = None
    project_id: int | None = None
    result_json: dict[str, Any] | None = None
    result_yaml: str | None = None
    error_message: str | None = None
    raw_response: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ParseStageError(ValueError):
    def __init__(self, message: str, raw_response: str | None = None) -> None:
        super().__init__(message)
        self.raw_response = raw_response


parse_tasks: dict[str, ParseTask] = {}
_task_lock = threading.RLock()


def create_parse_task(
    *,
    source_text: str | None = None,
    source_file_id: str | None = None,
    project_id: int | None = None,
) -> ParseTask:
    task = ParseTask(
        id=str(uuid.uuid4()),
        source_text=source_text,
        source_file_id=source_file_id,
        project_id=project_id,
    )
    with _task_lock:
        parse_tasks[task.id] = task
    return task


def get_parse_task(task_id: str) -> ParseTask | None:
    with _task_lock:
        return parse_tasks.get(task_id)


def run_parse_task(task_id: str) -> None:
    task = get_parse_task(task_id)
    if task is None:
        return

    try:
        _update_task(task_id, status="running", progress=5, message="正在读取小说文本")
        source_text, title = _task_source_text(task)
        if not source_text.strip():
            raise ValueError("解析文本不能为空。")

        _update_task(task_id, progress=10, message="正在切分章节")
        chunks = split_text_into_chunks(source_text)
        if not chunks:
            raise ValueError("未能切分出可解析文本块。")

        chunk_results = []
        total_chunks = len(chunks)
        for index, chunk in enumerate(chunks, start=1):
            progress = 10 + int(index / total_chunks * 70)
            _update_task(task_id, progress=progress, message=f"正在解析第 {index} / {total_chunks} 个文本块")
            parsed_chunk = _parse_chunk(chunk, index)
            if not llm_service._is_valid_chapter_analysis(parsed_chunk):
                raise ValueError(f"第 {index} 个文本块解析结果格式无效。")
            chunk_results.append(
                {
                    "chapter_number": index,
                    "source_title": chunk["title"],
                    "analysis": parsed_chunk,
                }
            )

        _update_task(task_id, progress=88, message="正在合并剧本解析结果")
        result = _merge_chunk_results(title, chunk_results)
        _save_project_result(task.project_id, result)
        _update_task(
            task_id,
            status="success",
            progress=100,
            message="解析完成",
            result_json=result,
        )
    except Exception as exc:
        raw_response = getattr(exc, "raw_response", None) or llm_service.get_last_llm_raw_response()
        raw_response_head = raw_response[:1000] if raw_response else None
        if raw_response_head:
            logger.error("Parse task failed with AI raw response head=%r", raw_response_head)
            print(f"Parse task AI raw/error head: {raw_response_head}", flush=True)
        _update_task(
            task_id,
            status="failed",
            progress=get_parse_task(task_id).progress if get_parse_task(task_id) else 0,
            message="解析失败",
            error_message=_error_message_with_raw(str(exc), raw_response_head),
            raw_response=raw_response_head,
        )


def split_text_into_chunks(text: str) -> list[dict[str, Any]]:
    chapters = _split_chapters(text)
    chunks: list[dict[str, Any]] = []
    for chapter_index, chapter in enumerate(chapters, start=1):
        chapter_chunks = _split_long_chapter(chapter["content"])
        for chunk_index, chunk_text in enumerate(chapter_chunks, start=1):
            suffix = f" / 片段 {chunk_index}" if len(chapter_chunks) > 1 else ""
            chunks.append(
                {
                    "title": f"{chapter['title']}{suffix}",
                    "content": chunk_text,
                    "chapter_index": chapter_index,
                    "chunk_index": chunk_index,
                }
            )
    return chunks


def _task_source_text(task: ParseTask) -> tuple[str, str]:
    if task.source_text:
        return task.source_text, "小说解析任务"

    if task.source_file_id:
        source_id = task.source_file_id.removeprefix("source-")
        payload = get_novel_source_project_payload(source_id)
        if payload is None:
            raise ValueError("素材文件不存在或无法读取。")
        text = "\n\n".join(f"{chapter['title']}\n{chapter['content']}" for chapter in payload["chapters"])
        return text, payload["title"]

    if task.project_id is None:
        raise ValueError("请提供小说文本或 project_id。")

    with SessionLocal() as db:
        project = db.get(Project, task.project_id)
        if project is None:
            raise ValueError("项目不存在。")
        text = "\n\n".join(f"{chapter.title}\n{chapter.content}" for chapter in project.chapters)
        return text, project.title


def _split_chapters(text: str) -> list[dict[str, str]]:
    pattern = re.compile(
        r"(?im)^\s*((?:第\s*[0-9一二三四五六七八九十百千万零〇两]+\s*[章节回卷部篇幕集].*)|(?:chapter\s+(?:\d+|[ivxlcdm]+).*))$"
    )
    matches = list(pattern.finditer(text))
    if not matches:
        return [{"title": "全文", "content": text.strip()}]

    chapters = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        title = match.group(1).strip()
        content = text[start:end].strip()
        if content:
            chapters.append({"title": title, "content": content})
    return chapters or [{"title": "全文", "content": text.strip()}]


def _split_long_chapter(text: str) -> list[str]:
    text = text.strip()
    if len(text) <= CHUNK_TARGET_CHARS:
        return [text] if text else []

    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        ideal_end = min(start + CHUNK_TARGET_CHARS, text_length)
        end = text_length if ideal_end >= text_length else _find_chunk_end(text, start, ideal_end)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_length:
            break
        start = max(end - CHUNK_OVERLAP_CHARS, start + 1)
    return chunks


def _find_chunk_end(text: str, start: int, ideal_end: int) -> int:
    min_end = max(start + int(CHUNK_TARGET_CHARS * 0.75), start + 1)
    max_end = min(len(text), ideal_end + 400)
    search = text[min_end:max_end]
    boundaries = ("\n\n", "\r\n\r\n", "\n", "。”", "！”", "？”", "。", "！", "？", "；")
    candidates = []

    for marker in boundaries:
        marker_start = 0
        while True:
            index = search.find(marker, marker_start)
            if index < 0:
                break
            candidates.append(min_end + index + len(marker))
            marker_start = index + len(marker)

    if not candidates:
        return ideal_end

    return min(candidates, key=lambda value: (abs(value - ideal_end), value > ideal_end))


def _parse_chunk(chunk: dict[str, Any], chunk_number: int) -> dict[str, Any]:
    character_result = _call_parse_stage(
        "角色",
        _characters_prompt(chunk, chunk_number),
        _normalize_characters_response,
        chunk,
        chunk_number,
    )
    characters = character_result["characters"]

    location_result = _call_parse_stage(
        "地点",
        _locations_prompt(chunk, chunk_number, characters),
        _normalize_locations_response,
        chunk,
        chunk_number,
    )
    locations = location_result["locations"]

    story_result = _call_parse_stage(
        "剧情与对白",
        _story_prompt(chunk, chunk_number, characters, locations),
        lambda parsed: _normalize_story_response(parsed, characters, locations),
        chunk,
        chunk_number,
    )

    return {
        "chapter_title": chunk["title"],
        "characters": characters,
        "locations": locations,
        "organizations": story_result["organizations"],
        "events": story_result["events"],
        "dialogues": story_result["dialogues"],
    }


def _call_parse_stage(
    stage_name: str,
    prompt: str,
    normalize,
    chunk: dict[str, Any],
    chunk_number: int,
) -> dict[str, Any]:
    last_error = "LLM 未返回有效 JSON。"
    last_hint = ""
    last_raw_response = None

    for attempt in range(1, CHUNK_MAX_ATTEMPTS + 1):
        parsed = llm_service._call_deepseek(prompt, timeout_seconds=CHUNK_LLM_TIMEOUT_SECONDS)
        normalized = normalize(parsed)
        if normalized is not None:
            return normalized
        last_error = f"第 {attempt} 次返回格式无效。"
        last_hint = _invalid_response_hint(parsed)
        raw_response = llm_service.get_last_llm_raw_response()
        if raw_response:
            last_raw_response = raw_response[:1000]
            logger.warning(
                "AI raw response for %s parse failed chunk=%s attempt=%s head=%r",
                stage_name,
                chunk_number,
                attempt,
                last_raw_response,
            )
            print(
                f"AI raw/error for {stage_name} parse failed chunk={chunk_number} attempt={attempt}: {last_raw_response}",
                flush=True,
            )

    detail = f"；{last_hint}" if last_hint else ""
    raise ParseStageError(
        f"第 {chunk_number} 个文本块（{chunk['title']}）{stage_name}解析失败：{last_error}{detail}",
        raw_response=last_raw_response,
    )


def _invalid_response_hint(parsed: Any) -> str:
    if parsed is None:
        return "最后一次未解析到 JSON 对象"
    if isinstance(parsed, dict):
        keys = list(parsed.keys())[:8]
        return f"最后一次返回字段：{', '.join(str(key) for key in keys) or '空对象'}"
    return f"最后一次返回类型：{type(parsed).__name__}"


def _error_message_with_raw(message: str, raw_response: str | None) -> str:
    if not raw_response:
        return message
    return f"{message}\n\nAI 原始返回/异常前 1000 字：\n{raw_response}"


def _characters_prompt(chunk: dict[str, Any], chunk_number: int) -> str:
    template = {
        "characters": [
            {
                "name": "人物姓名",
                "aliases": [],
                "role": "角色定位",
                "description": "只根据原文证据概括",
                "evidence": "原文中能证明该人物出现的短句",
            }
        ]
    }
    return "\n".join(
        [
            "你是小说角色识别器。只识别人物角色，不要分析地点、事件或对白。",
            "严格返回 JSON 对象，不要输出 Markdown、解释或代码块。",
            "要求：",
            "1. characters 只能包含真实人物、拟人化角色或明确有行动/说话能力的角色。",
            "2. 不要把动作短语、语气短语、地名、机构名、称谓描述或普通名词识别成人物。",
            "3. 例如“从而增加”“有话就”“沉声道”“推断很有”“中年男人”都不是人物姓名。",
            "4. 如果只有称谓没有姓名，可以保留称谓，但 evidence 必须来自原文。",
            "5. 没有人物时返回 {\"characters\": []}。",
            "返回 JSON 必须符合这个结构：",
            json.dumps(template, ensure_ascii=False),
            f"文本块编号：{chunk_number}",
            f"文本块标题：{chunk['title']}",
            "文本块内容：",
            chunk["content"],
        ]
    )


def _locations_prompt(chunk: dict[str, Any], chunk_number: int, characters: list[dict[str, Any]]) -> str:
    template = {
        "locations": [
            {
                "name": "地点名称",
                "description": "只根据原文证据概括",
                "evidence": "原文中能证明该地点出现的短句",
            }
        ]
    }
    return "\n".join(
        [
            "你是小说地点识别器。只识别地点，不要新增人物。",
            "严格返回 JSON 对象，不要输出 Markdown、解释或代码块。",
            "要求：",
            "1. locations 只能包含真实或剧情中的地点、场所、建筑、区域。",
            "2. 不要把人物、动作短语、心理描写或普通物品识别成地点。",
            "3. 没有地点时返回 {\"locations\": []}。",
            "已识别人物白名单，仅用于避免把人物当地点：",
            json.dumps([item.get("name") for item in characters if item.get("name")], ensure_ascii=False),
            "返回 JSON 必须符合这个结构：",
            json.dumps(template, ensure_ascii=False),
            f"文本块编号：{chunk_number}",
            f"文本块标题：{chunk['title']}",
            "文本块内容：",
            chunk["content"],
        ]
    )


def _story_prompt(
    chunk: dict[str, Any],
    chunk_number: int,
    characters: list[dict[str, Any]],
    locations: list[dict[str, Any]],
) -> str:
    template = {
        "organizations": [{"name": "组织名称", "description": "", "evidence": ""}],
        "events": [
            {
                "title": "事件标题",
                "summary": "事件摘要",
                "characters": ["必须来自人物白名单"],
                "location": "优先来自地点白名单",
                "evidence": "原文依据",
            }
        ],
        "dialogues": [
            {
                "speaker": "必须来自人物白名单，不确定则为 null",
                "line": "原文对白或旁白",
                "line_type": "dialogue",
                "emotion": "neutral",
                "evidence": "原文依据",
            }
        ],
    }
    return "\n".join(
        [
            "你是小说剧情与对白分析器。不要重新识别人物和地点，只能使用白名单。",
            "严格返回 JSON 对象，不要输出 Markdown、解释或代码块。",
            "要求：",
            "1. events.characters 只能从人物白名单中选择。",
            "2. dialogues.speaker 只能从人物白名单中选择，不确定时填 null。",
            "3. dialogues.line_type 只能是 dialogue、monologue 或 narration。",
            "4. 不要把“沉声道”“有话就”“从而增加”等短语当成 speaker。",
            "5. 没有组织、事件或对白时对应字段返回空数组。",
            "人物白名单：",
            json.dumps(characters, ensure_ascii=False),
            "地点白名单：",
            json.dumps(locations, ensure_ascii=False),
            "返回 JSON 必须符合这个结构：",
            json.dumps(template, ensure_ascii=False),
            f"文本块编号：{chunk_number}",
            f"文本块标题：{chunk['title']}",
            "文本块内容：",
            chunk["content"],
        ]
    )


CHARACTER_KEYS = (
    "characters", "character_list", "role_characters", "roles", "role_list",
    "人物", "人物列表", "角色", "角色列表", "主要人物", "主要角色", "角色分析", "人物分析",
)
LOCATION_KEYS = ("locations", "location_list", "places", "place_list", "地点", "地点列表", "场景", "场景列表", "场所", "场所列表")
ORGANIZATION_KEYS = ("organizations", "organization_list", "orgs", "组织", "组织列表", "机构", "机构列表")
EVENT_KEYS = ("events", "event_list", "剧情事件", "事件", "事件列表")
DIALOGUE_KEYS = ("dialogues", "dialogue_list", "lines", "对白", "对白列表", "台词", "台词列表")


def _normalize_characters_response(parsed: Any) -> dict[str, Any] | None:
    payload = _find_payload_with_any_key(parsed, CHARACTER_KEYS)
    characters = _first_collection_value(payload, CHARACTER_KEYS) if payload is not None else None
    if characters is None:
        return None
    normalized = _normalize_named_items(characters, include_role=True)
    if not normalized:
        return None
    return {"characters": normalized}


def _normalize_locations_response(parsed: Any) -> dict[str, Any] | None:
    payload = _find_payload_with_any_key(parsed, LOCATION_KEYS)
    locations = _first_collection_value(payload, LOCATION_KEYS) if payload is not None else None
    if locations is None:
        return None
    return {"locations": _normalize_named_items(locations, include_role=False)}


def _normalize_story_response(
    parsed: Any,
    characters: list[dict[str, Any]],
    locations: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not isinstance(parsed, dict):
        return None
    payload = _find_payload_with_any_key(parsed, ORGANIZATION_KEYS + EVENT_KEYS + DIALOGUE_KEYS)
    if payload is None:
        return None

    organizations = _first_collection_value(payload, ORGANIZATION_KEYS) or []
    events = _first_collection_value(payload, EVENT_KEYS) or []
    dialogues = _first_collection_value(payload, DIALOGUE_KEYS) or []
    character_names = _character_name_set(characters)
    location_names = {str(item.get("name")) for item in locations if item.get("name")}

    return {
        "organizations": _normalize_named_items(organizations, include_role=False),
        "events": [_normalize_event(item, character_names, location_names) for item in events if isinstance(item, dict)],
        "dialogues": [
            _normalize_dialogue_line_with_characters(item, character_names)
            for item in dialogues
            if isinstance(item, dict)
        ],
    }


def _find_payload_with_any_key(parsed: Any, keys: tuple[str, ...]) -> dict[str, Any] | None:
    for candidate in _walk_dicts(parsed):
        if any(key in candidate for key in keys):
            return candidate
    return None


def _walk_dicts(value: Any, *, max_depth: int = 5) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    def visit(item: Any, depth: int) -> None:
        if depth > max_depth:
            return
        if isinstance(item, dict):
            result.append(item)
            for child in item.values():
                visit(child, depth + 1)
        elif isinstance(item, list):
            for child in item:
                visit(child, depth + 1)

    visit(value, 0)
    return result


def _first_collection_value(payload: dict[str, Any], keys: tuple[str, ...]) -> list[Any] | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            nested_payload = _find_payload_with_any_key(value, tuple(candidate for candidate in keys if candidate != key))
            if nested_payload is not None:
                nested_value = _first_collection_value(nested_payload, keys)
                if nested_value is not None:
                    return nested_value
            return _mapping_to_items(value)
        if isinstance(value, str) and value.strip():
            return _split_name_string(value)
    return None


def _mapping_to_items(value: dict[str, Any]) -> list[Any]:
    items: list[Any] = []
    for name, data in value.items():
        if isinstance(data, dict):
            item = {"name": name, **data}
        else:
            item = {"name": name, "description": str(data or "")}
        items.append(item)
    return items


def _split_name_string(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[、，,；;\n]+", value) if item.strip()]


def _normalize_named_items(items: list[Any], *, include_role: bool) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        if isinstance(item, dict):
            nested_items = _first_collection_value(item, CHARACTER_KEYS if include_role else LOCATION_KEYS)
            if nested_items is not None:
                for nested in _normalize_named_items(nested_items, include_role=include_role):
                    if nested["name"] not in seen:
                        seen.add(nested["name"])
                        result.append(nested)
                continue

            name = str(_first_present(item, ("name", "canonical", "canonicalName", "姓名", "名字", "名称", "人物", "角色", "角色名")) or "").strip()
            aliases_value = _first_present(item, ("aliases", "alias", "别名", "称呼"))
            if isinstance(aliases_value, list):
                aliases = [str(alias).strip() for alias in aliases_value if str(alias).strip()]
            elif isinstance(aliases_value, str):
                aliases = _split_name_string(aliases_value)
            else:
                aliases = []
            role = str(_first_present(item, ("role", "身份", "职业", "角色定位", "定位")) or "").strip()
            description = str(_first_present(item, ("description", "描述", "简介", "说明")) or "").strip()
            evidence = str(_first_present(item, ("evidence", "证据", "原文依据", "依据")) or "").strip()
        else:
            name = str(item or "").strip()
            aliases = []
            role = ""
            description = ""
            evidence = ""

        if not name or name in seen:
            continue
        seen.add(name)
        normalized = {
            "name": name,
            "aliases": [alias for alias in dict.fromkeys(aliases) if alias != name],
            "description": description,
            "evidence": evidence,
        }
        if include_role:
            normalized["role"] = role
        result.append(normalized)
    return result


def _first_present(data: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return None


def _character_name_set(characters: list[dict[str, Any]]) -> set[str]:
    names: set[str] = set()
    for character in characters:
        name = character.get("name")
        if name:
            names.add(str(name))
        names.update(str(alias) for alias in character.get("aliases", []) or [] if alias)
    return names


def _canonical_from_set(name: Any, allowed_names: set[str]) -> str | None:
    value = str(name or "").strip()
    return value if value in allowed_names else None


def _normalize_event(item: dict[str, Any], character_names: set[str], location_names: set[str]) -> dict[str, Any]:
    raw_characters_value = _first_present(item, ("characters", "人物", "角色", "参与人物"))
    raw_characters = raw_characters_value if isinstance(raw_characters_value, list) else []
    location = str(_first_present(item, ("location", "地点", "场景", "发生地点")) or "").strip()
    return {
        "title": str(_first_present(item, ("title", "标题", "事件标题")) or "").strip(),
        "summary": str(_first_present(item, ("summary", "摘要", "概述", "事件摘要")) or "").strip(),
        "characters": [
            canonical
            for canonical in (_canonical_from_set(name, character_names) for name in raw_characters)
            if canonical
        ],
        "location": location if not location_names or location in location_names else "",
        "evidence": str(_first_present(item, ("evidence", "证据", "原文依据", "依据")) or "").strip(),
    }


def _normalize_dialogue_line_with_characters(line: dict[str, Any], character_names: set[str]) -> dict[str, Any]:
    normalized = _normalize_dialogue_line(line)
    normalized["speaker"] = _canonical_from_set(normalized.get("speaker"), character_names)
    return normalized


def _normalize_dialogue_line(line: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(line)
    normalized["speaker"] = _first_present(normalized, ("speaker", "说话人", "角色", "人物"))
    normalized["line"] = _first_present(normalized, ("line", "台词", "对白", "内容")) or ""
    normalized["emotion"] = _first_present(normalized, ("emotion", "情绪")) or ""
    normalized["evidence"] = _first_present(normalized, ("evidence", "证据", "原文依据", "依据")) or ""
    line_type = str(_first_present(normalized, ("line_type", "type", "类型")) or "dialogue").strip().lower()
    line_type_map = {
        "dialog": "dialogue",
        "dialogue": "dialogue",
        "speech": "dialogue",
        "对白": "dialogue",
        "对话": "dialogue",
        "monologue": "monologue",
        "inner": "monologue",
        "心理": "monologue",
        "内心独白": "monologue",
        "narration": "narration",
        "旁白": "narration",
        "叙述": "narration",
    }
    normalized["line_type"] = line_type_map.get(line_type, "dialogue")
    return normalized


def _merge_chunk_results(title: str, chunk_results: list[dict[str, Any]]) -> dict[str, Any]:
    character_names: list[str] = []
    location_names: list[str] = []
    organizations: list[dict[str, Any]] = []
    for item in chunk_results:
        analysis = item.get("analysis") or {}
        character_names.extend(character.get("name") for character in analysis.get("characters", []) if character.get("name"))
        location_names.extend(location.get("name") for location in analysis.get("locations", []) if location.get("name"))
        organizations.extend(analysis.get("organizations", []))

    characters = [
        {"id": f"char_{index:03d}", "name": name, "aliases": [], "role": "角色", "description": "分块解析识别的人物。"}
        for index, name in enumerate(llm_service._unique(character_names) or ["旁白"], start=1)
    ]
    locations = [
        {"id": f"loc_{index:03d}", "name": name, "description": "分块解析识别的地点。"}
        for index, name in enumerate(llm_service._unique(location_names) or ["未明确地点"], start=1)
    ]
    return {
        "source": "parse_task_chunks",
        "title": title,
        "chapter_analyses": chunk_results,
        "characters": characters,
        "locations": locations,
        "organizations": [
            {
                "id": f"org_{index:03d}",
                "name": item["name"],
                "description": item.get("description") or "分块解析识别的组织。",
            }
            for index, item in enumerate(llm_service._unique_dicts(organizations, "name"), start=1)
        ],
        "alias_map": [],
        "candidate_aliases": [],
        "themes": ["小说改编", "分块解析"],
        "conflicts": ["人物目标与情节阻碍之间的冲突"],
    }


def _save_project_result(project_id: int | None, result: dict[str, Any]) -> None:
    if project_id is None:
        return
    with SessionLocal() as db:
        project = db.get(Project, project_id)
        if project is None:
            return
        project.analysis_json = json.dumps(result, ensure_ascii=False)
        project.script_yaml = None
        project.status = "analysis_completed"
        db.commit()


def _update_task(task_id: str, **changes: Any) -> None:
    with _task_lock:
        task = parse_tasks.get(task_id)
        if task is None:
            return
        for key, value in changes.items():
            setattr(task, key, value)
        task.updated_at = datetime.now(timezone.utc)

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.core.config import BACKEND_DIR, settings
from app.db.session import SessionLocal
from app.models.project import Project
from app.services.frontend_data import get_novel_source_project_payload
from app.services import llm as llm_service


PARSE_PROMPT_VERSION = "parse_chunk_v5_relationships"
CHUNK_CACHE_DIR = BACKEND_DIR / ".cache" / "llm_chunks"
CHUNK_MAX_ATTEMPTS = max(settings.llm_max_retries + 1, 1)

logger = logging.getLogger(__name__)


def _is_local_ollama() -> bool:
    return (settings.llm_provider or "").strip().lower() == "ollama"


def _parse_timeout_seconds() -> int:
    if _is_local_ollama():
        return max(settings.llm_timeout_seconds, 900)
    return settings.llm_timeout_seconds


def _parse_max_concurrency() -> int:
    if _is_local_ollama():
        return 1
    return settings.llm_max_concurrency


def _parse_chunk_size() -> int:
    if _is_local_ollama():
        return min(settings.llm_chunk_size, 1000)
    return settings.llm_chunk_size


def _parse_chunk_limits() -> dict[str, int]:
    if _is_local_ollama():
        return {
            "characters": 4,
            "locations": 3,
            "organizations": 3,
            "events": 3,
            "dialogues": 4,
            "relationships": 4,
            "conflicts": 3,
            "summary": 50,
            "description": 30,
            "evidence": 20,
        }
    return {
        "characters": 8,
        "locations": 6,
        "organizations": 5,
        "events": 5,
        "dialogues": 8,
        "relationships": 8,
        "conflicts": 5,
        "summary": 60,
        "description": 30,
        "evidence": 20,
    }


def _parse_chunk_max_tokens() -> int:
    return 900 if _is_local_ollama() else 1800


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
    failed_chunks: list[dict[str, Any]] = field(default_factory=list)
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


def get_active_project_parse_task(project_id: int | None) -> ParseTask | None:
    if project_id is None:
        return None
    with _task_lock:
        active_tasks = [
            task
            for task in parse_tasks.values()
            if task.project_id == project_id and task.status in {"pending", "running"}
        ]
    if not active_tasks:
        return None
    return max(active_tasks, key=lambda task: task.created_at)


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

        chunk_results, failed_chunks = asyncio.run(_parse_chunks_concurrently(task_id, chunks))

        if not chunk_results:
            _update_task(
                task_id,
                status="failed",
                progress=100,
                message="解析失败",
                error_message="本地模型解析超时，请减少文本长度或稍后重试",
                failed_chunks=failed_chunks,
            )
            return

        _update_task(task_id, progress=88, message="正在合并剧本解析结果")
        result = _merge_chunk_results(title, chunk_results, failed_chunks)
        result["conflicts"] = _merge_conflicts_from_chunk_results(chunk_results) or result.get("conflicts", [])
        result["failed_chunks"] = failed_chunks
        _save_project_result(task.project_id, result)
        final_status = "completed_with_warnings" if failed_chunks else "completed"
        final_message = "部分内容解析失败，可稍后重试" if failed_chunks else "解析完成"
        _update_task(
            task_id,
            status=final_status,
            progress=100,
            message=final_message,
            result_json=result,
            failed_chunks=failed_chunks,
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


async def _parse_chunks_concurrently(
    task_id: str,
    chunks: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    semaphore = asyncio.Semaphore(_parse_max_concurrency())
    total_chunks = len(chunks)
    completed = 0
    completed_lock = asyncio.Lock()

    async def parse_one(index: int, chunk: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        nonlocal completed
        async with semaphore:
            _update_task(
                task_id,
                progress=10 + int(completed / total_chunks * 70),
                message=f"正在解析第 {index} / {total_chunks} 个文本块",
            )
            try:
                parsed_chunk = await asyncio.to_thread(_parse_chunk, chunk, index)
                if not llm_service._is_valid_chapter_analysis(parsed_chunk):
                    raise ValueError("文本块解析结果格式无效。")
                result = {
                    "chapter_number": index,
                    "source_title": chunk["title"],
                    "analysis": parsed_chunk,
                }
                failed = None
            except Exception as exc:
                raw_response = getattr(exc, "raw_response", None) or llm_service.get_last_llm_raw_response()
                failed = {
                    "chunk_number": index,
                    "title": chunk.get("title") or f"chunk {index}",
                    "error": str(exc),
                    "raw_response": (raw_response or "")[:1000] if raw_response else None,
                }
                print(f"Parse chunk {index} failed, continuing: {exc}", flush=True)
                logger.exception("Parse chunk %s failed", index)
                result = None

            async with completed_lock:
                completed += 1
                _update_task(
                    task_id,
                    progress=10 + int(completed / total_chunks * 70),
                    message=f"已完成 {completed} / {total_chunks} 个文本块",
                )
            return result, failed

    parsed = await asyncio.gather(
        *(parse_one(index, chunk) for index, chunk in enumerate(chunks, start=1))
    )
    chunk_results = [result for result, _failed in parsed if result is not None]
    failed_chunks = [failed for _result, failed in parsed if failed is not None]
    return chunk_results, failed_chunks


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
    chunk_size = _parse_chunk_size()
    chunk_overlap = min(settings.llm_chunk_overlap, max(chunk_size - 1, 0))
    if len(text) <= chunk_size:
        return [text] if text else []

    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        ideal_end = min(start + chunk_size, text_length)
        end = text_length if ideal_end >= text_length else _find_chunk_end(text, start, ideal_end)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_length:
            break
        start = max(end - chunk_overlap, start + 1)
    return chunks


def _find_chunk_end(text: str, start: int, ideal_end: int) -> int:
    min_end = max(start + int(_parse_chunk_size() * 0.75), start + 1)
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
    cache_key = _chunk_cache_key(chunk["content"])
    cached = _read_chunk_cache(cache_key)
    if cached is not None:
        logger.info("LLM cache hit chunk=%s key=%s", chunk_number, cache_key)
        print(f"LLM cache hit chunk={chunk_number} key={cache_key}", flush=True)
        return cached

    parsed = llm_service._call_deepseek(
        _single_chunk_prompt(chunk, chunk_number),
        timeout_seconds=_parse_timeout_seconds(),
        max_tokens=_parse_chunk_max_tokens(),
        purpose=f"parse_chunk_{chunk_number}",
    )
    normalized = _normalize_single_chunk_response(parsed, chunk)
    if normalized is None:
        raw_response = llm_service.get_last_llm_raw_response()
        raise ParseStageError(
            f"第 {chunk_number} 个文本块（{chunk['title']}）解析失败：LLM 未返回有效结构。",
            raw_response=raw_response[:1000] if raw_response else None,
        )
    _write_chunk_cache(cache_key, normalized)
    return normalized


def _chunk_cache_key(chunk_text: str) -> str:
    model = settings.llm_model or settings.ollama_model or ""
    payload = "\n".join([chunk_text or "", settings.llm_provider or "", model, PARSE_PROMPT_VERSION])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _read_chunk_cache(cache_key: str) -> dict[str, Any] | None:
    if not settings.llm_enable_cache:
        return None
    path = CHUNK_CACHE_DIR / f"{cache_key}.json"
    if not path.exists():
        return None
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Failed to read LLM chunk cache %s: %s", path, exc)
        return None
    return cached if isinstance(cached, dict) else None


def _write_chunk_cache(cache_key: str, result: dict[str, Any]) -> None:
    if not settings.llm_enable_cache:
        return
    try:
        CHUNK_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = CHUNK_CACHE_DIR / f"{cache_key}.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        logger.warning("Failed to write LLM chunk cache key=%s: %s", cache_key, exc)


def _single_chunk_prompt(chunk: dict[str, Any], chunk_number: int) -> str:
    limits = _parse_chunk_limits()
    template = {
        "characters": [{"name": "", "aliases": [], "role": "", "description": "", "evidence": ""}],
        "locations": [{"name": "", "description": "", "evidence": ""}],
        "organizations": [{"name": "", "description": "", "evidence": ""}],
        "events": [{"title": "", "summary": "", "characters": [], "location": "", "evidence": ""}],
        "dialogues": [{"speaker": "", "line": "", "line_type": "dialogue", "emotion": "", "evidence": ""}],
        "relationships": [{"source": "", "target": "", "relation": "", "description": "", "evidence": ""}],
        "conflicts": [],
    }
    return "\n".join(
        [
            "你是小说结构化解析器。只返回严格 JSON 对象，不要 markdown，不要解释。",
            "一次性解析当前文本块，返回 characters、locations、organizations、events、dialogues、relationships、conflicts。",
            "禁止返回 narration，禁止返回旁白，禁止复制大段原文。",
            (
                "数量限制："
                f"characters 最多 {limits['characters']} 个；"
                f"locations 最多 {limits['locations']} 个；"
                f"organizations 最多 {limits['organizations']} 个；"
                f"events 最多 {limits['events']} 个；"
                f"dialogues 最多 {limits['dialogues']} 条；"
                f"relationships 最多 {limits['relationships']} 条；"
                f"conflicts 最多 {limits['conflicts']} 条。"
            ),
            (
                "长度限制："
                f"description 不超过 {limits['description']} 字；"
                f"summary 不超过 {limits['summary']} 字；"
                f"evidence 不超过 {limits['evidence']} 字。"
            ),
            "dialogues 只保留明确说话人的真实对白；不确定说话人就不要返回该条。",
            "dialogues.line_type 只能是 dialogue 或 monologue。",
            "relationships 必须只使用 characters 中出现的人物姓名，描述人物之间的亲属、上下级、合作、冲突或对话互动。",
            "不要把动作短语、语气短语、地点、组织、普通名词识别成人物。",
            "返回 JSON 必须符合这个结构：",
            json.dumps(template, ensure_ascii=False),
            f"prompt_version: {PARSE_PROMPT_VERSION}",
            f"文本块编号：{chunk_number}",
            f"文本块标题：{chunk['title']}",
            "文本块内容：",
            chunk["content"],
        ]
    )


def _normalize_single_chunk_response(parsed: Any, chunk: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(parsed, dict):
        return None
    limits = _parse_chunk_limits()
    characters = _normalize_named_items(_as_list(parsed.get("characters"))[:limits["characters"]], include_role=True)
    locations = _normalize_named_items(_as_list(parsed.get("locations"))[:limits["locations"]], include_role=False)
    organizations = _normalize_named_items(_as_list(parsed.get("organizations"))[:limits["organizations"]], include_role=False)
    character_names = _character_name_set(characters)
    location_names = {str(item.get("name")) for item in locations if item.get("name")}

    normalized = {
        "chapter_title": chunk["title"],
        "characters": [_limit_named_item(item, include_role=True) for item in characters[:limits["characters"]]],
        "locations": [_limit_named_item(item, include_role=False) for item in locations[:limits["locations"]]],
        "organizations": [_limit_named_item(item, include_role=False) for item in organizations[:limits["organizations"]]],
        "events": [
            _limit_event(_normalize_event(item, character_names, location_names), limits)
            for item in _as_list(parsed.get("events"))[:limits["events"]]
            if isinstance(item, dict)
        ],
        "dialogues": [
            item
            for item in (
                _limit_dialogue(_normalize_dialogue_line_with_characters(line, character_names))
                for line in _as_list(parsed.get("dialogues"))[:limits["dialogues"]]
                if isinstance(line, dict)
            )
            if item is not None
        ],
        "relationships": [
            item
            for item in (
                _limit_relationship(_normalize_relationship(relation, character_names), limits)
                for relation in _as_list(parsed.get("relationships"))[:limits["relationships"]]
                if isinstance(relation, dict)
            )
            if item is not None
        ],
        "conflicts": _limit_string_list(_as_list(parsed.get("conflicts")), limits["conflicts"], limits["summary"]),
    }
    return normalized


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _clip_text(value: Any, limit: int) -> str:
    text = re.sub(r"\s+", "", str(value or ""))
    return text[:limit]


def _limit_named_item(item: dict[str, Any], *, include_role: bool) -> dict[str, Any]:
    result = {
        "name": _clip_text(item.get("name"), 20),
        "aliases": [_clip_text(alias, 20) for alias in item.get("aliases", [])[:3] if _clip_text(alias, 20)],
        "description": _clip_text(item.get("description"), 30),
        "evidence": _clip_text(item.get("evidence"), 20),
    }
    if include_role:
        result["role"] = _clip_text(item.get("role"), 20)
    return result


def _limit_event(item: dict[str, Any], limits: dict[str, int] | None = None) -> dict[str, Any]:
    limits = limits or _parse_chunk_limits()
    return {
        "title": _clip_text(item.get("title"), 30),
        "summary": _clip_text(item.get("summary"), limits["summary"]),
        "characters": [_clip_text(name, 20) for name in item.get("characters", [])[:8] if _clip_text(name, 20)],
        "location": _clip_text(item.get("location"), 20),
        "evidence": _clip_text(item.get("evidence"), limits["evidence"]),
    }


def _limit_dialogue(line: dict[str, Any]) -> dict[str, Any] | None:
    speaker = _clip_text(line.get("speaker"), 20)
    text = _clip_text(line.get("line"), 80)
    line_type = str(line.get("line_type") or "dialogue").strip().lower()
    if not speaker or not text or speaker == "旁白" or line_type == "narration":
        return None
    if line_type not in {"dialogue", "monologue"}:
        line_type = "dialogue"
    return {
        "speaker": speaker,
        "line": text,
        "line_type": line_type,
        "emotion": _clip_text(line.get("emotion"), 20) or "neutral",
        "evidence": _clip_text(line.get("evidence"), 20),
    }


def _limit_relationship(item: dict[str, Any] | None, limits: dict[str, int] | None = None) -> dict[str, Any] | None:
    if not item:
        return None
    limits = limits or _parse_chunk_limits()
    source = _clip_text(item.get("source"), 20)
    target = _clip_text(item.get("target"), 20)
    if not source or not target or source == target:
        return None
    return {
        "source": source,
        "target": target,
        "relation": _clip_text(item.get("relation"), 20) or "关联人物",
        "description": _clip_text(item.get("description"), limits["summary"]),
        "evidence": _clip_text(item.get("evidence"), limits["evidence"]),
    }


def _limit_string_list(items: list[Any], max_count: int, max_len: int) -> list[str]:
    result = []
    for item in items:
        text = _clip_text(item, max_len)
        if text:
            result.append(text)
        if len(result) >= max_count:
            break
    return result


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
        parsed = llm_service._call_deepseek(prompt, timeout_seconds=_parse_timeout_seconds())
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


def _normalize_relationship(item: dict[str, Any], character_names: set[str]) -> dict[str, Any] | None:
    source = _canonical_from_set(
        _first_present(item, ("source", "from", "character_a", "人物A", "来源人物")),
        character_names,
    )
    target = _canonical_from_set(
        _first_present(item, ("target", "to", "character_b", "人物B", "目标人物")),
        character_names,
    )
    if not source or not target or source == target:
        return None
    return {
        "source": source,
        "target": target,
        "relation": str(_first_present(item, ("relation", "relationship", "type", "关系", "关系类型")) or "").strip(),
        "description": str(_first_present(item, ("description", "note", "summary", "说明", "描述")) or "").strip(),
        "evidence": str(_first_present(item, ("evidence", "证据", "原文依据", "依据")) or "").strip(),
    }


def _merge_conflicts_from_chunk_results(chunk_results: list[dict[str, Any]]) -> list[str]:
    conflicts: list[str] = []
    for item in chunk_results:
        analysis = item.get("analysis") or {}
        conflicts.extend(str(conflict) for conflict in analysis.get("conflicts", []) if conflict)
    return llm_service._unique(conflicts)[:20]


def _merge_character_items(character_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for item in character_items:
        name = _clip_text(item.get("name"), 20)
        if not name:
            continue
        current = merged.setdefault(
            name,
            {
                "name": name,
                "aliases": [],
                "role": "",
                "description": "",
                "evidence": "",
            },
        )
        for alias in item.get("aliases", []) or []:
            alias_text = _clip_text(alias, 20)
            if alias_text and alias_text != name and alias_text not in current["aliases"]:
                current["aliases"].append(alias_text)
        if not current["role"] and item.get("role"):
            current["role"] = _clip_text(item.get("role"), 20)
        if not current["description"] and item.get("description"):
            current["description"] = _clip_text(item.get("description"), 60)
        if not current["evidence"] and item.get("evidence"):
            current["evidence"] = _clip_text(item.get("evidence"), 20)

    result = []
    for index, item in enumerate(merged.values(), start=1):
        role = _specific_role(item["name"], item.get("role"), item.get("description"))
        description = item.get("description") or _default_character_description(item["name"], role, item.get("evidence"))
        result.append(
            {
                "id": f"char_{index:03d}",
                "name": item["name"],
                "aliases": item.get("aliases", [])[:3],
                "role": role,
                "description": _clip_text(description, 60),
            }
        )
    return result


def _specific_role(name: str, role: Any, description: Any = "") -> str:
    value = _clip_text(role, 20)
    if value and value not in {"角色", "人物", "主要角色"}:
        return value
    text = f"{name}{description}"
    role_rules = (
        ("许七安", "主角"),
        ("堂弟", "堂弟"),
        ("叔父", "叔父"),
        ("二叔", "叔父"),
        ("府尹", "府尹"),
        ("打更人", "打更人"),
        ("司天监", "司天监术士"),
        ("术士", "司天监术士"),
        ("狱卒", "狱卒"),
        ("少女", "关键人物"),
        ("妖", "妖族相关人物"),
    )
    for keyword, inferred in role_rules:
        if keyword in text:
            return inferred
    return "剧情人物"


def _default_character_description(name: str, role: str, evidence: Any = "") -> str:
    evidence_text = _clip_text(evidence, 24)
    if evidence_text:
        return f"{role}，在情节中与{evidence_text}相关，推动案件和人物冲突。"
    return f"{role}，在已解析情节中推动事件发展，并影响主角行动选择。"


def _relationship_key(source: str, target: str) -> tuple[str, str]:
    return tuple(sorted((source, target)))


def _merge_relationships(chunk_results: list[dict[str, Any]], character_names: set[str]) -> list[dict[str, Any]]:
    relationships: dict[tuple[str, str], dict[str, Any]] = {}

    def add_relation(source: Any, target: Any, relation: str, note: str = "", evidence: str = "") -> None:
        source_name = _canonical_from_set(source, character_names)
        target_name = _canonical_from_set(target, character_names)
        if not source_name or not target_name or source_name == target_name:
            return
        key = _relationship_key(source_name, target_name)
        relationships.setdefault(
            key,
            {
                "source": source_name,
                "target": target_name,
                "relation": relation,
                "description": note,
                "evidence": evidence,
            },
        )

    for item in chunk_results:
        analysis = item.get("analysis") or {}
        for relation in analysis.get("relationships", []) or []:
            if isinstance(relation, dict):
                normalized = _normalize_relationship(relation, character_names)
                if normalized:
                    add_relation(
                        normalized.get("source"),
                        normalized.get("target"),
                        normalized.get("relation") or "人物关系",
                        normalized.get("description") or normalized.get("evidence") or "共同参与关键情节。",
                        normalized.get("evidence") or "",
                    )

        for event in analysis.get("events", []) or []:
            names = [name for name in event.get("characters", []) or [] if name in character_names]
            for index, source in enumerate(names):
                for target in names[index + 1:]:
                    add_relation(
                        source,
                        target,
                        "共同参与事件",
                        event.get("summary") or event.get("title") or "共同出现在同一剧情事件中。",
                        event.get("evidence") or "",
                    )

        previous_speaker = None
        for line in analysis.get("dialogues", []) or []:
            speaker = line.get("speaker")
            if previous_speaker and speaker and previous_speaker != speaker:
                add_relation(
                    previous_speaker,
                    speaker,
                    "对话互动",
                    line.get("line") or "在对白中发生互动。",
                    line.get("evidence") or "",
                )
            if speaker:
                previous_speaker = speaker

    return [
        {
            "source": item["source"],
            "target": item["target"],
            "relation": item["relation"],
            "note": _clip_text(item.get("description") or item.get("evidence") or "共同推动剧情发展。", 60),
            "evidence": _clip_text(item.get("evidence"), 20),
        }
        for item in list(relationships.values())[:12]
    ]


def _merge_chunk_results(
    title: str,
    chunk_results: list[dict[str, Any]],
    failed_chunks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    character_items: list[dict[str, Any]] = []
    location_names: list[str] = []
    organizations: list[dict[str, Any]] = []
    conflicts: list[str] = []
    for item in chunk_results:
        analysis = item.get("analysis") or {}
        character_items.extend(character for character in analysis.get("characters", []) if character.get("name"))
        location_names.extend(location.get("name") for location in analysis.get("locations", []) if location.get("name"))
        organizations.extend(analysis.get("organizations", []))
        conflicts.extend(str(conflict) for conflict in analysis.get("conflicts", []) if conflict)

    characters = _merge_character_items(character_items) or [
        {"id": "char_001", "name": "旁白", "aliases": [], "role": "叙述", "description": "暂无明确人物，等待重新解析补充。"}
    ]
    character_names = {character["name"] for character in characters}
    relationships = _merge_relationships(chunk_results, character_names)
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
        "relationships": relationships,
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

from __future__ import annotations

import json
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
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


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
        _update_task(
            task_id,
            status="failed",
            progress=get_parse_task(task_id).progress if get_parse_task(task_id) else 0,
            message="解析失败",
            error_message=str(exc),
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
    prompt = _chunk_prompt(chunk, chunk_number)
    last_error = "LLM 未返回有效 JSON。"

    for attempt in range(1, CHUNK_MAX_ATTEMPTS + 1):
        parsed = llm_service._call_deepseek(prompt, timeout_seconds=CHUNK_LLM_TIMEOUT_SECONDS)
        if llm_service._is_valid_chapter_analysis(parsed):
            return parsed
        last_error = f"第 {attempt} 次返回格式无效。"

    raise ValueError(f"第 {chunk_number} 个文本块（{chunk['title']}）解析失败：{last_error}")


def _chunk_prompt(chunk: dict[str, Any], chunk_number: int) -> str:
    template = {
        "chapter_title": chunk["title"],
        "characters": [{"name": "", "aliases": [], "role": "", "description": "", "evidence": ""}],
        "locations": [{"name": "", "description": "", "evidence": ""}],
        "organizations": [{"name": "", "description": "", "evidence": ""}],
        "events": [{"title": "", "summary": "", "characters": [], "location": "", "evidence": ""}],
        "dialogues": [{"speaker": "", "line": "", "line_type": "dialogue", "emotion": "", "evidence": ""}],
    }
    return "\n".join(
        [
            "你是小说分块结构化解析器。严格返回 JSON，不要输出解释。",
            "只解析当前文本块，不要编造未出现的人物、地点或对白。",
            "dialogues.line_type 只能是 dialogue、monologue 或 narration。",
            "返回 JSON 必须符合这个结构：",
            json.dumps(template, ensure_ascii=False),
            f"文本块编号：{chunk_number}",
            f"文本块标题：{chunk['title']}",
            "文本块内容：",
            chunk["content"],
        ]
    )


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

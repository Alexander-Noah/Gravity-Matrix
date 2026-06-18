from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services import llm as llm_service
from app.services.llm import _parse_json_object
from app.services.parse_tasks import (
    create_parse_task,
    parse_tasks,
    run_parse_task,
    split_text_into_chunks,
)


PASTED_TEXT_PATH = Path("C:/Users/34717/.codex/attachments/902782b3-e750-4564-af9d-62b93673dc6c/pasted-text.txt")


def _valid_chunk_response(title: str = "第一章 开端") -> dict:
    return {
        "chapter_title": title,
        "characters": [{"name": "许七安", "aliases": [], "role": "主角", "description": "", "evidence": "许七安"}],
        "locations": [{"name": "京兆府监牢", "description": "", "evidence": "京兆府，监牢"}],
        "organizations": [],
        "events": [{"title": "牢狱醒来", "summary": "许七安醒来并意识到处境。", "characters": ["许七安"], "location": "京兆府监牢", "evidence": "醒来"}],
        "dialogues": [{"speaker": "许七安", "line": "我在哪？", "line_type": "dialogue", "emotion": "confused", "evidence": "我在哪？"}],
    }


def setup_function() -> None:
    parse_tasks.clear()


def teardown_function() -> None:
    parse_tasks.clear()


def test_split_text_recognizes_pasted_novel_chapters() -> None:
    if PASTED_TEXT_PATH.exists():
        text = PASTED_TEXT_PATH.read_text(encoding="utf-8")
    else:
        text = " 第一章 牢狱之灾\n正文\n\n 第二章 妖物作祟\n正文\n\n 第三章 仙侠世界一样能推理\n正文"

    chunks = split_text_into_chunks(text)

    assert len(chunks) >= 3
    assert chunks[0]["title"].startswith("第一章")
    assert chunks[1]["title"].startswith("第二章")
    assert chunks[2]["title"].startswith("第三章")


def test_split_long_chapter_keeps_overlap() -> None:
    text = "第一章 长章\n" + ("abcdefg" * 1000)

    chunks = split_text_into_chunks(text)

    assert len(chunks) >= 3
    assert len(chunks[0]["content"]) <= 3000
    assert chunks[0]["content"][-200:] == chunks[1]["content"][:200]


def test_run_parse_task_retries_invalid_llm_response(monkeypatch) -> None:
    calls = {"count": 0}

    def fake_call_deepseek(prompt: str, timeout_seconds: int | None = None):
        calls["count"] += 1
        if calls["count"] == 1:
            return {"bad": "shape"}
        return _valid_chunk_response()

    monkeypatch.setattr(llm_service, "_call_deepseek", fake_call_deepseek)
    task = create_parse_task(source_text="第一章 开端\n许七安说：“我在哪？”")

    run_parse_task(task.id)

    assert calls["count"] == 2
    assert parse_tasks[task.id].status == "success"
    assert parse_tasks[task.id].progress == 100


def test_parse_json_object_extracts_fenced_json() -> None:
    content = """解析如下：
```json
{"characters": [], "locations": [], "events": [], "dialogues": []}
```
请查收。"""

    parsed = _parse_json_object(content)

    assert parsed == {"characters": [], "locations": [], "events": [], "dialogues": []}


def test_run_parse_task_marks_failed_after_chunk_retries(monkeypatch) -> None:
    monkeypatch.setattr(llm_service, "_call_deepseek", lambda prompt, timeout_seconds=None: None)
    task = create_parse_task(source_text="第一章 开端\n许七安说：“我在哪？”")

    run_parse_task(task.id)

    assert parse_tasks[task.id].status == "failed"
    assert "第 1 个文本块" in (parse_tasks[task.id].error_message or "")


def test_parse_task_result_returns_409_before_success() -> None:
    client = TestClient(app)
    task = create_parse_task(source_text="第一章 开端\n许七安说：“我在哪？”")

    response = client.get(f"/api/v1/parse/tasks/{task.id}/result")

    assert response.status_code == 409

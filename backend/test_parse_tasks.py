from pathlib import Path

from fastapi.testclient import TestClient

from app import main as app_main
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


def test_startup_llm_config_prints_without_api_key(monkeypatch, capsys) -> None:
    monkeypatch.setattr(app_main.settings, "llm_provider", "openai_compatible")
    monkeypatch.setattr(app_main.settings, "llm_base_url", "https://api.deepseek.com")
    monkeypatch.setattr(app_main.settings, "llm_model", "deepseek-chat")
    monkeypatch.setattr(app_main.settings, "llm_timeout_seconds", 30)
    monkeypatch.setattr(app_main.settings, "llm_api_key", "sk-secret-value")

    app_main._print_llm_startup_config()

    output = capsys.readouterr().out
    assert "LLM_PROVIDER=openai_compatible" in output
    assert "LLM_BASE_URL=https://api.deepseek.com" in output
    assert "LLM_MODEL=deepseek-chat" in output
    assert "LLM_TIMEOUT_SECONDS=30" in output
    assert "LLM_API_KEY_SET=true" in output
    assert "sk-secret-value" not in output


def test_startup_llm_config_rejects_missing_or_invalid_base_url(monkeypatch) -> None:
    monkeypatch.setattr(app_main.settings, "llm_base_url", "")

    try:
        app_main._validate_llm_startup_config()
    except RuntimeError as exc:
        assert "LLM_BASE_URL 不能为空" in str(exc)
    else:
        raise AssertionError("expected missing LLM_BASE_URL to fail")

    monkeypatch.setattr(app_main.settings, "llm_base_url", "api.deepseek.com")

    try:
        app_main._validate_llm_startup_config()
    except RuntimeError as exc:
        assert "必须以 http:// 或 https:// 开头" in str(exc)
    else:
        raise AssertionError("expected invalid LLM_BASE_URL to fail")


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

    assert calls["count"] == 4
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


def test_extract_json_from_text_keeps_fallback_parser() -> None:
    content = "说明文字 {\"characters\": [{\"name\": \"许七安\"}]} 结束"

    parsed = llm_service.extract_json_from_text(content)

    assert parsed == {"characters": [{"name": "许七安"}]}


def test_deepseek_payload_uses_json_mode_and_chat_model(monkeypatch) -> None:
    monkeypatch.setattr(llm_service.settings, "llm_provider", "openai_compatible")
    monkeypatch.setattr(llm_service.settings, "llm_base_url", "https://api.deepseek.com")
    monkeypatch.setattr(llm_service.settings, "llm_model", "deepseek-reasoner")

    payload = llm_service._deepseek_request_payload("返回角色")

    assert payload["model"] == "deepseek-chat"
    assert payload["temperature"] == 0.1
    assert payload["max_tokens"] >= 4096
    assert payload["response_format"] == {"type": "json_object"}
    joined_messages = "\n".join(message["content"] for message in payload["messages"])
    assert "json" in joined_messages
    assert "不要 Markdown" in joined_messages
    assert "不要解释" in joined_messages
    assert "不要 ```json 代码块" in joined_messages


def test_deepseek_response_format_falls_back_when_unsupported() -> None:
    class FakeCompletions:
        def __init__(self) -> None:
            self.calls = []

        def create(self, **request):
            self.calls.append(request)
            if len(self.calls) == 1:
                raise RuntimeError("response_format is not supported")
            return "ok"

    completions = FakeCompletions()
    client = type("FakeClient", (), {"chat": type("Chat", (), {"completions": completions})()})()

    result = llm_service._create_chat_completion(
        client,
        {
            "model": "deepseek-chat",
            "messages": [],
            "response_format": {"type": "json_object"},
        },
    )

    assert result == "ok"
    assert "response_format" in completions.calls[0]
    assert "response_format" not in completions.calls[1]


def test_call_deepseek_exposes_connection_error_as_raw(monkeypatch, capsys) -> None:
    class FailingCompletions:
        def create(self, **request):
            raise RuntimeError("Connection error.")

    class FakeOpenAI:
        def __init__(self, **kwargs) -> None:
            self.chat = type("Chat", (), {"completions": FailingCompletions()})()

    monkeypatch.setattr(llm_service, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(llm_service.settings, "llm_provider", "openai_compatible")
    monkeypatch.setattr(llm_service.settings, "llm_base_url", "https://api.deepseek.com")
    monkeypatch.setattr(llm_service.settings, "llm_model", "deepseek-chat")

    result = llm_service._call_deepseek("返回角色")

    captured = capsys.readouterr()
    assert result is None
    assert "Connection error." in llm_service.get_last_llm_raw_response()
    assert "LLM raw/error head:" in captured.out


def test_run_parse_task_marks_failed_after_chunk_retries(monkeypatch, caplog) -> None:
    calls = {"count": 0}

    def fake_call_deepseek(prompt: str, timeout_seconds: int | None = None):
        calls["count"] += 1
        return None

    monkeypatch.setattr(llm_service, "_call_deepseek", fake_call_deepseek)
    monkeypatch.setattr(llm_service, "get_last_llm_raw_response", lambda: "raw non-json response")
    caplog.set_level("WARNING")
    task = create_parse_task(source_text="第一章 开端\n许七安说：“我在哪？”")

    run_parse_task(task.id)

    assert calls["count"] == 3
    assert parse_tasks[task.id].status == "failed"
    assert "第 1 个文本块" in (parse_tasks[task.id].error_message or "")
    assert "AI 原始返回/异常前 1000 字" in (parse_tasks[task.id].error_message or "")
    assert parse_tasks[task.id].raw_response == "raw non-json response"
    assert "raw non-json response" in caplog.text
    assert "attempt=3" in caplog.text

    response = TestClient(app).get(f"/api/v1/parse/tasks/{task.id}")
    assert response.status_code == 200
    assert response.json()["raw_response"] == "raw non-json response"


def test_run_parse_task_accepts_wrapped_analysis_response(monkeypatch) -> None:
    monkeypatch.setattr(
        llm_service,
        "_call_deepseek",
        lambda prompt, timeout_seconds=None: {"analysis": _valid_chunk_response()},
    )
    task = create_parse_task(source_text="第一章 开端\n许七安说：“我在哪？”")

    run_parse_task(task.id)

    assert parse_tasks[task.id].status == "success"


def test_run_parse_task_limits_story_speakers_to_character_stage(monkeypatch) -> None:
    def fake_call_deepseek(prompt: str, timeout_seconds: int | None = None):
        if "角色识别器" in prompt:
            return {
                "characters": [
                    {"name": "许七安", "aliases": [], "role": "主角", "description": "", "evidence": "许七安说"}
                ]
            }
        if "地点识别器" in prompt:
            return {"locations": [{"name": "陈府", "description": "", "evidence": "陈府"}]}
        return {
            "organizations": [],
            "events": [
                {
                    "title": "审问",
                    "summary": "陈府内发生审问。",
                    "characters": ["许七安", "有话就"],
                    "location": "陈府",
                    "evidence": "有话就说",
                }
            ],
            "dialogues": [
                {
                    "speaker": "有话就",
                    "line": "有话就说。",
                    "line_type": "对白",
                    "emotion": "neutral",
                    "evidence": "有话就说",
                }
            ],
        }

    monkeypatch.setattr(llm_service, "_call_deepseek", fake_call_deepseek)
    task = create_parse_task(source_text="第一章 开端\n许七安在陈府听见：“有话就说。”")

    run_parse_task(task.id)

    analysis = parse_tasks[task.id].result_json["chapter_analyses"][0]["analysis"]
    assert analysis["events"][0]["characters"] == ["许七安"]
    assert analysis["dialogues"][0]["speaker"] is None
    assert analysis["dialogues"][0]["line_type"] == "dialogue"


def test_run_parse_task_accepts_deepseek_chinese_keys(monkeypatch) -> None:
    def fake_call_deepseek(prompt: str, timeout_seconds: int | None = None):
        if "角色识别器" in prompt:
            return {
                "人物": [
                    {"姓名": "许七安", "别名": ["许新年"], "身份": "主角", "描述": "牢狱中的人物", "证据": "许七安说"}
                ]
            }
        if "地点识别器" in prompt:
            return {"地点": [{"名称": "牢房", "描述": "关押地点", "证据": "牢房"}]}
        return {
            "组织": [],
            "事件": [
                {
                    "事件标题": "牢中对话",
                    "事件摘要": "许七安在牢房中回应问话。",
                    "参与人物": ["许七安"],
                    "发生地点": "牢房",
                    "原文依据": "许七安说",
                }
            ],
            "对白": [
                {
                    "说话人": "许七安",
                    "内容": "那你呢？",
                    "类型": "对白",
                    "情绪": "平静",
                    "依据": "那你呢？",
                }
            ],
        }

    monkeypatch.setattr(llm_service, "_call_deepseek", fake_call_deepseek)
    task = create_parse_task(source_text="第一章 牢狱之灾\n许七安在牢房里说：“那你呢？”")

    run_parse_task(task.id)

    analysis = parse_tasks[task.id].result_json["chapter_analyses"][0]["analysis"]
    assert parse_tasks[task.id].status == "success"
    assert analysis["characters"][0]["name"] == "许七安"
    assert analysis["locations"][0]["name"] == "牢房"
    assert analysis["events"][0]["characters"] == ["许七安"]
    assert analysis["dialogues"][0]["speaker"] == "许七安"
    assert analysis["dialogues"][0]["line"] == "那你呢？"


def test_run_parse_task_accepts_nested_character_analysis(monkeypatch) -> None:
    def fake_call_deepseek(prompt: str, timeout_seconds: int | None = None):
        if "角色识别器" in prompt:
            return {
                "分析结果": {
                    "角色分析": {
                        "主要角色": {
                            "许七安": {"身份": "主角", "描述": "牢中醒来的角色", "证据": "许七安"}
                        }
                    }
                }
            }
        if "地点识别器" in prompt:
            return {"分析结果": {"地点列表": "牢房"}}
        return {
            "分析结果": {
                "事件列表": [
                    {"标题": "醒来", "摘要": "许七安在牢房中醒来。", "人物": ["许七安"], "地点": "牢房", "依据": "许七安"}
                ],
                "对白列表": [],
            }
        }

    monkeypatch.setattr(llm_service, "_call_deepseek", fake_call_deepseek)
    task = create_parse_task(source_text="第一章 牢狱之灾\n许七安在牢房中醒来。")

    run_parse_task(task.id)

    analysis = parse_tasks[task.id].result_json["chapter_analyses"][0]["analysis"]
    assert parse_tasks[task.id].status == "success"
    assert analysis["characters"][0]["name"] == "许七安"
    assert analysis["locations"][0]["name"] == "牢房"


def test_first_chapter_prison_disaster_character_flow(monkeypatch) -> None:
    def fake_call_deepseek(prompt: str, timeout_seconds: int | None = None):
        if "角色识别器" in prompt:
            return {
                "characters": [
                    {"name": "许七安", "aliases": [], "role": "主角", "description": "牢狱中的人物", "evidence": "许七安鬼使神差的"},
                    {"name": "许新年", "aliases": [], "role": "亲属", "description": "与许七安对话的人", "evidence": "许新年不耐烦"},
                ]
            }
        if "地点识别器" in prompt:
            return {"locations": [{"name": "牢狱", "description": "关押地点", "evidence": "第一章 牢狱之灾"}]}
        return {
            "organizations": [],
            "events": [
                {
                    "title": "牢狱对话",
                    "summary": "许新年与许七安在牢狱相关情境中交谈。",
                    "characters": ["许七安", "许新年", "有话就"],
                    "location": "牢狱",
                    "evidence": "那你呢？",
                }
            ],
            "dialogues": [
                {"speaker": "许七安", "line": "那你呢？", "line_type": "dialogue", "emotion": "疑问", "evidence": "那你呢？"},
                {"speaker": "有话就", "line": "不该被识别为角色", "line_type": "dialogue", "emotion": "", "evidence": "有话就"},
            ],
        }

    monkeypatch.setattr(llm_service, "_call_deepseek", fake_call_deepseek)
    source_text = "\n".join(
        [
            "第一章 牢狱之灾",
            "许新年不耐烦。",
            "我已被革除功名，但有书院师长护着，不需要发配。管好你自己就行了。",
            "去了边陲，收敛脾气，能活一年是一年。",
            "年面无表情的拂袖。与汝何干。",
            "许七安鬼使神差的问：那你呢？",
        ]
    )
    task = create_parse_task(source_text=source_text)

    run_parse_task(task.id)

    analysis = parse_tasks[task.id].result_json["chapter_analyses"][0]["analysis"]
    assert parse_tasks[task.id].status == "success"
    assert [character["name"] for character in analysis["characters"]] == ["许七安", "许新年"]
    assert analysis["events"][0]["characters"] == ["许七安", "许新年"]
    assert analysis["dialogues"][0]["speaker"] == "许七安"
    assert analysis["dialogues"][1]["speaker"] is None


def test_parse_task_result_returns_409_before_success() -> None:
    client = TestClient(app)
    task = create_parse_task(source_text="第一章 开端\n许七安说：“我在哪？”")

    response = client.get(f"/api/v1/parse/tasks/{task.id}/result")

    assert response.status_code == 409

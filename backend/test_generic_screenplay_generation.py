from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app
from app.services.llm import AIParseError, analyze_project, generate_screenplay


def _project(detail_level: str | None = None):
    settings = "{}" if detail_level is None else f'{{"detail_level":"{detail_level}"}}'
    return SimpleNamespace(
        title="AI 解析测试小说",
        author="测试作者",
        generation_settings_json=settings,
        chapters=[
            SimpleNamespace(
                number=1,
                title="第一章 雨夜",
                content="陈府尹反驳道：“不妥。”林青心想：不能再拖。众人进入南桥客栈。",
            ),
            SimpleNamespace(
                number=2,
                title="第二章 追踪",
                content="林青说：“线索在哪里？”赵明道：“在茶楼。”两人离开东市街。",
            ),
            SimpleNamespace(
                number=3,
                title="第三章 对质",
                content="夜晚，赵明喝道：“站住！”黑衣男子离开后门。",
            ),
        ],
    )


def _chapter_response(title: str):
    return {
        "chapter_title": title,
        "characters": [{"name": "林青", "aliases": [], "role": "主角", "description": "", "evidence": "原文出现"}],
        "locations": [{"name": "南桥客栈", "description": "", "evidence": "原文出现"}],
        "organizations": [],
        "events": [{"title": "追查线索", "summary": "人物围绕线索行动", "characters": ["林青"], "location": "南桥客栈", "evidence": "原文"}],
        "dialogues": [{"speaker": "林青", "line": "线索在哪里？", "line_type": "dialogue", "emotion": "neutral", "evidence": "原文"}],
    }


def _global_response():
    return {
        "characters": [
            {"id": "char_001", "name": "林青", "aliases": [], "role": "主角", "description": "AI 识别的人物"},
            {"id": "char_002", "name": "赵明", "aliases": [], "role": "角色", "description": "AI 识别的人物"},
        ],
        "locations": [
            {"id": "loc_001", "name": "南桥客栈", "description": "AI 识别的地点"},
            {"id": "loc_002", "name": "东市街", "description": "AI 识别的地点"},
        ],
        "organizations": [],
        "alias_map": [],
        "themes": [],
        "conflicts": [],
    }


def _screenplay_response(detail_level: str = "standard"):
    return {
        "script": {
            "schema_version": "1.0",
            "metadata": {
                "title": "AI 解析测试小说",
                "original_novel": "AI 解析测试小说",
                "author": "测试作者",
                "language": "zh-CN",
                "target_format": "screenplay",
                "template_id": "tv-drama",
                "script_type": "影视剧",
                "adaptation_style": None,
                "total_chapters": 3,
                "adaptation_mode": detail_level,
                "omitted_reason": "由 AI 根据详细度控制省略。",
                "coverage": {
                    "source_chapters": 3,
                    "generated_scenes": 3,
                    "preserved_dialogues": 2,
                    "adaptation_mode": detail_level,
                    "omitted_reason": "由 AI 根据详细度控制省略。",
                },
            },
            "characters": _global_response()["characters"],
            "locations": _global_response()["locations"],
            "organizations": [],
            "chapters": [
                {
                    "id": "ch_001",
                    "title": "第一章 雨夜",
                    "source_chapter_numbers": [1],
                    "summary": "林青追查线索。",
                    "scenes": [
                        {
                            "id": "sc_001_001",
                            "title": "客栈起疑",
                            "location_id": "loc_001",
                            "time": "夜晚",
                            "characters": ["char_001"],
                            "synopsis": "林青发现线索。",
                            "source_range": {"chapter": 1, "start_hint": "陈府尹反驳道", "end_hint": "进入南桥客栈"},
                            "stage_directions": ["众人进入客栈。"],
                            "dialogue": [
                                {
                                    "speaker_id": None,
                                    "speaker_name": "旁白",
                                    "line": "不能再拖。",
                                    "emotion": "tense",
                                    "line_type": "monologue",
                                }
                            ],
                        }
                    ],
                },
                {
                    "id": "ch_002",
                    "title": "第二章 追踪",
                    "source_chapter_numbers": [2],
                    "summary": "两人追踪线索。",
                    "scenes": [
                        {
                            "id": "sc_002_001",
                            "title": "街上追问",
                            "location_id": "loc_002",
                            "time": "未明确",
                            "characters": ["char_001", "char_002"],
                            "synopsis": "林青询问赵明。",
                            "source_range": {"chapter": 2, "start_hint": "林青说", "end_hint": "离开东市街"},
                            "stage_directions": [],
                            "dialogue": [
                                {
                                    "speaker_id": "char_001",
                                    "speaker_name": "林青",
                                    "line": "线索在哪里？",
                                    "emotion": "neutral",
                                    "line_type": "dialogue",
                                }
                            ],
                        }
                    ],
                },
                {
                    "id": "ch_003",
                    "title": "第三章 对质",
                    "source_chapter_numbers": [3],
                    "summary": "赵明追上目标。",
                    "scenes": [
                        {
                            "id": "sc_003_001",
                            "title": "后门喝止",
                            "location_id": "loc_002",
                            "time": "夜晚",
                            "characters": ["char_002"],
                            "synopsis": "赵明喝止黑衣男子。",
                            "source_range": {"chapter": 3, "start_hint": "夜晚", "end_hint": "离开后门"},
                            "stage_directions": ["黑衣男子离开。"],
                            "dialogue": [
                                {
                                    "speaker_id": "char_002",
                                    "speaker_name": "赵明",
                                    "line": "站住！",
                                    "emotion": "tense",
                                    "line_type": "dialogue",
                                }
                            ],
                        }
                    ],
                },
            ],
            "adaptation_notes": {"themes": [], "conflicts": [], "omissions": [], "template_rules": []},
        }
    }


def test_analysis_calls_ai_for_each_chapter_and_global_merge(monkeypatch):
    from app.services import llm as llm_service

    prompts = []

    def fake_call(prompt: str):
        prompts.append(prompt)
        if "当前章节文本" in prompt or "章节文本：" in prompt:
            assert "不要把动作词并入人物名" in prompt
            return _chapter_response("章节")
        if "全局实体合并" in prompt:
            return _global_response()
        raise AssertionError(prompt)

    monkeypatch.setattr(llm_service, "_require_llm_config", lambda: None)
    monkeypatch.setattr(llm_service, "_call_deepseek", fake_call)

    result = analyze_project(_project())

    assert result.provider == llm_service.settings.llm_provider
    assert len(result.content["chapter_analyses"]) == 3
    assert result.content["characters"][0]["name"] == "林青"
    assert any("全局实体合并" in prompt for prompt in prompts)


def test_generate_screenplay_uses_ai_output_and_validates_references(monkeypatch):
    from app.services import llm as llm_service

    def fake_call(prompt: str):
        assert "scene.characters 必须来自全局 characters 的 id" in prompt
        return _screenplay_response("detailed")

    monkeypatch.setattr(llm_service, "_require_llm_config", lambda: None)
    monkeypatch.setattr(llm_service, "_call_deepseek", fake_call)

    result = generate_screenplay(_project("detailed"), _global_response())

    assert result.content["script"]["metadata"]["adaptation_mode"] == "detailed"
    assert result.content["script"]["chapters"][1]["scenes"][0]["dialogue"][0]["speaker_id"] == "char_001"


def test_generate_screenplay_rejects_missing_speaker_reference(monkeypatch):
    from app.services import llm as llm_service

    broken = _screenplay_response()
    broken["script"]["chapters"][1]["scenes"][0]["dialogue"][0]["speaker_id"] = "char_999"

    monkeypatch.setattr(llm_service, "_require_llm_config", lambda: None)
    monkeypatch.setattr(llm_service, "_call_deepseek", lambda prompt: broken)

    with pytest.raises(AIParseError, match="AI 解析失败，请重试"):
        generate_screenplay(_project(), _global_response())


def test_missing_ai_config_does_not_generate_fake_results(monkeypatch):
    from app.services import llm as llm_service

    monkeypatch.setattr(llm_service.settings, "llm_api_key", "")

    with pytest.raises(AIParseError, match="AI 服务未配置，请检查 API Key 或模型配置"):
        analyze_project(_project())


def test_api_flow_import_analyze_view_and_generate_yaml(monkeypatch):
    from app.services import llm as llm_service
    import app.db.session as db_session

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def fake_call(prompt: str):
        if "章节文本：" in prompt:
            return _chapter_response("章节")
        if "全局实体合并" in prompt:
            return _global_response()
        if "请基于全局 characters" in prompt:
            return _screenplay_response("standard")
        raise AssertionError(prompt)

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(db_session, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(llm_service, "_require_llm_config", lambda: None)
    monkeypatch.setattr(llm_service, "_call_deepseek", fake_call)

    try:
        client = TestClient(app)
        source_text = "\n\n".join(
            [
                "第一章 雨夜\n陈府尹反驳道：“不妥。”林青心想：不能再拖。众人进入南桥客栈。",
                "第二章 追踪\n林青说：“线索在哪里？”赵明道：“在茶楼。”两人离开东市街。",
                "第三章 对质\n夜晚，赵明喝道：“站住！”黑衣男子离开后门。",
            ]
        )

        preview = client.post("/api/v1/import/preview", json={"title": "AI 解析测试小说", "author": "测试作者", "text": source_text})
        assert preview.status_code == 200
        chapters = preview.json()["chapters"]

        created = client.post("/api/v1/projects", json={"title": "AI 解析测试小说", "author": "测试作者", "chapters": chapters})
        assert created.status_code == 201
        project_id = created.json()["id"]

        analysis_job = client.post(f"/api/v1/projects/{project_id}/analysis-jobs")
        assert analysis_job.status_code == 202
        analysis_payload = client.get(f"/api/v1/projects/{project_id}/analysis")
        assert analysis_payload.status_code == 200
        assert analysis_payload.json()["analysis"]["characters"][0]["name"] == "林青"

        settings = client.post(f"/api/v1/projects/{project_id}/generation-settings", json={"detail_level": "standard"})
        assert settings.status_code == 200

        script_job = client.post(f"/api/v1/projects/{project_id}/script-jobs")
        assert script_job.status_code == 202
        script = client.get(f"/api/v1/projects/{project_id}/script")
        assert script.status_code == 200
        assert "林青" in script.json()["yaml"]
    finally:
        app.dependency_overrides.clear()

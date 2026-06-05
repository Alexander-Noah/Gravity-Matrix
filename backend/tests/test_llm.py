from types import SimpleNamespace

from app.models.project import Chapter, Project
from app.services import llm


def _project() -> Project:
    project = Project(id=1, title="三国演义", author="罗贯中")
    project.chapters = [
        Chapter(number=1, title="桃园起义", content="刘备、关羽、张飞在乱世中相识。"),
        Chapter(number=2, title="桃园结义", content="三人焚香再拜，约定同心协力。"),
        Chapter(number=3, title="初战黄巾", content="刘备率兄弟投身战阵。"),
    ]
    return project


def _settings(monkeypatch, api_key: str = "", base_url: str = "", model: str = "") -> None:
    monkeypatch.setattr(llm.settings, "llm_provider", "deepseek")
    monkeypatch.setattr(llm.settings, "llm_api_key", api_key)
    monkeypatch.setattr(llm.settings, "llm_base_url", base_url)
    monkeypatch.setattr(llm.settings, "llm_model", model)


def test_analyze_project_uses_demo_without_llm_config(monkeypatch) -> None:
    _settings(monkeypatch)

    result = llm.analyze_project(_project())

    assert result.provider == "deterministic_demo"
    assert result.fallback_reason == "missing_config"
    assert result.content["chapter_summaries"][0]["title"] == "桃园起义"
    assert len(result.content["characters"]) >= 2
    assert result.content["characters"][0]["name"] == "刘备"


def test_analyze_project_uses_deepseek_when_configured(monkeypatch) -> None:
    _settings(monkeypatch, api_key="test-key", base_url="https://api.deepseek.com", model="deepseek-v4-flash")
    monkeypatch.setattr(
        llm,
        "_call_deepseek",
        lambda prompt: {
            "characters": [
                {
                    "id": "char_001",
                    "name": "刘备",
                    "role": "主角",
                    "gender": "male",
                    "age": None,
                    "description": "仁德之人。",
                }
            ],
            "locations": [{"id": "loc_001", "name": "桃园", "description": "结义地点。"}],
            "chapter_summaries": [{"chapter_number": 1, "title": "桃园起义", "summary": "群雄初起。"}],
            "themes": ["结义"],
            "conflicts": ["乱世与理想的冲突"],
        },
    )

    result = llm.analyze_project(_project())

    assert result.provider == "deepseek"
    assert result.fallback_reason is None
    assert result.content["characters"][0]["name"] == "刘备"


def test_generate_screenplay_falls_back_when_model_output_is_invalid(monkeypatch) -> None:
    _settings(monkeypatch, api_key="test-key", base_url="https://api.deepseek.com", model="deepseek-v4-flash")
    monkeypatch.setattr(llm, "_call_deepseek", lambda prompt: {"bad": "shape"})

    result = llm.generate_screenplay(_project())

    assert result.provider == "deterministic_demo"
    assert result.fallback_reason == "invalid_screenplay_response"
    assert result.content["script"]["metadata"]["title"] == "三国演义"
    scene = result.content["script"]["chapters"][0]["scenes"][0]
    assert len(result.content["script"]["characters"]) >= 2
    assert len(scene["dialogue"]) >= 2
    assert {line["speaker_id"] for line in scene["dialogue"]}.issubset(set(scene["characters"]))


def test_analyze_project_normalizes_unknown_character_age(monkeypatch) -> None:
    _settings(monkeypatch, api_key="test-key", base_url="https://api.deepseek.com", model="deepseek-v4-flash")
    monkeypatch.setattr(
        llm,
        "_call_deepseek",
        lambda prompt: {
            "characters": [
                {
                    "id": "char_001",
                    "name": "刘备",
                    "role": "主角",
                    "gender": "male",
                    "age": "未知",
                    "description": "仁德之人。",
                }
            ],
            "locations": [{"id": "loc_001", "name": "桃园", "description": "结义地点。"}],
            "chapter_summaries": [{"chapter_number": 1, "title": "桃园起义", "summary": "群雄初起。"}],
            "themes": ["结义"],
            "conflicts": ["乱世与理想的冲突"],
        },
    )

    result = llm.analyze_project(_project())

    assert result.content["characters"][0]["age"] is None


def test_analyze_project_records_fallback_reason_for_invalid_model_output(monkeypatch) -> None:
    _settings(monkeypatch, api_key="test-key", base_url="https://api.deepseek.com", model="deepseek-v4-flash")
    monkeypatch.setattr(llm, "_call_deepseek", lambda prompt: {"bad": "shape"})

    result = llm.analyze_project(_project())

    assert result.provider == "deterministic_demo"
    assert result.fallback_reason == "invalid_analysis_response"


def test_call_deepseek_parses_json_object(monkeypatch) -> None:
    _settings(monkeypatch, api_key="test-key", base_url="https://api.deepseek.com", model="deepseek-v4-flash")

    class FakeCompletions:
        def create(self, **kwargs):
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content='{"characters": [], "locations": []}')
                    )
                ]
            )

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr(llm, "OpenAI", FakeOpenAI)

    assert llm._call_deepseek("prompt") == {"characters": [], "locations": []}

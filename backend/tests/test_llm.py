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


def test_generate_screenplay_rejects_schema_valid_but_wrong_project_chapters(monkeypatch) -> None:
    _settings(monkeypatch, api_key="test-key", base_url="https://api.deepseek.com", model="deepseek-v4-flash")
    monkeypatch.setattr(
        llm,
        "_call_deepseek",
        lambda prompt: {
            "script": {
                "schema_version": "1.0",
                "metadata": {
                    "title": "错误小说",
                    "original_novel": "错误小说",
                    "author": "模型",
                    "language": "zh-CN",
                    "target_format": "screenplay",
                    "total_chapters": 3,
                },
                "characters": [
                    {
                        "id": "char_001",
                        "name": "陌生人",
                        "role": "主角",
                        "gender": "unknown",
                        "age": None,
                        "description": "不是当前小说的人物。",
                    },
                    {
                        "id": "char_002",
                        "name": "旁观者",
                        "role": "配角",
                        "gender": "unknown",
                        "age": None,
                        "description": "不是当前小说的人物。",
                    },
                ],
                "locations": [{"id": "loc_001", "name": "陌生城市", "description": "不是当前小说的地点。"}],
                "chapters": [
                    {
                        "id": "ch_001",
                        "title": "错误章节",
                        "source_chapter_numbers": [1, 2],
                        "summary": "这是结构合法但来源章节错误的内容。",
                        "scenes": [
                            {
                                "id": "sc_001_001",
                                "title": "错误场景",
                                "location_id": "loc_001",
                                "time": "day",
                                "characters": ["char_001", "char_002"],
                                "synopsis": "这是结构合法但不对应当前小说章节的场景。",
                                "stage_directions": ["陌生人站在陌生城市。"],
                                "dialogue": [
                                    {
                                        "speaker_id": "char_001",
                                        "speaker_name": "陌生人",
                                        "line": "这不是当前导入的小说。",
                                        "emotion": "calm",
                                    },
                                    {
                                        "speaker_id": "char_002",
                                        "speaker_name": "旁观者",
                                        "line": "应该触发后端兜底。",
                                        "emotion": "neutral",
                                    },
                                ],
                            }
                        ],
                    },
                    {
                        "id": "ch_002",
                        "title": "错误章节二",
                        "source_chapter_numbers": [2],
                        "summary": "第二个错误章节。",
                        "scenes": [
                            {
                                "id": "sc_002_001",
                                "title": "错误场景二",
                                "location_id": "loc_001",
                                "time": "day",
                                "characters": ["char_001", "char_002"],
                                "synopsis": "第二个错误场景。",
                                "stage_directions": ["旁观者停下。"],
                                "dialogue": [
                                    {
                                        "speaker_id": "char_001",
                                        "speaker_name": "陌生人",
                                        "line": "章节来源还是不对。",
                                        "emotion": "calm",
                                    },
                                    {
                                        "speaker_id": "char_002",
                                        "speaker_name": "旁观者",
                                        "line": "继续兜底。",
                                        "emotion": "neutral",
                                    },
                                ],
                            }
                        ],
                    },
                    {
                        "id": "ch_003",
                        "title": "错误章节三",
                        "source_chapter_numbers": [3],
                        "summary": "第三个错误章节。",
                        "scenes": [
                            {
                                "id": "sc_003_001",
                                "title": "错误场景三",
                                "location_id": "loc_001",
                                "time": "day",
                                "characters": ["char_001", "char_002"],
                                "synopsis": "第三个错误场景。",
                                "stage_directions": ["灯光暗下。"],
                                "dialogue": [
                                    {
                                        "speaker_id": "char_001",
                                        "speaker_name": "陌生人",
                                        "line": "这个 JSON Schema 合法。",
                                        "emotion": "calm",
                                    },
                                    {
                                        "speaker_id": "char_002",
                                        "speaker_name": "旁观者",
                                        "line": "但不该被接受。",
                                        "emotion": "neutral",
                                    },
                                ],
                            }
                        ],
                    },
                ],
                "adaptation_notes": {
                    "themes": ["错误主题"],
                    "conflicts": ["错误冲突"],
                    "omissions": ["错误省略"],
                },
            }
        },
    )

    result = llm.generate_screenplay(_project())

    assert result.provider == "deterministic_demo"
    assert result.fallback_reason == "invalid_screenplay_response"
    assert result.content["script"]["metadata"]["title"] == "三国演义"
    assert [chapter["source_chapter_numbers"] for chapter in result.content["script"]["chapters"]] == [[1], [2], [3]]


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


def test_demo_analysis_extracts_spaced_character_names(monkeypatch) -> None:
    _settings(monkeypatch)
    project = Project(id=2, title="测试长篇001：武侠之断裂玉牌", author="合成作者001")
    chapter_text = (
        "流萤车站 的风在夜色里慢慢压低，魏北辰 握着断裂玉牌，听见远处传来断续的钟声。"
        "秦知 说，事情不会只停在表面。温微 没有立刻回答，只把断裂玉牌 推到桌边。"
        "沈珩 从阴影里看着他们。"
    )
    project.chapters = [
        Chapter(number=1, title="第1章 长明城 的旧照片", content=chapter_text),
        Chapter(number=2, title="第2章 镜湖 的旧照片", content=chapter_text),
        Chapter(number=3, title="第3章 白塔 的旧戏票", content=chapter_text),
    ]

    result = llm.analyze_project(project)

    names = [character["name"] for character in result.content["characters"]]
    assert names[:4] == ["魏北辰", "秦知", "温微", "沈珩"]
    assert "的风" not in names
    assert "只停" not in names


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


def test_brief_prefers_sentence_boundary() -> None:
    text = "第一句完整。第二句也完整。第三句会被截断在后面。"

    assert llm._brief(text, 16) == "第一句完整。第二句也完整。..."


def test_brief_falls_back_to_character_limit_without_sentence_boundary() -> None:
    text = "没有明显断点的一长串内容"

    assert llm._brief(text, 8) == "没有明显断点的..."

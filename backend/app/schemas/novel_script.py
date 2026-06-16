from typing import Literal

from pydantic import BaseModel, Field, field_validator


ContentType = Literal["dialogue", "action", "narration", "inner_voice"]


class NovelCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)


class NovelCreateResponse(BaseModel):
    novel_id: int
    title: str
    chapter_count: int


class CharacterRead(BaseModel):
    id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    role: str = ""
    description: str = ""
    is_confirmed: bool = False


class CharactersResponse(BaseModel):
    characters: list[CharacterRead]


class CharactersSaveRequest(BaseModel):
    characters: list[CharacterRead]


class SceneRead(BaseModel):
    id: str
    chapter: str
    title: str
    location: str = ""
    time: str = ""
    atmosphere: str = ""
    characters: list[str] = Field(default_factory=list)
    summary: str = ""
    source_text: str


class ScenesResponse(BaseModel):
    scenes: list[SceneRead]


class ScenesSaveRequest(BaseModel):
    scenes: list[SceneRead]


class SceneContentRead(BaseModel):
    type: ContentType
    actor: str | None = None
    speaker: str | None = None
    emotion: str | None = None
    text: str
    source_text: str
    confidence: float = Field(..., ge=0, le=1)
    need_review: bool

    @field_validator("speaker")
    @classmethod
    def dialogue_speaker_can_be_unknown(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip() or "unknown"


class SceneContentResponse(BaseModel):
    content: list[SceneContentRead]


class SceneContentSaveRequest(BaseModel):
    content: list[SceneContentRead]


class YamlResponse(BaseModel):
    yaml: str
    script_id: int | None = None


class ScriptYamlSaveRequest(BaseModel):
    yaml: str = Field(..., min_length=1)


class ScriptYamlSaveResponse(BaseModel):
    script_id: int
    yaml: str

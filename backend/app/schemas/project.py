from pydantic import BaseModel, Field
from typing import Any


class ChapterCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    author: str | None = Field(default=None, max_length=255)
    chapters: list[ChapterCreate]


class ChapterRead(BaseModel):
    id: int
    number: int
    title: str
    content: str

    model_config = {"from_attributes": True}


class ProjectRead(BaseModel):
    id: int
    title: str
    author: str | None
    status: str
    chapter_count: int
    has_analysis: bool
    has_script: bool


class ProjectDetail(ProjectRead):
    chapters: list[ChapterRead]


class JobRead(BaseModel):
    id: int
    project_id: int
    type: str
    status: str
    progress: int
    current_step: str
    result_id: int | None
    error_message: str | None

    model_config = {"from_attributes": True}


class ScriptRead(BaseModel):
    project_id: int
    yaml: str


class AnalysisRead(BaseModel):
    project_id: int
    analysis: dict[str, Any]


class ScriptValidateRequest(BaseModel):
    yaml: str = Field(min_length=1)


class ScriptValidateResponse(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)

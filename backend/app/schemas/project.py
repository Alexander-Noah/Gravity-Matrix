from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any

from app.core.config import settings


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
    created_at: datetime
    updated_at: datetime


class ProjectListRead(BaseModel):
    items: list[ProjectRead]
    total: int
    limit: int
    offset: int


class ProjectReadinessRead(BaseModel):
    project_id: int
    can_analyze: bool
    can_generate_script: bool
    can_export: bool
    missing_steps: list[str] = Field(default_factory=list)
    next_action: str


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
    yaml: str = Field(min_length=1, max_length=settings.max_script_yaml_chars)


class ScriptValidateResponse(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)


class ScriptDiagnosisSummary(BaseModel):
    chapter_count: int
    scene_count: int
    character_count: int
    location_count: int
    dialogue_count: int
    issue_count: int
    warning_count: int
    suggestion_count: int


class ScriptDiagnosisFinding(BaseModel):
    code: str
    severity: str
    category: str
    path: str
    message: str
    recommendation: str


class ScriptDiagnosisResponse(BaseModel):
    project_id: int
    source: str
    valid_schema: bool
    score: int
    grade: str
    summary: ScriptDiagnosisSummary
    strengths: list[str] = Field(default_factory=list)
    findings: list[ScriptDiagnosisFinding] = Field(default_factory=list)


class WorkbenchWorkflowStep(BaseModel):
    number: str
    title: str
    description: str
    status: str


class WorkbenchStage(BaseModel):
    label: str
    status: str
    note: str


class WorkbenchProgress(BaseModel):
    percent: int
    stages: list[WorkbenchStage]


class WorkbenchAnalysis(BaseModel):
    raw: dict[str, Any] | None
    overview: dict[str, Any]


class WorkbenchScriptScene(BaseModel):
    id: str
    title: str
    label: str
    active: bool
    location_id: str
    time: str


class WorkbenchScriptChapter(BaseModel):
    id: str
    title: str
    label: str
    open: bool
    scenes: list[WorkbenchScriptScene]


class WorkbenchScript(BaseModel):
    yaml: str | None
    structure: list[WorkbenchScriptChapter]
    diagnosis: ScriptDiagnosisResponse | None


class ProjectWorkbenchRead(BaseModel):
    project: ProjectRead
    workflow_steps: list[WorkbenchWorkflowStep]
    progress: WorkbenchProgress
    analysis: WorkbenchAnalysis
    script: WorkbenchScript

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


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    author: str | None = Field(default=None, max_length=255)


class ImportPreviewRequest(BaseModel):
    text: str = Field(min_length=1)
    title: str | None = Field(default=None, max_length=255)
    author: str | None = Field(default=None, max_length=255)


class ImportPreviewChapter(BaseModel):
    number: int
    title: str
    content: str
    char_count: int
    excerpt: str


class ImportPreviewIssue(BaseModel):
    code: str
    severity: str
    message: str


class ImportPreprocessResult(BaseModel):
    characters: list[dict[str, Any]] = Field(default_factory=list)
    locations: list[dict[str, Any]] = Field(default_factory=list)
    chapter_summaries: list[dict[str, Any]] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    preparation_notes: list[str] = Field(default_factory=list)


class ImportPreviewResponse(BaseModel):
    title: str
    author: str | None
    chapter_count: int
    total_chars: int
    can_create_project: bool
    issues: list[ImportPreviewIssue]
    chapters: list[ImportPreviewChapter]
    preprocess: ImportPreprocessResult


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


class RecycleBinProjectRead(ProjectRead):
    deleted_at: datetime


class RecycleBinRead(BaseModel):
    items: list[RecycleBinProjectRead]
    total: int


class DashboardStat(BaseModel):
    label: str
    value: str
    note: str
    tone: str


class DashboardProjectCard(BaseModel):
    id: int
    title: str
    type: str
    status: str
    progress: int
    updatedAt: str
    chapters: int
    scenes: int
    owner: str
    nextAction: str


class DashboardActivity(BaseModel):
    title: str
    time: str
    status: str


class ProjectsDashboardRead(BaseModel):
    stats: list[DashboardStat]
    project_cards: list[DashboardProjectCard]
    activities: list[DashboardActivity]


class ScriptLibraryItem(BaseModel):
    id: str
    project_id: int | None = None
    source_id: str | None = None
    source_type: str = "project"
    title: str
    sourceNovel: str
    type: str
    chapters: int
    scenes: int
    dialogues: int
    schemaStatus: str
    status: str
    updatedAt: str
    tags: list[str]
    summary: str | None = None


class ScriptLibraryRead(BaseModel):
    stats: list[DashboardStat]
    items: list[ScriptLibraryItem]


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


class ParseTaskCreateRequest(BaseModel):
    source_text: str | None = Field(default=None, min_length=1)
    source_file_id: str | None = Field(default=None, max_length=255)
    project_id: int | None = None


class ParseTaskCreateResponse(BaseModel):
    task_id: str


class ParseTaskRead(BaseModel):
    task_id: str
    status: str
    progress: int
    message: str
    error: str | None = None


class ParseTaskResultRead(BaseModel):
    task_id: str
    result_json: dict[str, Any] | None = None
    result_yaml: str | None = None


class ScriptRead(BaseModel):
    project_id: int
    yaml: str


class ProjectDeleteResponse(BaseModel):
    deleted: bool
    project_id: int


class RecycleBinClearResponse(BaseModel):
    deleted: int


class TemplateRead(BaseModel):
    id: str
    name: str
    scenario: str
    target_format: str
    backend_rules: list[str] = Field(default_factory=list)
    features: list[str]
    fields: list[str]
    yamlExample: list[str]


class TemplateDefaultRequest(BaseModel):
    templateId: str = Field(min_length=1, max_length=80)


class TemplateDefaultResponse(BaseModel):
    templateId: str
    template: TemplateRead


class GenerationSettingsRequest(BaseModel):
    templateId: str | None = Field(default=None, max_length=80)
    scriptType: str | None = None
    adaptationStyle: str | None = None
    detail_level: str = Field(default="standard", pattern="^(brief|standard|detailed)$")
    contentOptions: list[str] = Field(default_factory=list)


class GenerationSettingsResponse(BaseModel):
    project_id: int
    accepted: bool
    settings: GenerationSettingsRequest


class SceneCreateRequest(BaseModel):
    chapterTitle: str = Field(min_length=1, max_length=255)
    sceneTitle: str = Field(min_length=1, max_length=255)
    location: str = Field(min_length=1, max_length=255)
    time: str = Field(min_length=1, max_length=255)
    characters: str | None = Field(default=None, max_length=1000)
    action: str | None = Field(default=None, max_length=5000)


class SceneCreateResponse(BaseModel):
    project_id: int
    yaml: str
    scene_id: str


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

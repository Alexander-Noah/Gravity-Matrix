from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.project import Chapter, Job, JobType, Project
from app.schemas.project import (
    JobRead,
    ProjectCreate,
    ProjectDetail,
    ProjectRead,
    ScriptRead,
    ScriptValidateRequest,
    ScriptValidateResponse,
)
from app.services.jobs import create_job, run_analysis_job, run_script_generation_job
from app.services.screenplay_yaml import validate_screenplay_yaml

router = APIRouter(tags=["projects"])


@router.post("/projects", response_model=ProjectRead, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> ProjectRead:
    if len(payload.chapters) < settings.min_chapters:
        raise HTTPException(status_code=422, detail=f"小说至少需要 {settings.min_chapters} 个章节。")

    if len(payload.chapters) > settings.max_chapters:
        raise HTTPException(status_code=422, detail=f"小说最多支持 {settings.max_chapters} 个章节。")

    for chapter in payload.chapters:
        if len(chapter.content) > settings.max_chapter_chars:
            raise HTTPException(
                status_code=422,
                detail=f"单章内容最多支持 {settings.max_chapter_chars} 个字符。",
            )

    project = Project(title=payload.title, author=payload.author)
    db.add(project)
    db.flush()

    for index, chapter_payload in enumerate(payload.chapters, start=1):
        db.add(
            Chapter(
                project_id=project.id,
                number=index,
                title=chapter_payload.title,
                content=chapter_payload.content,
            )
        )

    db.commit()
    db.refresh(project)
    return _project_to_read(project)


@router.get("/projects/{project_id}", response_model=ProjectDetail)
def get_project(project_id: int, db: Session = Depends(get_db)) -> ProjectDetail:
    project = _require_project(db, project_id)
    base = _project_to_read(project).model_dump()
    return ProjectDetail(**base, chapters=project.chapters)


@router.post("/projects/{project_id}/analysis-jobs", response_model=JobRead, status_code=202)
def start_analysis_job(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Job:
    _require_project(db, project_id)
    job = create_job(db, project_id, JobType.analysis)
    background_tasks.add_task(_run_analysis_job_task, job.id)
    return job


@router.post("/projects/{project_id}/script-jobs", response_model=JobRead, status_code=202)
def start_script_job(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Job:
    _require_project(db, project_id)
    job = create_job(db, project_id, JobType.script_generation)
    background_tasks.add_task(_run_script_generation_job_task, job.id)
    return job


@router.get("/jobs/{job_id}", response_model=JobRead)
def get_job(job_id: int, db: Session = Depends(get_db)) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="任务不存在。")
    return job


@router.get("/projects/{project_id}/script", response_model=ScriptRead)
def get_script(project_id: int, db: Session = Depends(get_db)) -> ScriptRead:
    project = _require_project(db, project_id)
    if not project.script_yaml:
        raise HTTPException(status_code=404, detail="当前项目还没有生成剧本。")
    return ScriptRead(project_id=project.id, yaml=project.script_yaml)


@router.post("/projects/{project_id}/script/validate", response_model=ScriptValidateResponse)
def validate_script(
    project_id: int,
    payload: ScriptValidateRequest,
    db: Session = Depends(get_db),
) -> ScriptValidateResponse:
    _require_project(db, project_id)
    valid, errors = validate_screenplay_yaml(payload.yaml)
    return ScriptValidateResponse(valid=valid, errors=errors)


@router.get("/projects/{project_id}/script/export")
def export_script(project_id: int, db: Session = Depends(get_db)) -> Response:
    project = _require_project(db, project_id)
    if not project.script_yaml:
        raise HTTPException(status_code=404, detail="当前项目还没有生成剧本。")

    filename = f"project-{project.id}-screenplay.yaml"
    return Response(
        content=project.script_yaml,
        media_type="application/x-yaml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _project_to_read(project: Project) -> ProjectRead:
    return ProjectRead(
        id=project.id,
        title=project.title,
        author=project.author,
        status=project.status,
        chapter_count=len(project.chapters),
        has_analysis=project.analysis_json is not None,
        has_script=project.script_yaml is not None,
    )


def _require_project(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在。")
    return project


def _run_analysis_job_task(job_id: int) -> None:
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        run_analysis_job(db, job_id)


def _run_script_generation_job_task(job_id: int) -> None:
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        run_script_generation_job(db, job_id)

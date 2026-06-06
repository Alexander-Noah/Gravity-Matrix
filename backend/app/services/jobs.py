import json
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.project import Job, JobStatus, JobType, Project
from app.services.llm import analyze_project, generate_screenplay
from app.services.screenplay_yaml import dump_screenplay_yaml


def run_analysis_job(db: Session, job_id: int) -> None:
    job = db.get(Job, job_id)
    if job is None:
        return

    try:
        _mark_running(db, job, "正在读取小说章节", 10)
        project = _get_project(db, job.project_id)

        _mark_running(db, job, "正在分析人物、场景和冲突", 45)
        result = analyze_project(project)

        _mark_running(db, job, "正在整理 AI 解析结果", 85)
        project.analysis_json = json.dumps(result.content, ensure_ascii=False)
        project.status = "analysis_completed"
        _mark_succeeded(db, job, "AI 解析完成", 100, project.id)
    except Exception as exc:  # pragma: no cover - defensive boundary for background tasks
        _mark_failed(db, job, str(exc))


def run_script_generation_job(db: Session, job_id: int) -> None:
    job = db.get(Job, job_id)
    if job is None:
        return

    try:
        _mark_running(db, job, "正在读取项目上下文", 10)
        project = _get_project(db, job.project_id)

        _mark_running(db, job, "正在整理章节结构", 30)
        analysis = json.loads(project.analysis_json) if project.analysis_json else None

        _mark_running(db, job, "正在生成场景和对白", 65)
        result = generate_screenplay(project, analysis)

        _mark_running(db, job, "正在校验并保存剧本 YAML", 90)
        project.script_yaml = dump_screenplay_yaml(result.content)
        project.status = "script_completed"
        _mark_succeeded(db, job, "剧本生成完成", 100, project.id)
    except Exception as exc:  # pragma: no cover - defensive boundary for background tasks
        _mark_failed(db, job, str(exc))


def _get_project(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise ValueError("项目不存在。")
    return project


def _mark_running(db: Session, job: Job, step: str, progress: int) -> None:
    job.status = JobStatus.running.value
    job.current_step = step
    job.progress = progress
    db.commit()


def _mark_succeeded(db: Session, job: Job, step: str, progress: int, result_id: int) -> None:
    job.status = JobStatus.succeeded.value
    job.current_step = step
    job.progress = progress
    job.result_id = result_id
    db.commit()


def _mark_failed(db: Session, job: Job, message: str) -> None:
    job.status = JobStatus.failed.value
    job.current_step = "任务失败"
    job.error_message = message
    db.commit()


def create_job(db: Session, project_id: int, job_type: JobType) -> Job:
    job = Job(project_id=project_id, type=job_type.value)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_active_job(db: Session, project_id: int, job_type: JobType) -> Job | None:
    job = (
        db.query(Job)
        .filter(
            Job.project_id == project_id,
            Job.type == job_type.value,
            Job.status.in_([JobStatus.queued.value, JobStatus.running.value]),
        )
        .order_by(Job.created_at.desc(), Job.id.desc())
        .first()
    )
    if job is not None and _is_stale_active_job(job):
        job.status = JobStatus.failed.value
        job.current_step = "任务已超时"
        job.error_message = "任务长时间没有更新，已自动结束。请重新启动任务。"
        db.commit()
        return None

    return job


def cancel_active_jobs(db: Session, project_id: int, job_type: JobType, reason: str) -> None:
    jobs = (
        db.query(Job)
        .filter(
            Job.project_id == project_id,
            Job.type == job_type.value,
            Job.status.in_([JobStatus.queued.value, JobStatus.running.value]),
        )
        .all()
    )
    for job in jobs:
        job.status = JobStatus.failed.value
        job.current_step = "任务已取消"
        job.error_message = reason
    db.commit()


def _is_stale_active_job(job: Job) -> bool:
    updated_at = job.updated_at
    if updated_at is None:
        return False
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - updated_at > timedelta(minutes=10)

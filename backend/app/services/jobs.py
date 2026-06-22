import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.project import Job, JobStatus, JobType, Project
from app.services import llm as llm_service
from app.services.llm import analyze_project, generate_screenplay
from app.services.screenplay_yaml import dump_screenplay_yaml

logger = logging.getLogger(__name__)


def run_analysis_job(db: Session, job_id: int) -> None:
    llm_service.clear_last_llm_raw_response()
    job = db.get(Job, job_id)
    if job is None:
        return

    try:
        with llm_service.llm_config_context(_job_llm_config(job)):
            _mark_running(db, job, "正在读取小说章节", 10)
            project = _get_project(db, job.project_id)
            text_chars = sum(len(chapter.content or "") for chapter in project.chapters)
            logger.info(
                "analysis_job input project_id=%s text_chars=%s chapters=%s real_ai=%s mock_fallback=%s",
                project.id,
                text_chars,
                len(project.chapters),
                True,
                False,
            )

            _mark_running(db, job, "正在请求 AI 解析整本小说", 35)
            result = analyze_project(project)

            if result.fallback_reason:
                _mark_running(db, job, "AI 返回较慢，已切换本地快速解析", 70)
            else:
                _mark_running(db, job, "正在整理 AI 解析结果", 85)
            project.analysis_json = json.dumps(result.content, ensure_ascii=False)
            project.status = "analysis_completed"
            scene_count = sum(
                len(item.get("analysis", {}).get("events", []) or [])
                for item in result.content.get("chapter_analyses", []) or []
                if isinstance(item, dict)
            )
            logger.info(
                "analysis_job output project_id=%s characters=%s scenes=%s mock_fallback=%s",
                project.id,
                len(result.content.get("characters", []) or []),
                scene_count,
                False,
            )
            _mark_succeeded(db, job, "AI 解析完成", 100, project.id)
    except Exception as exc:  # pragma: no cover - defensive boundary for background tasks
        raw_response = llm_service.get_last_llm_raw_response()
        if raw_response:
            print(f"Analysis job failed raw/error first 4000 chars:\n{raw_response[:4000]}", flush=True)
        print(f"Analysis job failed: {exc}", flush=True)
        _mark_failed(db, job, str(exc))


def run_script_generation_job(db: Session, job_id: int) -> None:
    llm_service.clear_last_llm_raw_response()
    job = db.get(Job, job_id)
    if job is None:
        return

    try:
        with llm_service.llm_config_context(_job_llm_config(job)):
            _mark_running(db, job, "正在读取项目上下文", 10)
            project = _get_project(db, job.project_id)

            _mark_running(db, job, "正在整理章节结构", 30)
            analysis = json.loads(project.analysis_json) if project.analysis_json else None
            if analysis is None:
                raise ValueError("请先完成第 2 步 AI 解析，再生成剧本 YAML。")

            _mark_running(db, job, "正在准备剧本生成", 40)
            logger.info(
                "script_job input project_id=%s analysis_characters=%s analysis_locations=%s real_ai=%s mock_fallback=%s",
                project.id,
                len(analysis.get("characters", []) or []),
                len(analysis.get("locations", []) or []),
                True,
                False,
            )
            def update_script_progress(step: str, progress: int) -> None:
                _mark_running(db, job, step, progress)

            result = generate_screenplay(project, analysis, progress_callback=update_script_progress)

            _mark_running(db, job, "正在校验并保存剧本 YAML", 90)
            project.script_yaml = dump_screenplay_yaml(result.content)
            project.status = "script_completed"
            script = result.content.get("script", {}) if isinstance(result.content, dict) else {}
            scene_count = sum(len(chapter.get("scenes", []) or []) for chapter in script.get("chapters", []) or [])
            logger.info("script_job output project_id=%s scenes=%s mock_fallback=%s", project.id, scene_count, False)
            _mark_succeeded(db, job, "剧本生成完成", 100, project.id)
    except Exception as exc:  # pragma: no cover - defensive boundary for background tasks
        raw_response = llm_service.get_last_llm_raw_response()
        if raw_response:
            print(f"Script generation job failed raw/error first 4000 chars:\n{raw_response[:4000]}", flush=True)
        print(f"Script generation job failed: {exc}", flush=True)
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


def create_job(db: Session, project_id: int, job_type: JobType, llm_config: dict | None = None) -> Job:
    job = Job(
        project_id=project_id,
        type=job_type.value,
        llm_config_json=json.dumps(llm_config, ensure_ascii=False) if llm_config else None,
    )
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


def _job_llm_config(job: Job) -> dict | None:
    if not job.llm_config_json:
        return None
    try:
        parsed = json.loads(job.llm_config_json)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None

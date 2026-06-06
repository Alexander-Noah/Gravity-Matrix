import json
import re
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session
import yaml

from app.core.config import settings
from app.db.session import get_db
from app.models.project import Chapter, Job, JobType, Project, ProjectGenerationSettings
from app.schemas.project import (
    AnalysisRead,
    AnalysisRerunResponse,
    GenerationSettingsRead,
    JobRead,
    MessageResponse,
    ProjectCreate,
    ProjectDetail,
    ProjectListRead,
    ProjectReadinessRead,
    ProjectRead,
    ProjectUpdate,
    ProjectWorkbenchRead,
    ScriptDiagnosisResponse,
    ScriptRead,
    ScriptValidateRequest,
    ScriptValidateResponse,
)
from app.services.jobs import create_job, get_active_job, run_analysis_job, run_script_generation_job
from app.services.script_export import screenplay_yaml_to_markdown, screenplay_yaml_to_txt
from app.services.script_diagnosis import diagnose_screenplay_yaml
from app.services.screenplay_yaml import validate_screenplay_yaml
from app.services.workbench import build_project_workbench

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


@router.get("/projects", response_model=ProjectListRead)
def list_projects(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> ProjectListRead:
    total = db.query(func.count(Project.id)).scalar() or 0
    projects = (
        db.query(Project)
        .order_by(Project.updated_at.desc(), Project.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return ProjectListRead(
        items=[_project_to_read(project) for project in projects],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/import/preview")
def preview_import(payload: dict[str, Any]) -> dict[str, Any]:
    text = str(payload.get("text") or "")
    title = str(payload.get("title") or _detect_title(text) or "未命名小说")
    author = payload.get("author")
    chapters = _detect_chapters(text)
    return {
        "title": title,
        "author": author,
        "text_length": len(text),
        "chapter_count": len(chapters),
        "can_create_project": len(chapters) >= settings.min_chapters,
        "chapters": chapters,
        "issues": [] if len(chapters) >= settings.min_chapters else [
            {"severity": "error", "message": f"小说至少需要 {settings.min_chapters} 个章节。"}
        ],
    }


@router.get("/projects/dashboard")
def get_projects_dashboard(db: Session = Depends(get_db)) -> dict[str, Any]:
    projects = db.query(Project).order_by(Project.updated_at.desc(), Project.id.desc()).limit(20).all()
    total = db.query(func.count(Project.id)).scalar() or 0
    script_count = sum(1 for project in projects if project.script_yaml)
    editing_count = sum(1 for project in projects if project.status == "script_edited")
    pending_count = sum(1 for project in projects if not project.analysis_json)
    return {
        "stats": [
            {"label": "全部项目", "value": str(total), "note": "来自后端项目列表", "tone": "violet"},
            {"label": "编辑中", "value": str(editing_count), "note": "已保存剧本草稿", "tone": "blue"},
            {"label": "已生成剧本", "value": str(script_count), "note": "可继续编辑或导出", "tone": "mint"},
            {"label": "待解析", "value": str(pending_count), "note": "需要进入 AI 解析", "tone": "orange"},
        ],
        "cards": [_project_card(project) for project in projects],
        "activities": [
            {
                "title": f"{_project_next_action(project)}：{project.title}",
                "time": project.updated_at,
                "status": _project_status_label(project),
            }
            for project in projects[:4]
        ],
    }


@router.get("/scripts/library")
def get_scripts_library(db: Session = Depends(get_db)) -> dict[str, Any]:
    projects = (
        db.query(Project)
        .filter(Project.script_yaml.isnot(None))
        .order_by(Project.updated_at.desc(), Project.id.desc())
        .all()
    )
    items = [_script_library_item(project) for project in projects]
    editing_count = sum(1 for item in items if item["status"] == "编辑中")
    completed_count = sum(1 for item in items if item["status"] == "已完成")
    invalid_count = sum(1 for item in items if item["status"] == "校验异常")
    return {
        "stats": [
            {"label": "全部剧本", "value": str(len(items)), "note": "来自已生成剧本的项目", "tone": "violet"},
            {"label": "编辑中", "value": str(editing_count), "note": "可继续修改 YAML", "tone": "blue"},
            {"label": "已完成", "value": str(completed_count), "note": "Schema 校验通过", "tone": "mint"},
            {"label": "校验异常", "value": str(invalid_count), "note": "需要修正字段或引用", "tone": "orange"},
        ],
        "items": items,
    }


@router.get("/templates")
def get_templates() -> list[dict[str, Any]]:
    return [
        {
            "id": "film",
            "name": "影视剧剧本模板",
            "scenario": "适合长篇小说改编为电视剧、网剧或电影分场剧本。",
            "features": ["按章节拆分场景", "保留人物动机与动作描写", "适配标准场景标题"],
            "fields": ["script", "characters", "chapters", "scenes", "dialogue"],
            "yamlExample": [
                "script:",
                "  schema_version: '1.0'",
                "  metadata:",
                "    target_format: screenplay",
                "  characters:",
                "    - id: char_001",
                "      name: 人物名",
            ],
        },
        {
            "id": "short-drama",
            "name": "短剧剧本模板",
            "scenario": "适合高节奏短剧、竖屏剧和强钩子内容生成。",
            "features": ["强化开场冲突", "突出反转节点", "每集保留结尾钩子"],
            "fields": ["episode", "hook", "conflict", "turning_point", "dialogue"],
            "yamlExample": ["episode:", "  hook: 开场三秒冲突", "  beats:", "    - type: reversal"],
        },
        {
            "id": "stage-play",
            "name": "话剧剧本模板",
            "scenario": "适合将小说改编为舞台表演文本和排练稿。",
            "features": ["强调舞台调度", "保留幕与场结构", "补充人物入场退场"],
            "fields": ["act", "scene", "stage_directions", "characters", "dialogue"],
            "yamlExample": ["act:", "  title: 第一幕", "  scenes:", "    - stage_directions:"],
        },
    ]


@router.get("/projects/{project_id}", response_model=ProjectDetail)
def get_project(project_id: int, db: Session = Depends(get_db)) -> ProjectDetail:
    project = _require_project(db, project_id)
    base = _project_to_read(project).model_dump()
    return ProjectDetail(**base, chapters=project.chapters)


@router.patch("/projects/{project_id}", response_model=ProjectRead)
def update_project(project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db)) -> ProjectRead:
    project = _require_project(db, project_id)
    title = payload.title if payload.title is not None else payload.name
    if title is not None:
        title = title.strip()
        if not title:
            raise HTTPException(status_code=422, detail="项目名称不能为空。")
        project.title = title

    db.commit()
    db.refresh(project)
    return _project_to_read(project)


@router.delete("/projects/{project_id}", response_model=MessageResponse)
def delete_project(project_id: int, db: Session = Depends(get_db)) -> MessageResponse:
    project = _require_project(db, project_id)
    db.delete(project)
    db.commit()
    return MessageResponse(success=True, message="项目已删除。")


@router.post("/projects/{project_id}/clone", response_model=ProjectRead, status_code=201)
def clone_project(project_id: int, db: Session = Depends(get_db)) -> ProjectRead:
    project = _require_project(db, project_id)
    clone = Project(
        title=f"{project.title} 副本",
        author=project.author,
        status=project.status,
        analysis_json=project.analysis_json,
        script_yaml=project.script_yaml,
    )
    db.add(clone)
    db.flush()
    for chapter in project.chapters:
        db.add(
            Chapter(
                project_id=clone.id,
                number=chapter.number,
                title=chapter.title,
                content=chapter.content,
            )
        )
    if project.generation_settings:
        db.add(
            ProjectGenerationSettings(
                project_id=clone.id,
                settings_json=project.generation_settings.settings_json,
            )
        )
    db.commit()
    db.refresh(clone)
    return _project_to_read(clone)


@router.get("/projects/{project_id}/workbench", response_model=ProjectWorkbenchRead)
def get_project_workbench(project_id: int, db: Session = Depends(get_db)) -> ProjectWorkbenchRead:
    project = _require_project(db, project_id)
    return ProjectWorkbenchRead.model_validate(build_project_workbench(project))


@router.get("/projects/{project_id}/readiness", response_model=ProjectReadinessRead)
def get_project_readiness(project_id: int, db: Session = Depends(get_db)) -> ProjectReadinessRead:
    project = _require_project(db, project_id)
    return _project_readiness(project)


@router.post("/projects/{project_id}/generation-settings", response_model=GenerationSettingsRead)
def save_generation_settings(
    project_id: int,
    settings_payload: dict[str, Any],
    db: Session = Depends(get_db),
) -> GenerationSettingsRead:
    _require_project(db, project_id)
    settings_json = json.dumps(settings_payload, ensure_ascii=False)
    existing = db.get(ProjectGenerationSettings, project_id)
    if existing is None:
        db.add(ProjectGenerationSettings(project_id=project_id, settings_json=settings_json))
    else:
        existing.settings_json = settings_json

    db.commit()
    return GenerationSettingsRead(project_id=project_id, settings=settings_payload)


@router.post("/projects/{project_id}/analysis-jobs", response_model=JobRead, status_code=202)
def start_analysis_job(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Job:
    _require_project(db, project_id)
    active_job = get_active_job(db, project_id, JobType.analysis)
    if active_job is not None:
        return active_job

    job = create_job(db, project_id, JobType.analysis)
    background_tasks.add_task(_run_analysis_job_task, job.id)
    return job


@router.post("/projects/{project_id}/analysis-jobs/rerun", response_model=AnalysisRerunResponse, status_code=202)
def rerun_analysis_job(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> AnalysisRerunResponse:
    _require_project(db, project_id)
    job = create_job(db, project_id, JobType.analysis)
    background_tasks.add_task(_run_analysis_job_task, job.id)
    return AnalysisRerunResponse(id=job.id, job_id=job.id, status=job.status, message="重新解析任务已启动。")


@router.get("/projects/{project_id}/analysis", response_model=AnalysisRead)
def get_analysis(project_id: int, db: Session = Depends(get_db)) -> AnalysisRead:
    project = _require_project(db, project_id)
    if not project.analysis_json:
        raise HTTPException(status_code=404, detail="当前项目还没有 AI 分析结果。")

    return AnalysisRead(project_id=project.id, analysis=json.loads(project.analysis_json))


@router.post("/projects/{project_id}/script-jobs", response_model=JobRead, status_code=202)
def start_script_job(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Job:
    _require_project(db, project_id)
    active_job = get_active_job(db, project_id, JobType.script_generation)
    if active_job is not None:
        return active_job

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


@router.put("/projects/{project_id}/script", response_model=ScriptRead)
def save_script(
    project_id: int,
    payload: ScriptValidateRequest,
    db: Session = Depends(get_db),
) -> ScriptRead:
    project = _require_project(db, project_id)
    valid, errors = validate_screenplay_yaml(payload.yaml)
    if not valid:
        raise HTTPException(status_code=422, detail={"message": "剧本 YAML 校验失败。", "errors": errors})

    project.script_yaml = payload.yaml
    project.status = "script_edited"
    db.commit()
    db.refresh(project)
    return ScriptRead(project_id=project.id, yaml=project.script_yaml or "")


@router.post("/projects/{project_id}/script/validate", response_model=ScriptValidateResponse)
def validate_script(
    project_id: int,
    payload: ScriptValidateRequest,
    db: Session = Depends(get_db),
) -> ScriptValidateResponse:
    _require_project(db, project_id)
    valid, errors = validate_screenplay_yaml(payload.yaml)
    return ScriptValidateResponse(valid=valid, errors=errors)


@router.get("/projects/{project_id}/script/diagnosis", response_model=ScriptDiagnosisResponse)
def diagnose_stored_script(project_id: int, db: Session = Depends(get_db)) -> ScriptDiagnosisResponse:
    project = _require_project(db, project_id)
    if not project.script_yaml:
        raise HTTPException(status_code=404, detail="当前项目还没有生成剧本。")

    return ScriptDiagnosisResponse.model_validate(
        diagnose_screenplay_yaml(project.id, project.script_yaml, "stored_yaml")
    )


@router.post("/projects/{project_id}/script/diagnosis", response_model=ScriptDiagnosisResponse)
def diagnose_script_draft(
    project_id: int,
    payload: ScriptValidateRequest,
    db: Session = Depends(get_db),
) -> ScriptDiagnosisResponse:
    project = _require_project(db, project_id)
    return ScriptDiagnosisResponse.model_validate(
        diagnose_screenplay_yaml(project.id, payload.yaml, "request_yaml")
    )


@router.post("/projects/{project_id}/scenes", response_model=ScriptRead)
def add_project_scene(project_id: int, payload: dict[str, Any], db: Session = Depends(get_db)) -> ScriptRead:
    project = _require_project(db, project_id)
    if not project.script_yaml:
        raise HTTPException(status_code=404, detail="当前项目还没有生成剧本。")

    try:
        document = yaml.safe_load(project.script_yaml)
    except yaml.YAMLError as exc:
        raise HTTPException(status_code=422, detail="已保存剧本 YAML 无法解析。") from exc

    if not isinstance(document, dict) or not isinstance(document.get("script"), dict):
        raise HTTPException(status_code=422, detail="已保存剧本 YAML 结构不完整。")

    _append_scene_to_document(document, payload)
    yaml_text = yaml.safe_dump(document, allow_unicode=True, sort_keys=False)
    valid, errors = validate_screenplay_yaml(yaml_text)
    if not valid:
        raise HTTPException(status_code=422, detail={"message": "新增场景后 YAML 校验失败。", "errors": errors})

    project.script_yaml = yaml_text
    project.status = "script_edited"
    db.commit()
    db.refresh(project)
    return ScriptRead(project_id=project.id, yaml=project.script_yaml or "")


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


@router.get("/projects/{project_id}/script/export/markdown")
def export_script_markdown(project_id: int, db: Session = Depends(get_db)) -> Response:
    project = _require_project(db, project_id)
    if not project.script_yaml:
        raise HTTPException(status_code=404, detail="当前项目还没有生成剧本。")

    try:
        content = screenplay_yaml_to_markdown(project.script_yaml)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    filename = f"project-{project.id}-screenplay.md"
    return Response(
        content=content,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/projects/{project_id}/script/export/txt")
def export_script_txt(project_id: int, db: Session = Depends(get_db)) -> Response:
    project = _require_project(db, project_id)
    if not project.script_yaml:
        raise HTTPException(status_code=404, detail="当前项目还没有生成剧本。")

    try:
        content = screenplay_yaml_to_txt(project.script_yaml)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    filename = f"project-{project.id}-screenplay.txt"
    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
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
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def _project_readiness(project: Project) -> ProjectReadinessRead:
    has_script = project.script_yaml is not None
    has_analysis = project.analysis_json is not None or has_script
    missing_steps = []
    if not has_analysis:
        missing_steps.append("analysis")
    if not has_script:
        missing_steps.append("script")

    if not has_analysis:
        next_action = "start_analysis"
    elif not has_script:
        next_action = "generate_script"
    else:
        next_action = "export_script"

    return ProjectReadinessRead(
        project_id=project.id,
        can_analyze=True,
        can_generate_script=True,
        can_export=has_script,
        missing_steps=missing_steps,
        next_action=next_action,
    )


def _require_project(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在。")
    return project


def _detect_title(text: str) -> str | None:
    match = re.search(r"^\s*标题[:：]\s*(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def _detect_chapters(text: str) -> list[dict[str, Any]]:
    matches = list(
        re.finditer(
            r"(^|\n)\s*((?:第\s*[\d一二三四五六七八九十百千万零〇两]+\s*[章节回幕]|Chapter\s*\d+)(?:\s+[^\n。！？!?]+)?)[ \t]*(?=\n|$)",
            text,
            flags=re.IGNORECASE,
        )
    )
    chapters = []
    for index, match in enumerate(matches):
        title_start = match.start() + len(match.group(1))
        next_start = matches[index + 1].start() + len(matches[index + 1].group(1)) if index + 1 < len(matches) else len(text)
        chapter_text = text[title_start:next_start].strip()
        body = chapter_text.replace(match.group(2), "", 1).strip()
        content = body or chapter_text
        excerpt = re.sub(r"\s+", " ", content)[:46]
        chapters.append(
            {
                "number": index + 1,
                "title": match.group(2).strip(),
                "content": content,
                "excerpt": f"{excerpt}..." if excerpt else "等待补充正文",
            }
        )
    return chapters


def _project_status_label(project: Project) -> str:
    if project.status == "script_edited":
        return "编辑中"
    if project.script_yaml:
        return "待导出"
    if project.analysis_json:
        return "待生成"
    return "待解析"


def _project_progress(project: Project) -> int:
    if project.status == "script_edited":
        return 75
    if project.script_yaml:
        return 80
    if project.analysis_json:
        return 60
    return 30


def _project_next_action(project: Project) -> str:
    if project.script_yaml:
        return "继续编辑 YAML"
    if project.analysis_json:
        return "生成剧本"
    return "进入 AI 解析"


def _project_card(project: Project) -> dict[str, Any]:
    return {
        "id": project.id,
        "title": f"《{project.title}》改编项目",
        "type": "结构化剧本 / YAML" if project.script_yaml else "小说改编 / 工作台",
        "status": _project_status_label(project),
        "progress": _project_progress(project),
        "updatedAt": project.updated_at,
        "chapters": len(project.chapters),
        "scenes": _script_summary(project.script_yaml)["scene_count"] if project.script_yaml else 0,
        "owner": project.author or "创作者",
        "nextAction": _project_next_action(project),
        "raw": _project_to_read(project).model_dump(),
    }


def _script_summary(yaml_text: str | None) -> dict[str, int]:
    if not yaml_text:
        return {"chapter_count": 0, "scene_count": 0, "dialogue_count": 0}
    try:
        report = diagnose_screenplay_yaml(0, yaml_text, "summary")
    except Exception:
        return {"chapter_count": 0, "scene_count": 0, "dialogue_count": 0}
    summary = report.get("summary", {})
    return {
        "chapter_count": summary.get("chapter_count", 0),
        "scene_count": summary.get("scene_count", 0),
        "dialogue_count": summary.get("dialogue_count", 0),
    }


def _script_library_item(project: Project) -> dict[str, Any]:
    summary = _script_summary(project.script_yaml)
    diagnosis = diagnose_screenplay_yaml(project.id, project.script_yaml or "", "stored_yaml")
    status = "校验异常" if diagnosis["valid_schema"] is False else ("编辑中" if project.status == "script_edited" else "已完成")
    return {
        "id": f"project-{project.id}",
        "projectId": project.id,
        "title": f"《{project.title}》剧本",
        "sourceNovel": f"《{project.title}》",
        "type": "影视剧",
        "chapters": summary["chapter_count"],
        "scenes": summary["scene_count"],
        "dialogues": summary["dialogue_count"],
        "schemaStatus": "校验异常" if diagnosis["valid_schema"] is False else "校验通过",
        "status": status,
        "updatedAt": project.updated_at,
        "tags": [project.status, "已解析" if project.analysis_json else "待解析", "YAML"],
        "raw": _project_to_read(project).model_dump(),
    }


def _append_scene_to_document(document: dict[str, Any], payload: dict[str, Any]) -> None:
    script = document["script"]
    chapters = script.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        raise HTTPException(status_code=422, detail="已保存剧本缺少章节。")

    chapter_title = str(payload.get("chapterTitle") or "")
    chapter = next((item for item in chapters if item.get("title") == chapter_title), chapters[0])
    scenes = chapter.setdefault("scenes", [])
    if not isinstance(scenes, list):
        raise HTTPException(status_code=422, detail="目标章节 scenes 字段不是数组。")

    location_name = str(payload.get("location") or "未命名地点").strip()
    location_id = _ensure_location(script, location_name)
    character_ids = _ensure_characters(script, str(payload.get("characters") or ""))
    if not character_ids and script.get("characters"):
        character_ids = [script["characters"][0]["id"]]

    scene_index = len(scenes) + 1
    chapter_id = str(chapter.get("id") or f"ch_{chapters.index(chapter) + 1:03d}")
    scene_id = f"{chapter_id}_sc_{scene_index:03d}"
    action = str(payload.get("action") or "新增场景草稿，等待继续补充动作与对白。").strip()
    scenes.append(
        {
            "id": scene_id,
            "title": str(payload.get("sceneTitle") or f"新增场景 {scene_index}").strip(),
            "location_id": location_id,
            "time": str(payload.get("time") or "待定").strip(),
            "characters": character_ids,
            "synopsis": action,
            "stage_directions": [action],
            "dialogue": [],
        }
    )


def _ensure_location(script: dict[str, Any], name: str) -> str:
    locations = script.setdefault("locations", [])
    for location in locations:
        if location.get("name") == name:
            return str(location.get("id"))
    location_id = f"loc_{len(locations) + 1:03d}"
    locations.append({"id": location_id, "name": name, "description": f"作者新增场景地点：{name}。"})
    return location_id


def _ensure_characters(script: dict[str, Any], raw_names: str) -> list[str]:
    names = [name.strip() for name in re.split(r"[、,，\s]+", raw_names) if name.strip()]
    characters = script.setdefault("characters", [])
    ids = []
    for name in names:
        existing = next((character for character in characters if character.get("name") == name), None)
        if existing:
            ids.append(str(existing.get("id")))
            continue
        character_id = f"char_{len(characters) + 1:03d}"
        characters.append(
            {
                "id": character_id,
                "name": name,
                "role": "配角",
                "gender": "unknown",
                "age": None,
                "description": "作者新增场景中出现的人物。",
            }
        )
        ids.append(character_id)
    return list(dict.fromkeys(ids))


def _run_analysis_job_task(job_id: int) -> None:
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        run_analysis_job(db, job_id)


def _run_script_generation_job_task(job_id: int) -> None:
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        run_script_generation_job(db, job_id)

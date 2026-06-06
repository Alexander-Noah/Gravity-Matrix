import json

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.project import Chapter, Job, JobType, Project
from app.schemas.project import (
    AnalysisRead,
    GenerationSettingsRequest,
    GenerationSettingsResponse,
    ImportPreviewRequest,
    ImportPreviewResponse,
    JobRead,
    ProjectCreate,
    ProjectDeleteResponse,
    ProjectsDashboardRead,
    ProjectDetail,
    ProjectListRead,
    ProjectReadinessRead,
    ProjectRead,
    ProjectUpdate,
    ProjectWorkbenchRead,
    SceneCreateRequest,
    SceneCreateResponse,
    ScriptLibraryRead,
    ScriptDiagnosisResponse,
    ScriptRead,
    ScriptValidateRequest,
    ScriptValidateResponse,
    TemplateRead,
)
from app.services.frontend_data import (
    build_projects_dashboard,
    build_scripts_library,
    get_novel_source_project_payload,
    preview_import_text,
)
from app.services.jobs import cancel_active_jobs, create_job, get_active_job, run_analysis_job, run_script_generation_job
from app.services.script_diagnosis import diagnose_screenplay_yaml
from app.services.screenplay_yaml import validate_screenplay_yaml
from app.services.workbench import build_project_workbench
import yaml

router = APIRouter(tags=["projects"])


@router.get("/templates", response_model=list[TemplateRead])
def list_templates() -> list[TemplateRead]:
    return [
        TemplateRead(
            id="tv-drama",
            name="影视剧剧本模板",
            scenario="适合长篇小说改编为电视剧、网剧或电影分场剧本。",
            target_format="screenplay",
            backend_rules=["按章节组织场景", "突出人物动作和对白", "每场保留可拍摄的地点、时间和调度"],
            features=["按章节拆分场景", "保留人物动机与动作描写", "适配标准场景标题"],
            fields=["script", "metadata", "characters", "locations", "chapters", "scenes", "dialogue"],
            yamlExample=[
                "script:",
                "  schema_version: 1.0",
                "  metadata:",
                "    title: 剧本标题",
                "    target_format: screenplay",
                "  chapters:",
                "    - id: ch_001",
                "      scenes:",
                "        - id: sc_001_001",
                "          title: 场景标题",
                "          location_id: loc_001",
                "          dialogue:",
                "            - speaker_name: 人物名",
                "              line: 对白内容",
            ],
        ),
        TemplateRead(
            id="short-drama",
            name="短剧剧本模板",
            scenario="适合高节奏短剧、竖屏剧和强钩子内容生成。",
            target_format="short_drama",
            backend_rules=["开场三秒给出冲突", "每章场景要有反转或钩子", "对白更短更直接"],
            features=["强化开场冲突", "突出反转节点", "每集保留结尾钩子"],
            fields=["script", "metadata", "chapters", "scenes", "synopsis", "dialogue"],
            yamlExample=[
                "script:",
                "  metadata:",
                "    target_format: short_drama",
                "  chapters:",
                "    - id: ep_001",
                "      scenes:",
                "        - title: 开场冲突",
                "          synopsis: 主角被迫当众证明自己",
            ],
        ),
        TemplateRead(
            id="stage-play",
            name="话剧剧本模板",
            scenario="适合将小说改编为舞台表演文本和排练稿。",
            target_format="stage_play",
            backend_rules=["强化舞台调度和入退场", "减少不可舞台化的镜头描写", "对白承载更多心理变化"],
            features=["强调舞台调度", "保留幕与场结构", "补充人物入场退场"],
            fields=["script", "chapters", "scenes", "stage_directions", "dialogue"],
            yamlExample=[
                "script:",
                "  metadata:",
                "    target_format: stage_play",
                "  chapters:",
                "    - title: 第一幕",
                "      scenes:",
                "        - title: 出租屋夜谈",
                "          stage_directions:",
                "            - 灯光渐亮，人物入场。",
            ],
        ),
        TemplateRead(
            id="storyboard",
            name="分镜剧本模板",
            scenario="适合短视频、广告片、动画和导演分镜草案。",
            target_format="storyboard",
            backend_rules=["场景标题尽量镜头化", "stage_directions 写景别、运动和画面重点", "对白服务镜头节奏"],
            features=["拆分镜号", "补充景别与机位", "保留镜头意图"],
            fields=["script", "chapters", "scenes", "stage_directions", "dialogue"],
            yamlExample=[
                "script:",
                "  metadata:",
                "    target_format: storyboard",
                "  chapters:",
                "    - title: 分镜段落",
                "      scenes:",
                "        - title: 镜头 1",
                "          stage_directions:",
                "            - 全景展示地点与人物关系。",
            ],
        ),
        TemplateRead(
            id="audio-drama",
            name="广播剧剧本模板",
            scenario="适合有声剧、广播剧和多人配音脚本。",
            target_format="audio_drama",
            backend_rules=["用声音和环境音建立空间", "stage_directions 强调音效", "对白需要清晰区分人物身份"],
            features=["补充环境音", "强化对白辨识度", "减少视觉依赖"],
            fields=["script", "metadata", "chapters", "scenes", "stage_directions", "dialogue"],
            yamlExample=[
                "script:",
                "  metadata:",
                "    target_format: audio_drama",
                "  chapters:",
                "    - title: 第一集",
                "      scenes:",
                "        - title: 夜雨来信",
                "          stage_directions:",
                "            - SFX: 雨声渐强，纸张展开。",
                "          dialogue:",
                "            - speaker_name: 人物名",
                "              line: 这封信，终于到了。",
            ],
        ),
    ]


@router.post("/import/preview", response_model=ImportPreviewResponse)
def preview_import(payload: ImportPreviewRequest) -> ImportPreviewResponse:
    return ImportPreviewResponse.model_validate(
        preview_import_text(payload.title, payload.author, payload.text)
    )


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


@router.get("/projects/dashboard", response_model=ProjectsDashboardRead)
def get_projects_dashboard(db: Session = Depends(get_db)) -> ProjectsDashboardRead:
    return ProjectsDashboardRead.model_validate(build_projects_dashboard(db))


@router.get("/scripts/library", response_model=ScriptLibraryRead)
def get_scripts_library(db: Session = Depends(get_db)) -> ScriptLibraryRead:
    return ScriptLibraryRead.model_validate(build_scripts_library(db))


@router.post("/scripts/library/sources/{source_id}/import", response_model=ProjectRead, status_code=201)
def import_source_novel(source_id: str, db: Session = Depends(get_db)) -> ProjectRead:
    payload = get_novel_source_project_payload(source_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="素材小说不存在或无法读取。")

    project = Project(title=payload["title"], author=payload["author"])
    db.add(project)
    db.flush()

    for index, chapter_payload in enumerate(payload["chapters"], start=1):
        db.add(
            Chapter(
                project_id=project.id,
                number=index,
                title=chapter_payload["title"],
                content=chapter_payload["content"],
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


@router.delete("/projects/{project_id}", response_model=ProjectDeleteResponse)
def delete_project(project_id: int, db: Session = Depends(get_db)) -> ProjectDeleteResponse:
    project = _require_project(db, project_id)
    db.delete(project)
    db.commit()
    return ProjectDeleteResponse(deleted=True, project_id=project_id)


@router.patch("/projects/{project_id}", response_model=ProjectRead)
def update_project(project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db)) -> ProjectRead:
    project = _require_project(db, project_id)
    if payload.title is not None:
        project.title = payload.title
    if payload.author is not None:
        project.author = payload.author
    db.commit()
    db.refresh(project)
    return _project_to_read(project)


@router.post("/projects/{project_id}/clone", response_model=ProjectRead, status_code=201)
def clone_project(project_id: int, db: Session = Depends(get_db)) -> ProjectRead:
    source = _require_project(db, project_id)
    cloned = Project(
        title=f"{source.title} 副本",
        author=source.author,
        status=source.status,
        analysis_json=source.analysis_json,
        script_yaml=source.script_yaml,
        generation_settings_json=source.generation_settings_json,
    )
    db.add(cloned)
    db.flush()

    for chapter in source.chapters:
        db.add(
            Chapter(
                project_id=cloned.id,
                number=chapter.number,
                title=chapter.title,
                content=chapter.content,
            )
        )

    db.commit()
    db.refresh(cloned)
    return _project_to_read(cloned)


@router.get("/projects/{project_id}/workbench", response_model=ProjectWorkbenchRead)
def get_project_workbench(project_id: int, db: Session = Depends(get_db)) -> ProjectWorkbenchRead:
    project = _require_project(db, project_id)
    return ProjectWorkbenchRead.model_validate(build_project_workbench(project))


@router.get("/projects/{project_id}/readiness", response_model=ProjectReadinessRead)
def get_project_readiness(project_id: int, db: Session = Depends(get_db)) -> ProjectReadinessRead:
    project = _require_project(db, project_id)
    return _project_readiness(project)


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


@router.post("/projects/{project_id}/analysis-jobs/rerun", response_model=JobRead, status_code=202)
def rerun_analysis_job(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Job:
    project = _require_project(db, project_id)
    project.analysis_json = None
    project.script_yaml = None
    project.status = "created"
    db.query(Job).filter(
        Job.project_id == project_id,
        Job.type == JobType.analysis.value,
        Job.status.in_(["queued", "running"]),
    ).update({"status": "failed", "current_step": "已被重新解析任务取代", "error_message": "rerun"})
    db.commit()

    job = create_job(db, project_id, JobType.analysis)
    background_tasks.add_task(_run_analysis_job_task, job.id)
    return job


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


@router.post("/projects/{project_id}/script-jobs/rerun", response_model=JobRead, status_code=202)
def rerun_script_job(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Job:
    project = _require_project(db, project_id)
    cancel_active_jobs(db, project_id, JobType.script_generation, "已被重新生成任务取代")
    project.script_yaml = None
    if project.analysis_json:
        project.status = "analysis_completed"
    db.commit()

    job = create_job(db, project_id, JobType.script_generation)
    background_tasks.add_task(_run_script_generation_job_task, job.id)
    return job


@router.post("/projects/{project_id}/generation-settings", response_model=GenerationSettingsResponse)
def update_generation_settings(
    project_id: int,
    payload: GenerationSettingsRequest,
    db: Session = Depends(get_db),
) -> GenerationSettingsResponse:
    project = _require_project(db, project_id)
    project.generation_settings_json = json.dumps(payload.model_dump(), ensure_ascii=False)
    db.commit()
    return GenerationSettingsResponse(project_id=project_id, accepted=True, settings=payload)


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


@router.get("/projects/{project_id}/script/export/txt")
def export_script_txt(project_id: int, db: Session = Depends(get_db)) -> Response:
    project = _require_project(db, project_id)
    if not project.script_yaml:
        raise HTTPException(status_code=404, detail="当前项目还没有生成剧本。")

    content = _screenplay_text(project.script_yaml)
    filename = f"project-{project.id}-screenplay.txt"
    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/projects/{project_id}/script/export/markdown")
def export_script_markdown(project_id: int, db: Session = Depends(get_db)) -> Response:
    project = _require_project(db, project_id)
    if not project.script_yaml:
        raise HTTPException(status_code=404, detail="当前项目还没有生成剧本。")

    content = _screenplay_markdown(project.script_yaml)
    filename = f"project-{project.id}-screenplay.md"
    return Response(
        content=content,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/projects/{project_id}/scenes", response_model=SceneCreateResponse)
def add_project_scene(
    project_id: int,
    payload: SceneCreateRequest,
    db: Session = Depends(get_db),
) -> SceneCreateResponse:
    project = _require_project(db, project_id)
    if not project.script_yaml:
        raise HTTPException(status_code=404, detail="当前项目还没有生成剧本。")

    updated_yaml, scene_id = _append_scene(project.script_yaml, payload)
    valid, errors = validate_screenplay_yaml(updated_yaml)
    if not valid:
        raise HTTPException(status_code=422, detail={"message": "新增场景后剧本 YAML 校验失败。", "errors": errors})

    project.script_yaml = updated_yaml
    project.status = "script_edited"
    db.commit()
    db.refresh(project)
    return SceneCreateResponse(project_id=project.id, yaml=updated_yaml, scene_id=scene_id)


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


def _run_analysis_job_task(job_id: int) -> None:
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        run_analysis_job(db, job_id)


def _run_script_generation_job_task(job_id: int) -> None:
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        run_script_generation_job(db, job_id)


def _load_screenplay(yaml_text: str) -> dict:
    parsed = yaml.safe_load(yaml_text)
    if not isinstance(parsed, dict) or not isinstance(parsed.get("script"), dict):
        raise HTTPException(status_code=422, detail="剧本 YAML 结构无效。")
    return parsed


def _append_scene(yaml_text: str, payload: SceneCreateRequest) -> tuple[str, str]:
    parsed = _load_screenplay(yaml_text)
    script = parsed["script"]
    chapters = script.get("chapters") or []
    if not chapters:
        raise HTTPException(status_code=422, detail="剧本 YAML 中没有可添加场景的章节。")

    target_chapter = next((chapter for chapter in chapters if chapter.get("title") == payload.chapterTitle), chapters[0])
    scenes = target_chapter.setdefault("scenes", [])
    scene_id = f"{target_chapter.get('id', 'ch')}_extra_{len(scenes) + 1:03d}"

    locations = script.setdefault("locations", [])
    location_id = _ensure_location(locations, payload.location)
    characters = script.setdefault("characters", [])
    character_ids = _ensure_characters(characters, payload.characters)

    scene = {
        "id": scene_id,
        "title": payload.sceneTitle,
        "location_id": location_id,
        "time": payload.time,
        "characters": character_ids,
        "synopsis": payload.action or payload.sceneTitle,
        "stage_directions": [payload.action or f"{payload.location}中，人物围绕新冲突展开行动。"],
        "dialogue": [
            {
                "speaker_id": character_ids[0],
                "speaker_name": _character_name(characters, character_ids[0]),
                "line": payload.action or "这一场戏需要继续打磨对白。",
                "emotion": "neutral",
            }
        ],
    }
    scenes.append(scene)
    return yaml.safe_dump(parsed, allow_unicode=True, sort_keys=False), scene_id


def _ensure_location(locations: list[dict], name: str) -> str:
    for location in locations:
        if location.get("name") == name:
            return str(location.get("id"))

    location_id = f"loc_{len(locations) + 1:03d}"
    locations.append({"id": location_id, "name": name, "description": f"{name}，新增场景发生地。"})
    return location_id


def _ensure_characters(characters: list[dict], names_text: str | None) -> list[str]:
    names = [name.strip() for name in (names_text or "").replace(",", "、").split("、") if name.strip()]
    if not names and characters:
        return [str(characters[0]["id"])]
    if not names:
        names = ["待定人物"]

    ids = []
    for name in names:
        existing = next((character for character in characters if character.get("name") == name), None)
        if existing:
            ids.append(str(existing["id"]))
            continue

        character_id = f"char_extra_{len(characters) + 1:03d}"
        characters.append(
            {
                "id": character_id,
                "name": name,
                "role": "新增人物",
                "gender": "unknown",
                "age": None,
                "description": f"{name}，由作者在编辑阶段新增。",
            }
        )
        ids.append(character_id)
    return ids


def _character_name(characters: list[dict], character_id: str) -> str:
    for character in characters:
        if character.get("id") == character_id:
            return str(character.get("name") or character_id)
    return character_id


def _screenplay_text(yaml_text: str) -> str:
    parsed = _load_screenplay(yaml_text)
    script = parsed["script"]
    lines = [
        str(script.get("metadata", {}).get("title") or "未命名剧本"),
        "",
    ]
    for chapter in script.get("chapters", []):
        lines.extend([str(chapter.get("title", "未命名章节")), ""])
        for scene in chapter.get("scenes", []):
            lines.append(str(scene.get("title", "未命名场景")))
            lines.append(f"时间：{scene.get('time', '待定')}")
            if scene.get("synopsis"):
                lines.append(str(scene["synopsis"]))
            for direction in scene.get("stage_directions", []):
                lines.append(str(direction))
            for dialogue in scene.get("dialogue", []):
                lines.append(f"{dialogue.get('speaker_name', dialogue.get('speaker_id', '人物'))}：{dialogue.get('line', '')}")
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def _screenplay_markdown(yaml_text: str) -> str:
    parsed = _load_screenplay(yaml_text)
    script = parsed["script"]
    lines = [f"# {script.get('metadata', {}).get('title') or '未命名剧本'}", ""]
    for chapter in script.get("chapters", []):
        lines.extend([f"## {chapter.get('title', '未命名章节')}", ""])
        for scene in chapter.get("scenes", []):
            lines.extend([f"### {scene.get('title', '未命名场景')}", "", f"- 时间：{scene.get('time', '待定')}"])
            if scene.get("synopsis"):
                lines.extend(["", str(scene["synopsis"])])
            for direction in scene.get("stage_directions", []):
                lines.extend(["", f"> {direction}"])
            for dialogue in scene.get("dialogue", []):
                speaker = dialogue.get("speaker_name", dialogue.get("speaker_id", "人物"))
                lines.extend(["", f"**{speaker}**：{dialogue.get('line', '')}"])
            lines.append("")
    return "\n".join(lines).strip() + "\n"

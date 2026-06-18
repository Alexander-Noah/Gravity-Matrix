from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project import AppSetting, Job, JobStatus, JobType, Project
from app.models.user import User
from app.schemas.screenplay import ScreenplayDocument
from app.services.script_diagnosis import diagnose_screenplay_yaml
from app.services.workbench import build_project_workbench


def preview_import_text(title: str | None, author: str | None, text: str) -> dict[str, Any]:
    cleaned_text = _clean_import_text(text)
    chapters = _detect_chapters(cleaned_text)
    issues = _import_issues(cleaned_text, chapters)
    detected_title = title or _detect_title(cleaned_text) or "未命名小说"
    preprocess = _preprocess_import_text(chapters, cleaned_text)

    return {
        "title": detected_title,
        "author": author,
        "chapter_count": len(chapters),
        "total_chars": len(cleaned_text),
        "can_create_project": not any(issue["severity"] == "error" for issue in issues),
        "issues": issues,
        "chapters": chapters,
        "preprocess": preprocess,
    }


def build_projects_dashboard(db: Session) -> dict[str, Any]:
    active_projects_query = db.query(Project).filter(Project.deleted_at.is_(None))
    projects = active_projects_query.order_by(Project.updated_at.desc(), Project.id.desc()).limit(20).all()
    total = active_projects_query.count()
    has_script = active_projects_query.filter(Project.script_yaml.is_not(None)).count()
    active = (
        active_projects_query
        .filter(Project.status.in_(["created", "analysis_completed", "script_completed", "script_edited"]))
        .count()
    )
    exported = has_script
    needs_validation = sum(1 for project in projects if project.script_yaml and not _script_valid(project.script_yaml))

    return {
        "stats": [
            {
                "label": "进行中项目",
                "value": str(active),
                "note": f"共 {total} 个项目",
                "tone": "violet",
            },
            {
                "label": "已生成剧本",
                "value": str(has_script),
                "note": "可进入编辑或导出",
                "tone": "blue",
            },
            {
                "label": "待校验 YAML",
                "value": str(needs_validation),
                "note": "建议优先处理",
                "tone": "orange",
            },
            {
                "label": "已导出文件",
                "value": str(exported),
                "note": "后端支持 YAML 导出",
                "tone": "mint",
            },
        ],
        "project_cards": [_project_card(project) for project in projects],
        "activities": _recent_activities(db, projects),
    }


def build_scripts_library(db: Session) -> dict[str, Any]:
    projects = (
        db.query(Project)
        .filter(Project.deleted_at.is_(None))
        .filter(Project.script_yaml.is_not(None))
        .order_by(Project.updated_at.desc(), Project.id.desc())
        .all()
    )
    generated_items = [_script_library_item(project) for project in projects]
    source_items = _novel_source_library_items(limit=24)
    items = generated_items + source_items

    return {
        "stats": [
            {
                "label": "全部剧本",
                "value": str(len(generated_items)),
                "note": "已生成可编辑剧本",
                "tone": "violet",
            },
            {
                "label": "编辑中",
                "value": str(sum(1 for item in generated_items if item["status"] == "编辑中")),
                "note": "可继续修改 YAML",
                "tone": "blue",
            },
            {
                "label": "本地素材",
                "value": str(len(source_items)),
                "note": "可导入生成剧本",
                "tone": "mint",
            },
            {
                "label": "校验异常",
                "value": str(sum(1 for item in generated_items if item["status"] == "校验异常")),
                "note": "需要修正字段或引用",
                "tone": "orange",
            },
        ],
        "items": items,
    }


def build_profile_summary(
    db: Session,
    user: User,
    default_template_id: str,
    template_names: dict[str, str],
) -> dict[str, Any]:
    active_projects_query = db.query(Project).filter(Project.deleted_at.is_(None))
    latest_project = active_projects_query.order_by(Project.updated_at.desc(), Project.id.desc()).first()
    generated_scripts = active_projects_query.filter(Project.script_yaml.is_not(None)).all()
    selected_template_id = _default_template_id(db, default_template_id)
    if selected_template_id not in template_names:
        selected_template_id = default_template_id
    selected_template = template_names.get(selected_template_id, "影视剧剧本模板")

    if latest_project is None:
        current_project = "未创建项目"
        project_progress = 0
        workflow_step = "导入小说"
        script_status = "尚未生成剧本"
        schema_status = "待校验"
    else:
        workbench = build_project_workbench(latest_project)
        current_project = f"《{latest_project.title}》改编项目"
        project_progress = int(workbench["progress"]["percent"])
        workflow_step = _profile_workflow_step(latest_project)
        script_status = "已有 YAML 草稿" if latest_project.script_yaml else "尚未生成剧本"
        schema_status = "校验通过" if latest_project.script_yaml and _script_valid(latest_project.script_yaml) else "待校验"

    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": "创作者",
        },
        "stats": {
            "workspaceName": "AI 小说转剧本",
            "currentProject": current_project,
            "projectProgress": project_progress,
            "workflowStep": workflow_step,
            "selectedTemplate": selected_template,
            "scriptStatus": script_status,
            "libraryCount": len(generated_scripts),
            "schemaStatus": schema_status,
        },
    }


def get_novel_source_project_payload(source_id: str) -> dict[str, Any] | None:
    source_dir = _novel_source_root() / source_id
    if not source_dir.is_dir():
        return None

    metadata = _read_source_metadata(source_dir)
    title = _source_title(source_dir, metadata)
    author = metadata.get("author") or "本地素材"
    chapters = _source_chapters(source_dir, metadata)
    if not chapters:
        return None

    return {
        "title": title,
        "author": author,
        "chapters": [{"title": chapter["title"], "content": chapter["content"]} for chapter in chapters],
    }


def _novel_source_root() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "test_novels_by_book"


def _novel_source_library_items(limit: int = 24) -> list[dict[str, Any]]:
    root = _novel_source_root()
    if not root.is_dir():
        return []

    items = []
    for source_dir in sorted([path for path in root.iterdir() if path.is_dir()])[:limit]:
        metadata = _read_source_metadata(source_dir)
        chapters = _source_chapters(source_dir, metadata, include_content=False)
        title = _source_title(source_dir, metadata)
        genre = metadata.get("genre") or "小说素材"
        tone = metadata.get("tone") or "待分析"

        items.append(
            {
                "id": f"source-{source_dir.name}",
                "project_id": None,
                "source_id": source_dir.name,
                "source_type": "source_novel",
                "title": f"《{title}》素材",
                "sourceNovel": f"《{title}》",
                "type": genre,
                "chapters": int(metadata.get("chapter_count") or len(chapters)),
                "scenes": 0,
                "dialogues": 0,
                "schemaStatus": "待生成",
                "status": "素材",
                "updatedAt": _relative_time(datetime.fromtimestamp(source_dir.stat().st_mtime)),
                "tags": [genre, tone, "本地素材", source_dir.name],
                "summary": _source_summary(source_dir, metadata),
            }
        )

    return items


def _read_source_metadata(source_dir: Path) -> dict[str, Any]:
    metadata_path = source_dir / "metadata.json"
    if not metadata_path.exists():
        return {}
    try:
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _source_title(source_dir: Path, metadata: dict[str, Any]) -> str:
    title = str(metadata.get("title") or "").strip()
    if title:
        return title

    full_text_path = source_dir / "full_text.txt"
    if full_text_path.exists():
        try:
            for line in full_text_path.read_text(encoding="utf-8").splitlines()[:12]:
                stripped = line.strip()
                if stripped.startswith("标题："):
                    return stripped.replace("标题：", "", 1).strip() or source_dir.name
                if stripped.startswith("第"):
                    return stripped[:60]
        except (UnicodeDecodeError, OSError):
            pass

    return source_dir.name.replace("_", " ").title()


def _source_chapters(
    source_dir: Path,
    metadata: dict[str, Any],
    include_content: bool = True,
) -> list[dict[str, Any]]:
    chapter_titles = [str(title) for title in metadata.get("chapter_titles", []) if str(title).strip()]
    chapter_dir = source_dir / "chapters"
    chapter_files = sorted(chapter_dir.glob("chapter_*.txt")) if chapter_dir.is_dir() else []
    chapters = []

    for index, path in enumerate(chapter_files, start=1):
        if path.name == "chapter_demo.txt":
            continue
        title = chapter_titles[index - 1] if index <= len(chapter_titles) else f"第{index}章"
        content = ""
        if include_content:
            try:
                content = path.read_text(encoding="utf-8").strip()
            except (UnicodeDecodeError, OSError):
                content = ""
        chapters.append({"title": title, "content": content})

    if chapters:
        return chapters

    full_text_path = source_dir / "full_text.txt"
    if not full_text_path.exists():
        return []
    try:
        text = full_text_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    detected = _detect_chapters(text)
    return [
        {
            "title": chapter["title"],
            "content": chapter["content"] if include_content else "",
        }
        for chapter in detected
    ]


def _source_summary(source_dir: Path, metadata: dict[str, Any]) -> str:
    characters = metadata.get("main_characters") or []
    genre = metadata.get("genre") or "小说"
    tone = metadata.get("tone") or "待分析"
    if characters:
        return f"{genre} / {tone}；主要人物：{'、'.join(str(name) for name in characters[:4])}。"
    return f"{genre} / {tone}；可导入工作台生成剧本。"


def _detect_chapters(text: str) -> list[dict[str, Any]]:
    if not text:
        return []

    chapters = []
    for index, chapter in enumerate(_simple_split_chapters(text), start=1):
        content = chapter["content"].strip()
        chapters.append(
            {
                "number": index,
                "title": chapter["title"].strip(),
                "content": content,
                "char_count": len(content),
                "excerpt": _brief(content, 80),
            }
        )
    return chapters


def _clean_import_text(text: str) -> str:
    return "\n".join(line.rstrip() for line in str(text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")).strip()


def _simple_split_chapters(text: str) -> list[dict[str, str]]:
    lines = _clean_import_text(text).splitlines()
    chapters: list[dict[str, str]] = []
    current_title: str | None = None
    current_lines: list[str] = []
    chapter_title_pattern = re.compile(r"^\s*(第[一二三四五六七八九十百千万零〇\d]+[章节回卷集].*|Chapter\s+\d+.*)\s*$", re.IGNORECASE)

    for line in lines:
        if chapter_title_pattern.match(line):
            if current_title is not None or current_lines:
                chapters.append({"title": current_title or "全文", "content": "\n".join(current_lines).strip()})
            current_title = line.strip()
            current_lines = []
            continue
        current_lines.append(line)

    if current_title is not None or current_lines:
        chapters.append({"title": current_title or "全文", "content": "\n".join(current_lines).strip()})
    return chapters or [{"title": "全文", "content": _clean_import_text(text)}]


def _preprocess_import_text(chapters: list[dict[str, Any]], text: str) -> dict[str, Any]:
    """Return import metadata only; AI performs semantic parsing later."""
    source_units = chapters or [
        {
            "number": 1,
            "title": "全文",
            "content": text,
            "char_count": len(text),
            "excerpt": _brief(text, 80),
        }
    ]

    return {
        "characters": [],
        "locations": [],
        "chapter_summaries": [
            {
                "chapter_number": unit["number"],
                "title": unit["title"],
                "summary": "",
                "char_count": unit.get("char_count", len(unit.get("content", ""))),
                "source": "import_structure",
            }
            for unit in source_units
        ],
        "themes": [],
        "conflicts": [],
        "preparation_notes": [
            f"已保存 {len(source_units)} 个章节。人物、地点、事件、对白归属将在 AI 解析阶段完成。",
        ],
    }


def _import_issues(text: str, chapters: list[dict[str, Any]]) -> list[dict[str, str]]:
    issues = []
    if not text:
        issues.append(_issue("empty_text", "error", "文本为空，请粘贴或上传小说正文。"))
        return issues

    if len(chapters) < settings.min_chapters:
        issues.append(
            _issue(
                "not_enough_chapters",
                "error",
                f"当前识别到 {len(chapters)} 个章节，至少需要 {settings.min_chapters} 个章节。",
            )
        )

    if len(chapters) > settings.max_chapters:
        issues.append(
            _issue(
                "too_many_chapters",
                "error",
                f"当前识别到 {len(chapters)} 个章节，最多支持 {settings.max_chapters} 个章节。",
            )
        )

    for chapter in chapters:
        if chapter["char_count"] == 0:
            issues.append(_issue("empty_chapter", "warning", f"{chapter['title']} 没有识别到正文。"))
        if chapter["char_count"] > settings.max_chapter_chars:
            issues.append(
                _issue(
                    "chapter_too_long",
                    "error",
                    f"{chapter['title']} 超过单章 {settings.max_chapter_chars} 字限制。",
                )
            )

    if not issues:
        issues.append(_issue("ready", "info", "章节结构满足创建项目要求。"))
    return issues


def _project_card(project: Project) -> dict[str, Any]:
    progress = build_project_workbench(project)["progress"]["percent"]
    scene_count = 0
    if project.script_yaml:
        scene_count = _script_summary(project.script_yaml)["scene_count"]

    return {
        "id": project.id,
        "title": f"《{project.title}》改编项目",
        "type": _project_type(project),
        "status": _project_status_label(project),
        "progress": progress,
        "updatedAt": _relative_time(project.updated_at),
        "chapters": len(project.chapters),
        "scenes": scene_count,
        "owner": project.author or "创作者",
        "nextAction": _next_action_label(project),
    }


def _script_library_item(project: Project) -> dict[str, Any]:
    summary = _script_summary(project.script_yaml or "")
    valid_schema = summary["valid_schema"]
    diagnosis = diagnose_screenplay_yaml(project.id, project.script_yaml or "", "stored_yaml")
    schema_status = "校验通过" if valid_schema else "字段缺失"
    status = _script_status_label(project, valid_schema)

    return {
        "id": f"script-{project.id:03d}",
        "project_id": project.id,
        "title": f"《{project.title}》剧本",
        "sourceNovel": f"《{project.title}》",
        "type": "影视剧",
        "chapters": summary["chapter_count"],
        "scenes": summary["scene_count"],
        "dialogues": summary["dialogue_count"],
        "schemaStatus": schema_status,
        "status": status,
        "updatedAt": _relative_time(project.updated_at),
        "tags": _script_tags(project, diagnosis),
    }


def _recent_activities(db: Session, projects: list[Project]) -> list[dict[str, str]]:
    jobs = db.query(Job).order_by(Job.updated_at.desc(), Job.id.desc()).limit(8).all()
    activities = []
    project_map = {project.id: project for project in projects}
    for job in jobs:
        project = project_map.get(job.project_id) or db.get(Project, job.project_id)
        if project is None or project.deleted_at is not None:
            continue
        activities.append(
            {
                "title": _job_activity_title(project, job),
                "time": _relative_time(job.updated_at),
                "status": _job_status_label(job.status),
            }
        )

    if activities:
        return activities[:6]

    return [
        {
            "title": f"创建《{project.title}》改编项目",
            "time": _relative_time(project.created_at),
            "status": "已保存",
        }
        for project in projects[:6]
    ]


def _script_summary(yaml_text: str) -> dict[str, Any]:
    try:
        parsed = yaml.safe_load(yaml_text)
        document = ScreenplayDocument.model_validate(parsed)
    except (yaml.YAMLError, ValidationError, ValueError, TypeError):
        return {"valid_schema": False, "chapter_count": 0, "scene_count": 0, "dialogue_count": 0}

    return {
        "valid_schema": True,
        "chapter_count": len(document.script.chapters),
        "scene_count": sum(len(chapter.scenes) for chapter in document.script.chapters),
        "dialogue_count": sum(
            len(scene.dialogue)
            for chapter in document.script.chapters
            for scene in chapter.scenes
        ),
    }


def _script_valid(yaml_text: str) -> bool:
    return bool(_script_summary(yaml_text)["valid_schema"])


def _default_template_id(db: Session, fallback: str) -> str:
    setting = db.get(AppSetting, "default_template_id")
    return setting.value if setting is not None else fallback


def _profile_workflow_step(project: Project) -> str:
    if project.script_yaml:
        return "编辑与导出"
    if project.analysis_json:
        return "生成剧本"
    return "AI 解析"


def _detect_title(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("第") and not stripped.lower().startswith("chapter"):
            return stripped[:80]
    return None


def _project_type(project: Project) -> str:
    themes = []
    if project.analysis_json:
        try:
            themes = json.loads(project.analysis_json).get("themes", [])
        except json.JSONDecodeError:
            themes = []
    prefix = " / ".join(str(theme) for theme in themes[:2]) or "小说改编"
    return f"{prefix} / 影视剧"


def _project_status_label(project: Project) -> str:
    labels = {
        "created": "待解析",
        "analysis_completed": "待生成",
        "script_completed": "编辑中",
        "script_edited": "已完成",
    }
    return labels.get(project.status, project.status)


def _script_status_label(project: Project, valid_schema: bool) -> str:
    if not valid_schema:
        return "校验异常"
    if project.status == "script_edited":
        return "已完成"
    return "编辑中"


def _next_action_label(project: Project) -> str:
    if project.script_yaml:
        return "继续编辑 YAML"
    if project.analysis_json:
        return "生成剧本"
    return "进入 AI 解析"


def _script_tags(project: Project, diagnosis: dict[str, Any]) -> list[str]:
    tags = ["影视剧"]
    if diagnosis.get("grade"):
        tags.append(str(diagnosis["grade"]))
    if project.analysis_json:
        try:
            themes = json.loads(project.analysis_json).get("themes", [])
        except json.JSONDecodeError:
            themes = []
        tags.extend(str(theme) for theme in themes[:2])
    return list(dict.fromkeys(tags))[:4]


def _job_activity_title(project: Project, job: Job) -> str:
    if job.type == JobType.analysis.value:
        action = "生成 AI 解析"
    elif job.type == JobType.script_generation.value:
        action = "生成剧本 YAML"
    else:
        action = "更新项目"
    return f"{action}《{project.title}》"


def _job_status_label(status: str) -> str:
    labels = {
        JobStatus.queued.value: "排队中",
        JobStatus.running.value: "进行中",
        JobStatus.succeeded.value: "已完成",
        JobStatus.failed.value: "失败",
    }
    return labels.get(status, status)


def _relative_time(value: datetime | None) -> str:
    if value is None:
        return "未知时间"
    return value.strftime("%Y-%m-%d %H:%M")


def _issue(code: str, severity: str, message: str) -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _brief(text: str, limit: int) -> str:
    compact = re.sub(r"\s+", " ", text.strip())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "..."

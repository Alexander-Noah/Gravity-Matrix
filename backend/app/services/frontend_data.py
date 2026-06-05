from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

import yaml
from pydantic import ValidationError
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project import Job, JobStatus, JobType, Project
from app.schemas.screenplay import ScreenplayDocument
from app.services.script_diagnosis import diagnose_screenplay_yaml
from app.services.workbench import build_project_workbench


def preview_import_text(title: str | None, author: str | None, text: str) -> dict[str, Any]:
    cleaned_text = text.strip()
    chapters = _detect_chapters(cleaned_text)
    issues = _import_issues(cleaned_text, chapters)
    detected_title = title or _detect_title(cleaned_text) or "未命名小说"

    return {
        "title": detected_title,
        "author": author,
        "chapter_count": len(chapters),
        "total_chars": len(cleaned_text),
        "can_create_project": not any(issue["severity"] == "error" for issue in issues),
        "issues": issues,
        "chapters": chapters,
    }


def build_projects_dashboard(db: Session) -> dict[str, Any]:
    projects = db.query(Project).order_by(Project.updated_at.desc(), Project.id.desc()).limit(20).all()
    total = db.query(func.count(Project.id)).scalar() or 0
    has_script = db.query(func.count(Project.id)).filter(Project.script_yaml.is_not(None)).scalar() or 0
    active = (
        db.query(func.count(Project.id))
        .filter(Project.status.in_(["created", "analysis_completed", "script_completed", "script_edited"]))
        .scalar()
        or 0
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
        .filter(Project.script_yaml.is_not(None))
        .order_by(Project.updated_at.desc(), Project.id.desc())
        .all()
    )
    items = [_script_library_item(project) for project in projects]

    return {
        "stats": [
            {
                "label": "全部剧本",
                "value": str(len(items)),
                "note": "来自已生成剧本的项目",
                "tone": "violet",
            },
            {
                "label": "编辑中",
                "value": str(sum(1 for item in items if item["status"] == "编辑中")),
                "note": "可继续修改 YAML",
                "tone": "blue",
            },
            {
                "label": "已完成",
                "value": str(sum(1 for item in items if item["status"] == "已完成")),
                "note": "Schema 校验通过",
                "tone": "mint",
            },
            {
                "label": "校验异常",
                "value": str(sum(1 for item in items if item["status"] == "校验异常")),
                "note": "需要修正字段或引用",
                "tone": "orange",
            },
        ],
        "items": items,
    }


def _detect_chapters(text: str) -> list[dict[str, Any]]:
    if not text:
        return []

    pattern = re.compile(
        r"(?m)^\s*(?P<title>(?:第[\d一二三四五六七八九十百千万零〇两]+[章节回卷幕部集][^\n]{0,80}|Chapter\s+\d+[^\n]{0,80}|CHAPTER\s+[IVXLCDM\d]+[^\n]{0,80}))\s*$",
        re.IGNORECASE,
    )
    matches = list(pattern.finditer(text))
    if not matches:
        return []

    chapters = []
    for index, match in enumerate(matches, start=1):
        start = match.end()
        end = matches[index].start() if index < len(matches) else len(text)
        content = text[start:end].strip()
        chapters.append(
            {
                "number": index,
                "title": match.group("title").strip(),
                "char_count": len(content),
                "excerpt": _brief(content, 80),
            }
        )
    return chapters


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
        if project is None:
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

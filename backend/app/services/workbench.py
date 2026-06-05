from __future__ import annotations

import json
from typing import Any

import yaml
from pydantic import ValidationError

from app.models.project import Project
from app.schemas.screenplay import ScreenplayDocument
from app.services.script_diagnosis import diagnose_screenplay_yaml


def build_project_workbench(project: Project) -> dict[str, Any]:
    analysis = _analysis_payload(project)
    script = _script_payload(project)
    return {
        "project": _project_payload(project),
        "workflow_steps": _workflow_steps(project),
        "progress": _progress(project),
        "analysis": analysis,
        "script": script,
    }


def _project_payload(project: Project) -> dict[str, Any]:
    return {
        "id": project.id,
        "title": project.title,
        "author": project.author,
        "status": project.status,
        "chapter_count": len(project.chapters),
        "has_analysis": project.analysis_json is not None,
        "has_script": project.script_yaml is not None,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }


def _analysis_payload(project: Project) -> dict[str, Any]:
    if not project.analysis_json:
        return {
            "raw": None,
            "overview": {
                "character_count": 0,
                "location_count": 0,
                "chapter_summary_count": 0,
                "conflict_count": 0,
                "themes": [],
                "conflicts": [],
            },
        }

    raw = json.loads(project.analysis_json)
    return {
        "raw": raw,
        "overview": {
            "character_count": len(raw.get("characters", [])),
            "location_count": len(raw.get("locations", [])),
            "chapter_summary_count": len(raw.get("chapter_summaries", [])),
            "conflict_count": len(raw.get("conflicts", [])),
            "themes": raw.get("themes", []),
            "conflicts": raw.get("conflicts", []),
        },
    }


def _script_payload(project: Project) -> dict[str, Any]:
    if not project.script_yaml:
        return {"yaml": None, "structure": [], "diagnosis": None}

    return {
        "yaml": project.script_yaml,
        "structure": _script_structure(project.script_yaml),
        "diagnosis": diagnose_screenplay_yaml(project.id, project.script_yaml, "stored_yaml"),
    }


def _script_structure(yaml_text: str) -> list[dict[str, Any]]:
    try:
        parsed = yaml.safe_load(yaml_text)
        document = ScreenplayDocument.model_validate(parsed)
    except (yaml.YAMLError, ValidationError, ValueError, TypeError):
        return []

    chapters = []
    for chapter_index, chapter in enumerate(document.script.chapters):
        scenes = []
        for scene_index, scene in enumerate(chapter.scenes):
            scenes.append(
                {
                    "id": scene.id,
                    "title": scene.title,
                    "label": f"场景 {chapter_index + 1}-{scene_index + 1} {scene.title}",
                    "active": chapter_index == 0 and scene_index == 0,
                    "location_id": scene.location_id,
                    "time": scene.time,
                }
            )

        chapters.append(
            {
                "id": chapter.id,
                "title": chapter.title,
                "label": f"第 {chapter_index + 1} 章 {chapter.title}",
                "open": chapter_index == 0,
                "scenes": scenes,
            }
        )
    return chapters


def _workflow_steps(project: Project) -> list[dict[str, str]]:
    has_script = project.script_yaml is not None
    has_analysis = project.analysis_json is not None or has_script
    has_edited_script = project.status == "script_edited"

    return [
        {
            "number": "1",
            "title": "导入小说",
            "description": "上传或粘贴小说内容",
            "status": "done",
        },
        {
            "number": "2",
            "title": "AI 解析",
            "description": "智能识别人物、场景与剧情",
            "status": "done" if has_analysis else "current",
        },
        {
            "number": "3",
            "title": "生成剧本",
            "description": "一键生成结构化剧本",
            "status": "done" if has_script else ("current" if has_analysis else "upcoming"),
        },
        {
            "number": "4",
            "title": "编辑与导出",
            "description": "在线编辑并导出剧本",
            "status": "done" if has_edited_script else ("current" if has_script else "upcoming"),
        },
    ]


def _progress(project: Project) -> dict[str, Any]:
    has_script = project.script_yaml is not None
    has_analysis = project.analysis_json is not None or has_script
    has_edited_script = project.status == "script_edited"
    stages = [
        {"label": "小说导入", "status": "done", "note": ""},
        _stage("AI内容解析", has_analysis, True),
        _stage("生成剧本", has_script, has_analysis),
        _stage("编辑与导出", has_edited_script, has_script),
    ]

    completed = sum(1 for stage in stages if stage["status"] == "done")
    return {"percent": completed * 25, "stages": stages}


def _stage(label: str, done: bool, can_start: bool) -> dict[str, str]:
    if done:
        return {"label": label, "status": "done", "note": ""}
    if can_start:
        return {"label": label, "status": "active", "note": "进行中"}
    return {"label": label, "status": "pending", "note": "待开始"}

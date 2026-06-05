from __future__ import annotations

from typing import Any

import yaml
from pydantic import ValidationError

from app.schemas.screenplay import ScreenplayDocument


def diagnose_screenplay_yaml(project_id: int, yaml_text: str, source: str) -> dict[str, Any]:
    try:
        parsed = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        return _invalid_report(
            project_id,
            source,
            "yaml_parse_error",
            f"YAML 解析失败：{exc}",
            "请检查缩进、冒号和列表格式后重新诊断。",
        )

    if not isinstance(parsed, dict):
        return _invalid_report(
            project_id,
            source,
            "yaml_top_level_not_object",
            "YAML 顶层必须是对象，并包含 script 字段。",
            "请按剧本 YAML Schema 使用 script 作为顶层字段。",
        )

    try:
        document = ScreenplayDocument.model_validate(parsed)
    except ValidationError as exc:
        findings = [
            _finding(
                code="schema_validation_error",
                severity="error",
                category="schema",
                path=_error_path(error.get("loc", ())),
                message=str(error.get("msg", "剧本 YAML 不符合 Schema。")),
                recommendation="请根据 YAML Schema 文档补齐字段或修正引用关系。",
            )
            for error in exc.errors()
        ]
        return _report(project_id, source, False, 0, "invalid", _empty_summary(len(findings)), [], findings)
    except ValueError as exc:
        return _invalid_report(
            project_id,
            source,
            "schema_reference_error",
            str(exc),
            "请检查场景地点、出场人物和对白说话人是否引用了已声明的 id。",
        )

    script = document.script
    findings = _diagnose_valid_script(document)
    summary = _summary(document, findings)
    score = _score(findings)
    grade = _grade(score)
    strengths = _strengths(document, findings)

    return _report(project_id, source, True, score, grade, summary, strengths, findings)


def _diagnose_valid_script(document: ScreenplayDocument) -> list[dict[str, str]]:
    script = document.script
    findings: list[dict[str, str]] = []
    character_scene_counts = {character.id: 0 for character in script.characters}
    location_scene_counts = {location.id: 0 for location in script.locations}

    if script.metadata.total_chapters != len(script.chapters):
        findings.append(
            _finding(
                code="metadata_chapter_count_mismatch",
                severity="warning",
                category="structure",
                path="script.metadata.total_chapters",
                message="metadata.total_chapters 与实际剧本章节数不一致。",
                recommendation="请让 total_chapters 与 chapters 数组长度保持一致，便于前端和导出工具读取。",
            )
        )

    for chapter_index, chapter in enumerate(script.chapters):
        chapter_path = f"script.chapters[{chapter_index}]"
        if len(chapter.scenes) == 1:
            findings.append(
                _finding(
                    code="low_scene_density",
                    severity="suggestion",
                    category="structure",
                    path=f"{chapter_path}.scenes",
                    message="该章节只有 1 个场景，戏剧推进可能偏概括。",
                    recommendation="可考虑拆成铺垫、冲突、转折等多个场景。",
                )
            )

        if len(chapter.summary.strip()) < 20:
            findings.append(
                _finding(
                    code="short_chapter_summary",
                    severity="suggestion",
                    category="structure",
                    path=f"{chapter_path}.summary",
                    message="章节摘要偏短，可能不足以说明改编取舍。",
                    recommendation="补充本章目标、冲突和转折，让作者更容易回看结构。",
                )
            )

        for scene_index, scene in enumerate(chapter.scenes):
            scene_path = f"{chapter_path}.scenes[{scene_index}]"
            location_scene_counts[scene.location_id] = location_scene_counts.get(scene.location_id, 0) + 1
            for character_id in scene.characters:
                character_scene_counts[character_id] = character_scene_counts.get(character_id, 0) + 1

            if len(scene.synopsis.strip()) < 20:
                findings.append(
                    _finding(
                        code="short_scene_synopsis",
                        severity="suggestion",
                        category="scene",
                        path=f"{scene_path}.synopsis",
                        message="场景概述偏短，可能缺少人物目标或场景冲突。",
                        recommendation="补充该场景发生了什么、人物想要什么、阻力是什么。",
                    )
                )

            if not scene.stage_directions:
                findings.append(
                    _finding(
                        code="missing_stage_directions",
                        severity="warning",
                        category="scene",
                        path=f"{scene_path}.stage_directions",
                        message="该场景没有舞台说明，画面感和可拍性不足。",
                        recommendation="至少补充一条动作、环境或镜头调度说明。",
                    )
                )

            if not scene.dialogue:
                findings.append(
                    _finding(
                        code="missing_dialogue",
                        severity="warning",
                        category="dialogue",
                        path=f"{scene_path}.dialogue",
                        message="该场景没有对白，剧本可能更像章节摘要。",
                        recommendation="为主要人物补充能推动冲突或表现情绪的对白。",
                    )
                )
            elif len(scene.dialogue) < 2:
                findings.append(
                    _finding(
                        code="low_dialogue_density",
                        severity="suggestion",
                        category="dialogue",
                        path=f"{scene_path}.dialogue",
                        message="该场景对白数量偏少，人物互动可能不足。",
                        recommendation="可补充问答、反驳或停顿后的回应，让场景更有戏剧张力。",
                    )
                )

            scene_character_ids = set(scene.characters)
            for dialogue_index, dialogue in enumerate(scene.dialogue):
                if dialogue.speaker_id not in scene_character_ids:
                    findings.append(
                        _finding(
                            code="dialogue_speaker_not_in_scene",
                            severity="warning",
                            category="dialogue",
                            path=f"{scene_path}.dialogue[{dialogue_index}].speaker_id",
                            message="对白说话人没有出现在当前场景 characters 列表中。",
                            recommendation="把该人物加入当前场景 characters，或修改对白 speaker_id。",
                        )
                    )

    unused_characters = [character_id for character_id, count in character_scene_counts.items() if count == 0]
    for character_id in unused_characters:
        findings.append(
            _finding(
                code="unused_character",
                severity="warning",
                category="character",
                path=f"script.characters.{character_id}",
                message=f"人物 {character_id} 已声明但没有在任何场景出场。",
                recommendation="如果该人物重要，请安排出场；如果不重要，可以从人物表中移除。",
            )
        )

    if script.characters:
        lead_character = script.characters[0]
        lead_count = character_scene_counts.get(lead_character.id, 0)
        total_scenes = sum(len(chapter.scenes) for chapter in script.chapters)
        if total_scenes and lead_count / total_scenes < 0.5:
            findings.append(
                _finding(
                    code="lead_character_underused",
                    severity="suggestion",
                    category="character",
                    path=f"script.characters.{lead_character.id}",
                    message="首位核心人物出场比例偏低，主线聚焦可能不够。",
                    recommendation="确认主角是否应在更多关键场景中推动行动或承受冲突。",
                )
            )

    if location_scene_counts:
        most_used_location_count = max(location_scene_counts.values())
        total_scenes = sum(location_scene_counts.values())
        if total_scenes >= 3 and most_used_location_count / total_scenes > 0.8:
            findings.append(
                _finding(
                    code="location_usage_too_concentrated",
                    severity="suggestion",
                    category="scene",
                    path="script.locations",
                    message="场景地点使用过于集中，视觉层次可能单一。",
                    recommendation="可考虑加入与剧情转折相关的新空间，增强场景变化。",
                )
            )

    notes = script.adaptation_notes
    if not notes.themes:
        findings.append(
            _finding(
                code="missing_themes",
                severity="suggestion",
                category="adaptation",
                path="script.adaptation_notes.themes",
                message="改编说明缺少主题记录。",
                recommendation="补充 1 到 3 个主题，帮助作者判断改编方向是否一致。",
            )
        )
    if not notes.conflicts:
        findings.append(
            _finding(
                code="missing_conflicts",
                severity="suggestion",
                category="adaptation",
                path="script.adaptation_notes.conflicts",
                message="改编说明缺少核心冲突记录。",
                recommendation="补充主要人物目标与阻碍，方便后续强化戏剧张力。",
            )
        )
    if not notes.omissions:
        findings.append(
            _finding(
                code="missing_omissions",
                severity="suggestion",
                category="adaptation",
                path="script.adaptation_notes.omissions",
                message="改编说明缺少删减或压缩记录。",
                recommendation="记录哪些小说内容被压缩，方便作者回溯取舍。",
            )
        )

    return findings


def _summary(document: ScreenplayDocument, findings: list[dict[str, str]]) -> dict[str, int]:
    script = document.script
    scene_count = sum(len(chapter.scenes) for chapter in script.chapters)
    dialogue_count = sum(len(scene.dialogue) for chapter in script.chapters for scene in chapter.scenes)
    return {
        "chapter_count": len(script.chapters),
        "scene_count": scene_count,
        "character_count": len(script.characters),
        "location_count": len(script.locations),
        "dialogue_count": dialogue_count,
        "issue_count": _count(findings, "error"),
        "warning_count": _count(findings, "warning"),
        "suggestion_count": _count(findings, "suggestion"),
    }


def _empty_summary(issue_count: int = 0) -> dict[str, int]:
    return {
        "chapter_count": 0,
        "scene_count": 0,
        "character_count": 0,
        "location_count": 0,
        "dialogue_count": 0,
        "issue_count": issue_count,
        "warning_count": 0,
        "suggestion_count": 0,
    }


def _strengths(document: ScreenplayDocument, findings: list[dict[str, str]]) -> list[str]:
    strengths = ["YAML Schema 合法", "人物和地点引用关系完整"]
    if _count(findings, "warning") == 0:
        strengths.append("未发现需要立即修正的结构风险")
    if document.script.adaptation_notes.themes and document.script.adaptation_notes.conflicts:
        strengths.append("改编说明包含主题和核心冲突")
    if sum(len(scene.dialogue) for chapter in document.script.chapters for scene in chapter.scenes) > 0:
        strengths.append("剧本已包含可继续打磨的对白")
    return strengths


def _score(findings: list[dict[str, str]]) -> int:
    penalty = _count(findings, "error") * 20
    penalty += _count(findings, "warning") * 8
    penalty += _count(findings, "suggestion") * 3
    return max(0, 100 - penalty)


def _grade(score: int) -> str:
    if score >= 90:
        return "excellent"
    if score >= 75:
        return "good"
    if score >= 60:
        return "needs_work"
    return "poor"


def _count(findings: list[dict[str, str]], severity: str) -> int:
    return sum(1 for finding in findings if finding["severity"] == severity)


def _invalid_report(
    project_id: int,
    source: str,
    code: str,
    message: str,
    recommendation: str,
) -> dict[str, Any]:
    findings = [
        _finding(
            code=code,
            severity="error",
            category="schema",
            path="script",
            message=message,
            recommendation=recommendation,
        )
    ]
    return _report(project_id, source, False, 0, "invalid", _empty_summary(1), [], findings)


def _report(
    project_id: int,
    source: str,
    valid_schema: bool,
    score: int,
    grade: str,
    summary: dict[str, int],
    strengths: list[str],
    findings: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "project_id": project_id,
        "source": source,
        "valid_schema": valid_schema,
        "score": score,
        "grade": grade,
        "summary": summary,
        "strengths": strengths,
        "findings": findings,
    }


def _finding(
    code: str,
    severity: str,
    category: str,
    path: str,
    message: str,
    recommendation: str,
) -> dict[str, str]:
    return {
        "code": code,
        "severity": severity,
        "category": category,
        "path": path,
        "message": message,
        "recommendation": recommendation,
    }


def _error_path(location: tuple[Any, ...]) -> str:
    if not location:
        return "script"
    path = ""
    for item in location:
        if isinstance(item, int):
            path += f"[{item}]"
        else:
            path = f"{path}.{item}" if path else str(item)
    return path

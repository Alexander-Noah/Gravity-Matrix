from __future__ import annotations

import re
from typing import Any

from app.schemas.novel_script import CharacterRead, SceneContentRead, SceneRead


def clean_text(content: str) -> str:
    return "\n".join(
        line.rstrip()
        for line in str(content or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    ).strip()


def split_chapters(content: str) -> list[dict[str, str]]:
    text = clean_text(content)
    if not text:
        return []

    chapter_title_pattern = re.compile(
        r"^\s*(第[一二三四五六七八九十百千万零〇\d]+[章节回卷集].*|Chapter\s+\d+.*)\s*$",
        re.IGNORECASE,
    )
    chapters: list[dict[str, str]] = []
    current_title: str | None = None
    current_lines: list[str] = []
    for line in text.splitlines():
        if chapter_title_pattern.match(line):
            if current_title is not None or current_lines:
                chapters.append({"title": current_title or "全文", "content": "\n".join(current_lines).strip()})
            current_title = line.strip()
            current_lines = []
            continue
        current_lines.append(line)

    if current_title is not None or current_lines:
        chapters.append({"title": current_title or "全文", "content": "\n".join(current_lines).strip()})
    return chapters or [{"title": "全文", "content": text}]


def extract_characters(content: str) -> list[CharacterRead]:
    raise RuntimeError("本地人物识别已禁用，请使用项目 AI 解析流程。")


def extract_scenes(chapters: list[dict], characters: list[dict]) -> list[SceneRead]:
    raise RuntimeError("本地场景识别已禁用，请使用项目 AI 解析流程。")


def generate_scene_content(scene: dict, characters: list[dict]) -> list[SceneContentRead]:
    raise RuntimeError("本地对白归属已禁用，请使用项目 AI 解析流程。")


def build_yaml(title: str, characters: list[dict], scenes: list[dict]) -> str:
    raise RuntimeError("本地模板剧本生成已禁用，请使用项目 AI 生成剧本流程。")

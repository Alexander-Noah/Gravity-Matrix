from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
ARGS = None
if "--demo" in sys.argv:
    os.environ["LLM_API_KEY"] = ""
    os.environ["LLM_BASE_URL"] = ""
    os.environ["LLM_MODEL"] = ""

from app.db.session import Base, get_db
from app.main import app
import app.db.session as db_session
from app.core.config import settings


def main() -> None:
    args = _parse_args()
    if args.demo:
        settings.llm_api_key = ""
        settings.llm_base_url = ""
        settings.llm_model = ""

    source_dir = Path(args.source_dir)
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    db_path = report_dir / f"{args.name}.db"
    database_url = f"sqlite:///{db_path.as_posix()}"

    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    db_session.SessionLocal = TestingSessionLocal

    try:
        summary = run_report(TestClient(app), source_dir, args.limit, args.max_chapters)
    finally:
        app.dependency_overrides.clear()

    summary["database"] = str(db_path)
    summary["mode"] = "demo" if args.demo else "configured_llm"
    json_path = report_dir / f"{args.name}.json"
    md_path = report_dir / f"{args.name}.md"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_markdown(summary), encoding="utf-8")

    print(json.dumps({"json": str(json_path), "markdown": str(md_path), **summary["totals"]}, ensure_ascii=False))


def run_report(client: TestClient, source_dir: Path, limit: int, max_chapters: int) -> dict:
    books = sorted([path for path in source_dir.iterdir() if path.is_dir()])[:limit]
    results = []
    start_all = time.perf_counter()
    for book_dir in books:
        result = run_book(client, book_dir, max_chapters)
        results.append(result)

    elapsed = time.perf_counter() - start_all
    passed = [result for result in results if result["ok"]]
    seconds = [result["seconds"] for result in passed]
    scores = [result["score"] for result in passed if result["score"] is not None]
    totals = {
        "sample_size": len(results),
        "passed": len(passed),
        "failed": len(results) - len(passed),
        "total_seconds": round(elapsed, 3),
        "avg_seconds_per_book": round(statistics.mean(seconds), 3) if seconds else None,
        "max_seconds_per_book": round(max(seconds), 3) if seconds else None,
        "avg_yaml_chars": round(statistics.mean([result["yaml_chars"] for result in passed]), 1) if passed else None,
        "score_min": min(scores) if scores else None,
        "score_max": max(scores) if scores else None,
        "grades": {
            grade: sum(1 for result in passed if result["grade"] == grade)
            for grade in sorted({result["grade"] for result in passed})
        },
    }
    return {"totals": totals, "results": results}


def run_book(client: TestClient, book_dir: Path, max_chapters: int) -> dict:
    payload = _book_payload(book_dir, max_chapters)
    start = time.perf_counter()
    try:
        create_response = client.post("/api/v1/projects", json=payload)
        create_response.raise_for_status()
        project_id = create_response.json()["id"]

        analysis_response = client.post(f"/api/v1/projects/{project_id}/analysis-jobs")
        script_response = client.post(f"/api/v1/projects/{project_id}/script-jobs")
        yaml_response = client.get(f"/api/v1/projects/{project_id}/script")
        yaml_text = yaml_response.json()["yaml"]
        validate_response = client.post(f"/api/v1/projects/{project_id}/script/validate", json={"yaml": yaml_text})
        diagnosis_response = client.get(f"/api/v1/projects/{project_id}/script/diagnosis")
        workbench_response = client.get(f"/api/v1/projects/{project_id}/workbench")
        dashboard_response = client.get("/api/v1/projects/dashboard")
        library_response = client.get("/api/v1/scripts/library")
        export_response = client.get(f"/api/v1/projects/{project_id}/script/export")
        diagnosis = diagnosis_response.json()

        ok = all(
            response.status_code in {200, 201, 202}
            for response in [
                analysis_response,
                script_response,
                yaml_response,
                validate_response,
                diagnosis_response,
                workbench_response,
                dashboard_response,
                library_response,
                export_response,
            ]
        )
        return {
            "book": payload["title"],
            "project_id": project_id,
            "ok": ok,
            "chapters": len(payload["chapters"]),
            "seconds": round(time.perf_counter() - start, 3),
            "yaml_chars": len(yaml_text),
            "score": diagnosis.get("score"),
            "grade": diagnosis.get("grade"),
            "scene_count": diagnosis.get("summary", {}).get("scene_count"),
            "dialogue_count": diagnosis.get("summary", {}).get("dialogue_count"),
            "workbench_progress": workbench_response.json().get("progress", {}).get("percent"),
            "export_chars": len(export_response.text),
        }
    except Exception as exc:
        return {
            "book": payload["title"],
            "ok": False,
            "chapters": len(payload["chapters"]),
            "seconds": round(time.perf_counter() - start, 3),
            "error": str(exc),
            "yaml_chars": 0,
            "score": None,
            "grade": None,
        }


def _book_payload(book_dir: Path, max_chapters: int) -> dict:
    metadata_path = book_dir / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
    chapter_files = sorted((book_dir / "chapters").glob("*.txt"))[:max_chapters]
    chapters = []
    for index, chapter_file in enumerate(chapter_files, start=1):
        text = chapter_file.read_text(encoding="utf-8")
        lines = text.splitlines()
        title = lines[0].strip()[:80] if lines else f"第 {index} 章"
        body = "\n".join(lines[1:]).strip() or text.strip()
        chapters.append({"title": title or f"第 {index} 章", "content": body[:20000]})
    return {
        "title": metadata.get("title") or book_dir.name,
        "author": metadata.get("author"),
        "chapters": chapters,
    }


def _markdown(summary: dict) -> str:
    totals = summary["totals"]
    lines = [
        "# 小说后端全链路测试报告",
        "",
        f"- 模式：{summary['mode']}",
        f"- 样本数：{totals['sample_size']}",
        f"- 通过：{totals['passed']}",
        f"- 失败：{totals['failed']}",
        f"- 总耗时：{totals['total_seconds']}s",
        f"- 平均每本：{totals['avg_seconds_per_book']}s",
        f"- 平均 YAML 长度：{totals['avg_yaml_chars']}",
        f"- 诊断分数范围：{totals['score_min']} - {totals['score_max']}",
        f"- 诊断等级：{json.dumps(totals['grades'], ensure_ascii=False)}",
        f"- 临时数据库：{summary['database']}",
        "",
        "| 小说 | 章节 | 耗时(s) | YAML 字符 | 场景 | 对白 | 分数 | 等级 | 进度 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for result in summary["results"]:
        lines.append(
            "| {book} | {chapters} | {seconds} | {yaml_chars} | {scene_count} | {dialogue_count} | {score} | {grade} | {workbench_progress} |".format(
                book=result["book"],
                chapters=result["chapters"],
                seconds=result["seconds"],
                yaml_chars=result.get("yaml_chars", 0),
                scene_count=result.get("scene_count", ""),
                dialogue_count=result.get("dialogue_count", ""),
                score=result.get("score", ""),
                grade=result.get("grade", ""),
                workbench_progress=result.get("workbench_progress", ""),
            )
        )
    return "\n".join(lines) + "\n"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", default="data/test_novels_by_book")
    parser.add_argument("--report-dir", default="data/reports")
    parser.add_argument("--name", default="novel_flow_report")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--max-chapters", type=int, default=8)
    parser.add_argument("--demo", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    main()

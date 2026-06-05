from fastapi.testclient import TestClient

from app.main import app


def _payload(chapter_count: int = 3) -> dict:
    chapter_samples = [
        "话说天下大势，分久必合，合久必分。东汉末年，朝政日非，群雄渐起，刘备、关羽、张飞在乱世中相识。",
        "张飞庄后桃园花开正盛，刘备、关羽、张飞三人焚香再拜，约定同心协力，救困扶危，上报国家，下安黎庶。",
        "黄巾军势大，各地豪杰纷纷响应朝廷招募。刘备率新结义的兄弟投身战阵，开始踏入动荡的天下局势。",
    ]
    return {
        "title": "三国演义",
        "author": "罗贯中",
        "chapters": [
            {
                "title": f"第 {index} 章",
                "content": chapter_samples[index - 1] if index <= len(chapter_samples) else chapter_samples[-1],
            }
            for index in range(1, chapter_count + 1)
        ],
    }


def test_create_project_requires_three_chapters() -> None:
    client = TestClient(app)

    response = client.post("/api/v1/projects", json=_payload(2))

    assert response.status_code == 422
    assert "至少需要" in response.text


def test_create_project_and_generate_script() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    analysis_response = client.post(f"/api/v1/projects/{project_id}/analysis-jobs")
    assert analysis_response.status_code == 202
    analysis_job = client.get(f"/api/v1/jobs/{analysis_response.json()['id']}")
    assert analysis_job.json()["status"] == "succeeded"

    script_response = client.post(f"/api/v1/projects/{project_id}/script-jobs")
    assert script_response.status_code == 202
    script_job = client.get(f"/api/v1/jobs/{script_response.json()['id']}")
    assert script_job.json()["status"] == "succeeded"

    screenplay = client.get(f"/api/v1/projects/{project_id}/script")
    assert screenplay.status_code == 200
    assert "script:" in screenplay.json()["yaml"]

    validate_response = client.post(
        f"/api/v1/projects/{project_id}/script/validate",
        json={"yaml": screenplay.json()["yaml"]},
    )
    assert validate_response.status_code == 200
    assert validate_response.json() == {"valid": True, "errors": []}

    export_response = client.get(f"/api/v1/projects/{project_id}/script/export")
    assert export_response.status_code == 200
    assert "script:" in export_response.text

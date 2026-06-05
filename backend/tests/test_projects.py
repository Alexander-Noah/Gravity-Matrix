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


def test_get_analysis_requires_completed_analysis() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    response = client.get(f"/api/v1/projects/{project_id}/analysis")

    assert response.status_code == 404
    assert "还没有 AI 分析结果" in response.text


def test_create_project_and_generate_script() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    analysis_response = client.post(f"/api/v1/projects/{project_id}/analysis-jobs")
    assert analysis_response.status_code == 202
    analysis_job = client.get(f"/api/v1/jobs/{analysis_response.json()['id']}")
    assert analysis_job.json()["status"] == "succeeded"

    analysis = client.get(f"/api/v1/projects/{project_id}/analysis")
    assert analysis.status_code == 200
    assert analysis.json()["project_id"] == project_id
    assert analysis.json()["analysis"]["characters"]
    assert "id" in analysis.json()["analysis"]["characters"][0]
    assert len(analysis.json()["analysis"]["chapter_summaries"]) == 3

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

    edited_yaml = screenplay.json()["yaml"].replace("title: 三国演义", "title: 三国演义（作者修订版）", 1)
    save_response = client.put(f"/api/v1/projects/{project_id}/script", json={"yaml": edited_yaml})
    assert save_response.status_code == 200
    assert "作者修订版" in save_response.json()["yaml"]

    updated_screenplay = client.get(f"/api/v1/projects/{project_id}/script")
    assert updated_screenplay.status_code == 200
    assert "作者修订版" in updated_screenplay.json()["yaml"]

    export_response = client.get(f"/api/v1/projects/{project_id}/script/export")
    assert export_response.status_code == 200
    assert "作者修订版" in export_response.text


def test_save_script_rejects_invalid_yaml() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    script_response = client.post(f"/api/v1/projects/{project_id}/script-jobs")
    assert script_response.status_code == 202

    original = client.get(f"/api/v1/projects/{project_id}/script").json()["yaml"]
    save_response = client.put(f"/api/v1/projects/{project_id}/script", json={"yaml": "script: []"})

    assert save_response.status_code == 422
    assert "剧本 YAML 校验失败" in save_response.text
    assert client.get(f"/api/v1/projects/{project_id}/script").json()["yaml"] == original


def test_get_script_diagnosis_requires_generated_script() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    response = client.get(f"/api/v1/projects/{project_id}/script/diagnosis")

    assert response.status_code == 404
    assert "还没有生成剧本" in response.text


def test_get_script_diagnosis_returns_quality_report() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    script_response = client.post(f"/api/v1/projects/{project_id}/script-jobs")
    assert script_response.status_code == 202

    response = client.get(f"/api/v1/projects/{project_id}/script/diagnosis")

    assert response.status_code == 200
    report = response.json()
    assert report["project_id"] == project_id
    assert report["source"] == "stored_yaml"
    assert report["valid_schema"] is True
    assert 0 <= report["score"] <= 100
    assert report["grade"] in {"excellent", "good", "needs_work", "poor"}
    assert report["summary"]["chapter_count"] == 3
    assert report["summary"]["scene_count"] == 3
    assert report["summary"]["dialogue_count"] >= 0
    assert "YAML Schema 合法" in report["strengths"]
    assert isinstance(report["findings"], list)


def test_post_script_diagnosis_accepts_request_yaml() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    script_response = client.post(f"/api/v1/projects/{project_id}/script-jobs")
    assert script_response.status_code == 202
    yaml_text = client.get(f"/api/v1/projects/{project_id}/script").json()["yaml"]

    response = client.post(f"/api/v1/projects/{project_id}/script/diagnosis", json={"yaml": yaml_text})

    assert response.status_code == 200
    report = response.json()
    assert report["project_id"] == project_id
    assert report["source"] == "request_yaml"
    assert report["valid_schema"] is True
    assert report["summary"]["character_count"] >= 1


def test_post_script_diagnosis_reports_invalid_yaml_without_422() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    response = client.post(f"/api/v1/projects/{project_id}/script/diagnosis", json={"yaml": "script: []"})

    assert response.status_code == 200
    report = response.json()
    assert report["valid_schema"] is False
    assert report["grade"] == "invalid"
    assert report["score"] == 0
    assert report["summary"]["issue_count"] >= 1
    assert report["findings"][0]["severity"] == "error"


def test_script_diagnosis_returns_404_for_missing_project() -> None:
    client = TestClient(app)

    get_response = client.get("/api/v1/projects/999999/script/diagnosis")
    post_response = client.post("/api/v1/projects/999999/script/diagnosis", json={"yaml": "script: []"})

    assert get_response.status_code == 404
    assert post_response.status_code == 404

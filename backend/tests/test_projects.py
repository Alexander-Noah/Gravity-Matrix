import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes import projects as project_routes
from app.db.session import Base, get_db
from app.main import app


@pytest.fixture(autouse=True)
def isolated_database(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr("app.db.session.SessionLocal", TestingSessionLocal)
    try:
        yield
    finally:
        app.dependency_overrides.clear()


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


def _register_and_auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "测试创作者", "email": "creator@example.com", "password": "secret123"},
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_project_requires_three_chapters() -> None:
    client = TestClient(app)

    response = client.post("/api/v1/projects", json=_payload(2))

    assert response.status_code == 422
    assert "至少需要" in response.text


def test_import_preview_detects_chapters_and_readiness() -> None:
    client = TestClient(app)
    text = "\n\n".join(
        [
            "第1章 初入桃园\n刘备在街头遇见关羽，二人谈起天下局势。",
            "第2章 结义之约\n张飞邀二人到庄后桃园，三人焚香立誓。",
            "第3章 奔赴战场\n黄巾军起，三兄弟带着乡勇赶赴战阵。",
        ]
    )

    response = client.post(
        "/api/v1/import/preview",
        json={"title": "三国演义", "author": "罗贯中", "text": text},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "三国演义"
    assert payload["author"] == "罗贯中"
    assert payload["chapter_count"] == 3
    assert payload["can_create_project"] is True
    assert payload["issues"][0]["severity"] == "info"
    assert payload["chapters"][0]["title"] == "第1章 初入桃园"
    assert payload["chapters"][0]["content"]
    assert payload["chapters"][0]["char_count"] > 0
    assert payload["preprocess"]["chapter_summaries"][0]["title"] == "第1章 初入桃园"
    assert payload["preprocess"]["preparation_notes"]
    assert "local_preprocess" in payload["preprocess"]["chapter_summaries"][0]["source"]


def test_import_preview_reports_missing_chapters() -> None:
    client = TestClient(app)

    response = client.post("/api/v1/import/preview", json={"text": "只有一段没有章节标题的小说正文。"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["chapter_count"] == 0
    assert payload["can_create_project"] is False
    assert payload["issues"][0]["code"] == "not_enough_chapters"
    assert payload["preprocess"]["chapter_summaries"][0]["title"] == "全文"


def test_list_projects_returns_empty_page() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/projects")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": 20, "offset": 0}


def test_projects_dashboard_returns_empty_frontend_shape() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/projects/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert [stat["label"] for stat in payload["stats"]] == ["进行中项目", "已生成剧本", "待校验 YAML", "已导出文件"]
    assert payload["project_cards"] == []
    assert payload["activities"] == []


def test_scripts_library_returns_empty_frontend_shape() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/scripts/library")

    assert response.status_code == 200
    payload = response.json()
    assert payload["stats"][0]["label"] == "全部剧本"
    assert payload["stats"][0]["value"] == "0"
    assert payload["stats"][2]["label"] == "本地素材"
    assert int(payload["stats"][2]["value"]) >= 1
    assert payload["items"][0]["source_type"] == "source_novel"
    assert payload["items"][0]["source_id"]


def test_templates_endpoint_matches_latest_web_shape() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/templates")

    assert response.status_code == 200
    templates = response.json()
    assert {template["id"] for template in templates} >= {"tv-drama", "short-drama", "stage-play", "storyboard"}
    assert templates[0]["scenario"]
    assert templates[0]["features"]
    assert templates[0]["fields"]
    assert templates[0]["yamlExample"]


def test_template_center_backend_supports_filter_detail_and_default_template() -> None:
    client = TestClient(app)

    filtered_response = client.get("/api/v1/templates", params={"q": "短剧", "target_format": "short_drama"})
    assert filtered_response.status_code == 200
    assert [template["id"] for template in filtered_response.json()] == ["short-drama"]

    detail_response = client.get("/api/v1/templates/short-drama")
    assert detail_response.status_code == 200
    assert detail_response.json()["target_format"] == "short_drama"

    default_response = client.get("/api/v1/templates/default")
    assert default_response.status_code == 200
    assert default_response.json()["templateId"] == "tv-drama"

    update_response = client.put("/api/v1/templates/default", json={"templateId": "short-drama"})
    assert update_response.status_code == 200
    assert update_response.json()["template"]["id"] == "short-drama"
    assert client.get("/api/v1/templates/default").json()["templateId"] == "short-drama"

    invalid_response = client.put("/api/v1/templates/default", json={"templateId": "missing-template"})
    assert invalid_response.status_code == 404
    assert "模板不存在" in invalid_response.text


def test_profile_summary_requires_login() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/profile/summary")

    assert response.status_code == 403


def test_profile_summary_returns_empty_workspace_for_new_user() -> None:
    client = TestClient(app)
    headers = _register_and_auth_headers(client)

    response = client.get("/api/v1/profile/summary", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["user"] == {
        "id": 1,
        "name": "测试创作者",
        "email": "creator@example.com",
        "role": "创作者",
    }
    assert payload["stats"] == {
        "workspaceName": "AI 小说转剧本",
        "currentProject": "未创建项目",
        "projectProgress": 0,
        "workflowStep": "导入小说",
        "selectedTemplate": "影视剧剧本模板",
        "scriptStatus": "尚未生成剧本",
        "libraryCount": 0,
        "schemaStatus": "待校验",
    }


def test_profile_summary_uses_backend_project_script_and_template_data() -> None:
    client = TestClient(app)
    headers = _register_and_auth_headers(client)

    template_response = client.put("/api/v1/templates/default", json={"templateId": "short-drama"})
    assert template_response.status_code == 200

    create_response = client.post("/api/v1/projects", json={**_payload(), "title": "后端个人中心"})
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    script_response = client.post(f"/api/v1/projects/{project_id}/script-jobs")
    assert script_response.status_code == 202

    response = client.get("/api/v1/profile/summary", headers=headers)

    assert response.status_code == 200
    stats = response.json()["stats"]
    assert stats["workspaceName"] == "AI 小说转剧本"
    assert stats["currentProject"] == "《后端个人中心》改编项目"
    assert stats["projectProgress"] == 75
    assert stats["workflowStep"] == "编辑与导出"
    assert stats["selectedTemplate"] == "短剧剧本模板"
    assert stats["scriptStatus"] == "已有 YAML 草稿"
    assert stats["libraryCount"] == 1
    assert stats["schemaStatus"] == "校验通过"


def test_list_projects_returns_recent_projects_with_pagination() -> None:
    client = TestClient(app)

    first_response = client.post("/api/v1/projects", json={**_payload(), "title": "第一个项目"})
    second_response = client.post("/api/v1/projects", json={**_payload(), "title": "第二个项目"})
    third_response = client.post("/api/v1/projects", json={**_payload(), "title": "第三个项目"})
    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert third_response.status_code == 201

    response = client.get("/api/v1/projects", params={"limit": 2, "offset": 0})

    assert response.status_code == 200
    payload = response.json()
    assert payload["limit"] == 2
    assert payload["offset"] == 0
    assert payload["total"] == 3
    assert len(payload["items"]) == 2
    assert [item["id"] for item in payload["items"]] == sorted(
        [item["id"] for item in payload["items"]],
        reverse=True,
    )
    assert payload["items"][0]["title"] == "第三个项目"

    project = payload["items"][0]
    assert project["chapter_count"] == 3
    assert project["has_analysis"] is False
    assert project["has_script"] is False
    assert project["created_at"]
    assert project["updated_at"]

    next_page = client.get("/api/v1/projects", params={"limit": 1, "offset": 2})
    assert next_page.status_code == 200
    assert len(next_page.json()["items"]) == 1
    assert next_page.json()["items"][0]["id"] == first_response.json()["id"]


def test_list_projects_rejects_invalid_pagination() -> None:
    client = TestClient(app)

    invalid_limit = client.get("/api/v1/projects", params={"limit": 0})
    invalid_offset = client.get("/api/v1/projects", params={"offset": -1})

    assert invalid_limit.status_code == 422
    assert invalid_offset.status_code == 422


def test_update_project_renames_project() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    response = client.patch(f"/api/v1/projects/{project_id}", json={"title": "新的项目名"})

    assert response.status_code == 200
    assert response.json()["title"] == "新的项目名"


def test_update_project_rejects_blank_name() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    response = client.patch(f"/api/v1/projects/{project_id}", json={"name": "   "})

    assert response.status_code == 422
    assert "项目名称不能为空" in response.text


def test_delete_project_moves_project_to_recycle_bin() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]
    analysis_response = client.post(f"/api/v1/projects/{project_id}/analysis-jobs")
    assert analysis_response.status_code == 202

    response = client.delete(f"/api/v1/projects/{project_id}")

    assert response.status_code == 200
    assert response.json() == {"deleted": True, "project_id": project_id}
    assert client.get(f"/api/v1/projects/{project_id}").status_code == 404
    assert client.get("/api/v1/projects").json()["total"] == 0
    assert client.get(f"/api/v1/jobs/{analysis_response.json()['id']}").status_code == 200

    recycle_bin = client.get("/api/v1/projects/recycle-bin")
    assert recycle_bin.status_code == 200
    assert recycle_bin.json()["total"] == 1
    assert recycle_bin.json()["items"][0]["id"] == project_id
    assert recycle_bin.json()["items"][0]["deleted_at"]


def test_restore_project_from_recycle_bin() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]
    assert client.delete(f"/api/v1/projects/{project_id}").status_code == 200

    response = client.post(f"/api/v1/projects/{project_id}/restore")

    assert response.status_code == 200
    assert response.json()["id"] == project_id
    assert client.get(f"/api/v1/projects/{project_id}").status_code == 200
    assert client.get("/api/v1/projects/recycle-bin").json() == {"items": [], "total": 0}


def test_clear_recycle_bin_permanently_deletes_projects() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]
    analysis_response = client.post(f"/api/v1/projects/{project_id}/analysis-jobs")
    assert analysis_response.status_code == 202
    assert client.delete(f"/api/v1/projects/{project_id}").status_code == 200

    response = client.delete("/api/v1/projects/recycle-bin")

    assert response.status_code == 200
    assert response.json() == {"deleted": 1}
    assert client.get("/api/v1/projects/recycle-bin").json() == {"items": [], "total": 0}
    assert client.get(f"/api/v1/projects/{project_id}").status_code == 404
    assert client.get(f"/api/v1/jobs/{analysis_response.json()['id']}").status_code == 404


def test_get_analysis_requires_completed_analysis() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    response = client.get(f"/api/v1/projects/{project_id}/analysis")

    assert response.status_code == 404
    assert "还没有 AI 分析结果" in response.text


def test_get_workbench_returns_empty_analysis_and_script_for_new_project() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    response = client.get(f"/api/v1/projects/{project_id}/workbench")

    assert response.status_code == 200
    workbench = response.json()
    assert workbench["project"]["id"] == project_id
    assert workbench["project"]["has_analysis"] is False
    assert workbench["project"]["has_script"] is False
    assert workbench["workflow_steps"][0]["status"] == "done"
    assert workbench["workflow_steps"][1]["status"] == "current"
    assert workbench["progress"]["percent"] == 25
    assert workbench["analysis"]["raw"] is None
    assert workbench["analysis"]["overview"]["character_count"] == 0
    assert workbench["script"]["yaml"] is None
    assert workbench["script"]["structure"] == []
    assert workbench["script"]["diagnosis"] is None


def test_get_readiness_for_new_project_points_to_analysis() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    response = client.get(f"/api/v1/projects/{project_id}/readiness")

    assert response.status_code == 200
    readiness = response.json()
    assert readiness == {
        "project_id": project_id,
        "can_analyze": True,
        "can_generate_script": True,
        "can_export": False,
        "missing_steps": ["analysis", "script"],
        "next_action": "start_analysis",
    }


def test_start_analysis_job_reuses_active_job(monkeypatch) -> None:
    client = TestClient(app)
    monkeypatch.setattr(project_routes, "_run_analysis_job_task", lambda job_id: None)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    first_response = client.post(f"/api/v1/projects/{project_id}/analysis-jobs")
    second_response = client.post(f"/api/v1/projects/{project_id}/analysis-jobs")

    assert first_response.status_code == 202
    assert second_response.status_code == 202
    assert second_response.json()["id"] == first_response.json()["id"]
    assert second_response.json()["status"] == "queued"


def test_rerun_analysis_job_creates_new_job(monkeypatch) -> None:
    client = TestClient(app)
    monkeypatch.setattr(project_routes, "_run_analysis_job_task", lambda job_id: None)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]
    first_response = client.post(f"/api/v1/projects/{project_id}/analysis-jobs")

    response = client.post(f"/api/v1/projects/{project_id}/analysis-jobs/rerun")

    assert response.status_code == 202
    assert response.json()["id"] == response.json()["job_id"]
    assert response.json()["job_id"] != first_response.json()["id"]
    assert response.json()["status"] == "queued"
    assert response.json()["message"] == "重新解析任务已启动。"


def test_save_generation_settings_returns_saved_payload() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]
    settings = {"scriptType": "短剧", "contentOptions": ["保留对白", "强化冲突"]}

    response = client.post(f"/api/v1/projects/{project_id}/generation-settings", json=settings)

    assert response.status_code == 200
    assert response.json() == {"project_id": project_id, "settings": settings}


def test_create_project_and_generate_script() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    analysis_response = client.post(f"/api/v1/projects/{project_id}/analysis-jobs")
    assert analysis_response.status_code == 202
    analysis_job = client.get(f"/api/v1/jobs/{analysis_response.json()['id']}")
    assert analysis_job.json()["status"] == "succeeded"
    assert analysis_job.json()["current_step"] == "AI 解析完成"

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
    assert script_job.json()["current_step"] == "剧本生成完成"

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

    markdown_response = client.get(f"/api/v1/projects/{project_id}/script/export/markdown")
    assert markdown_response.status_code == 200
    assert markdown_response.headers["content-disposition"] == f'attachment; filename="project-{project_id}-screenplay.md"'
    assert "# 三国演义（作者修订版）" in markdown_response.text
    assert "## 人物" in markdown_response.text

    txt_response = client.get(f"/api/v1/projects/{project_id}/script/export/txt")
    assert txt_response.status_code == 200
    assert txt_response.headers["content-disposition"] == f'attachment; filename="project-{project_id}-screenplay.txt"'
    assert "三国演义（作者修订版）" in txt_response.text
    assert "人物" in txt_response.text

    pdf_response = client.get(f"/api/v1/projects/{project_id}/script/export/pdf")
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert pdf_response.headers["content-disposition"] == f'attachment; filename="project-{project_id}-screenplay.pdf"'
    assert pdf_response.content.startswith(b"%PDF-")


def test_export_script_pdf_returns_downloadable_pdf() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]
    assert client.post(f"/api/v1/projects/{project_id}/script-jobs").status_code == 202

    response = client.get(f"/api/v1/projects/{project_id}/script/export/pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == f'attachment; filename="project-{project_id}-screenplay.pdf"'
    assert response.content.startswith(b"%PDF-")
    assert b"%%EOF" in response.content


def test_frontend_extension_endpoints_support_latest_web_calls() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    settings_response = client.post(
        f"/api/v1/projects/{project_id}/generation-settings",
        json={
            "templateId": "short-drama",
            "scriptType": "短剧",
            "adaptationStyle": "忠于原文",
            "contentOptions": ["动作描写", "情绪提示"],
        },
    )
    assert settings_response.status_code == 200
    assert settings_response.json()["accepted"] is True

    update_response = client.patch(f"/api/v1/projects/{project_id}", json={"title": "改名后的三国项目"})
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "改名后的三国项目"

    clone_response = client.post(f"/api/v1/projects/{project_id}/clone")
    assert clone_response.status_code == 201
    assert clone_response.json()["id"] != project_id
    assert clone_response.json()["title"] == "改名后的三国项目 副本"
    assert clone_response.json()["chapter_count"] == 3

    rerun_response = client.post(f"/api/v1/projects/{project_id}/analysis-jobs/rerun")
    assert rerun_response.status_code == 202
    assert client.get(f"/api/v1/jobs/{rerun_response.json()['id']}").json()["status"] == "succeeded"

    script_response = client.post(f"/api/v1/projects/{project_id}/script-jobs")
    assert script_response.status_code == 202
    script_yaml = client.get(f"/api/v1/projects/{project_id}/script").json()["yaml"]
    assert "target_format: short_drama" in script_yaml
    assert "template_id: short-drama" in script_yaml

    markdown_response = client.get(f"/api/v1/projects/{project_id}/script/export/markdown")
    txt_response = client.get(f"/api/v1/projects/{project_id}/script/export/txt")
    assert markdown_response.status_code == 200
    assert txt_response.status_code == 200
    assert markdown_response.text.startswith("# ")
    assert "时间：" in txt_response.text

    add_scene_response = client.post(
        f"/api/v1/projects/{project_id}/scenes",
        json={
            "chapterTitle": "第 1 章",
            "sceneTitle": "新增对峙",
            "location": "桃园",
            "time": "夜晚",
            "characters": "刘备、关羽",
            "action": "刘备与关羽重新确认结义初心。",
        },
    )
    assert add_scene_response.status_code == 200
    assert "新增对峙" in add_scene_response.json()["yaml"]

    diagnosis_response = client.get(f"/api/v1/projects/{project_id}/script/diagnosis")
    assert diagnosis_response.status_code == 200
    assert diagnosis_response.json()["summary"]["scene_count"] == 4

    delete_response = client.delete(f"/api/v1/projects/{project_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"deleted": True, "project_id": project_id}
    assert client.get(f"/api/v1/projects/{project_id}").status_code == 404


def test_get_readiness_after_analysis_points_to_script_generation() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    analysis_response = client.post(f"/api/v1/projects/{project_id}/analysis-jobs")
    assert analysis_response.status_code == 202

    response = client.get(f"/api/v1/projects/{project_id}/readiness")

    assert response.status_code == 200
    readiness = response.json()
    assert readiness["can_analyze"] is True
    assert readiness["can_generate_script"] is True
    assert readiness["can_export"] is False
    assert readiness["missing_steps"] == ["script"]
    assert readiness["next_action"] == "generate_script"


def test_get_readiness_after_script_points_to_export() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    script_response = client.post(f"/api/v1/projects/{project_id}/script-jobs")
    assert script_response.status_code == 202

    response = client.get(f"/api/v1/projects/{project_id}/readiness")

    assert response.status_code == 200
    readiness = response.json()
    assert readiness["can_analyze"] is True
    assert readiness["can_generate_script"] is True
    assert readiness["can_export"] is True
    assert readiness["missing_steps"] == []
    assert readiness["next_action"] == "export_script"


def test_start_script_job_reuses_active_job(monkeypatch) -> None:
    client = TestClient(app)
    monkeypatch.setattr(project_routes, "_run_script_generation_job_task", lambda job_id: None)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    first_response = client.post(f"/api/v1/projects/{project_id}/script-jobs")
    second_response = client.post(f"/api/v1/projects/{project_id}/script-jobs")

    assert first_response.status_code == 202
    assert second_response.status_code == 202
    assert second_response.json()["id"] == first_response.json()["id"]
    assert second_response.json()["status"] == "queued"


def test_rerun_script_job_replaces_active_job(monkeypatch) -> None:
    client = TestClient(app)
    monkeypatch.setattr(project_routes, "_run_script_generation_job_task", lambda job_id: None)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    first_response = client.post(f"/api/v1/projects/{project_id}/script-jobs")
    rerun_response = client.post(f"/api/v1/projects/{project_id}/script-jobs/rerun")

    assert first_response.status_code == 202
    assert rerun_response.status_code == 202
    assert rerun_response.json()["id"] != first_response.json()["id"]

    old_job = client.get(f"/api/v1/jobs/{first_response.json()['id']}")
    assert old_job.status_code == 200
    assert old_job.json()["status"] == "failed"
    assert old_job.json()["current_step"] == "任务已取消"


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


def test_script_yaml_request_rejects_oversized_content() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/projects/{project_id}/script/validate",
        json={"yaml": "x" * 1_000_001},
    )

    assert response.status_code == 422
    assert "String should have at most 1000000 characters" in response.text


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


def test_get_workbench_after_analysis_returns_analysis_overview() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    analysis_response = client.post(f"/api/v1/projects/{project_id}/analysis-jobs")
    assert analysis_response.status_code == 202

    response = client.get(f"/api/v1/projects/{project_id}/workbench")

    assert response.status_code == 200
    workbench = response.json()
    assert workbench["project"]["has_analysis"] is True
    assert workbench["project"]["has_script"] is False
    assert workbench["workflow_steps"][1]["status"] == "done"
    assert workbench["workflow_steps"][2]["status"] == "current"
    assert workbench["progress"]["percent"] == 50
    assert workbench["analysis"]["raw"]["characters"]
    assert workbench["analysis"]["overview"]["chapter_summary_count"] == 3
    assert workbench["script"]["yaml"] is None


def test_get_workbench_after_script_returns_structure_and_diagnosis() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    script_response = client.post(f"/api/v1/projects/{project_id}/script-jobs")
    assert script_response.status_code == 202

    response = client.get(f"/api/v1/projects/{project_id}/workbench")

    assert response.status_code == 200
    workbench = response.json()
    assert workbench["project"]["has_script"] is True
    assert workbench["workflow_steps"][2]["status"] == "done"
    assert workbench["workflow_steps"][3]["status"] == "current"
    assert workbench["progress"]["percent"] == 75
    assert "script:" in workbench["script"]["yaml"]
    assert len(workbench["script"]["structure"]) == 3
    assert workbench["script"]["structure"][0]["open"] is True
    assert workbench["script"]["structure"][0]["scenes"]
    assert workbench["script"]["diagnosis"]["valid_schema"] is True


def test_dashboard_and_library_reflect_generated_script() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    analysis_response = client.post(f"/api/v1/projects/{project_id}/analysis-jobs")
    script_response = client.post(f"/api/v1/projects/{project_id}/script-jobs")
    assert analysis_response.status_code == 202
    assert script_response.status_code == 202

    dashboard_response = client.get("/api/v1/projects/dashboard")
    library_response = client.get("/api/v1/scripts/library")

    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()
    assert dashboard["stats"][1]["value"] == "1"
    assert dashboard["project_cards"][0]["id"] == project_id
    assert dashboard["project_cards"][0]["progress"] == 75
    assert dashboard["project_cards"][0]["scenes"] == 3
    assert dashboard["activities"][0]["status"] == "已完成"

    assert library_response.status_code == 200
    library = library_response.json()
    assert library["stats"][0]["value"] == "1"
    assert int(library["stats"][2]["value"]) >= 1
    assert library["items"][0]["project_id"] == project_id
    assert library["items"][0]["schemaStatus"] == "校验通过"
    assert library["items"][0]["scenes"] == 3
    assert library["items"][0]["dialogues"] >= 6


def test_import_source_novel_from_local_library() -> None:
    client = TestClient(app)

    library_response = client.get("/api/v1/scripts/library")
    assert library_response.status_code == 200
    source = next(item for item in library_response.json()["items"] if item["source_type"] == "source_novel")

    import_response = client.post(f"/api/v1/scripts/library/sources/{source['source_id']}/import")

    assert import_response.status_code == 201
    payload = import_response.json()
    assert payload["chapter_count"] >= 3
    assert payload["title"] in source["title"]


def test_get_workbench_returns_404_for_missing_project() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/projects/999999/workbench")

    assert response.status_code == 404


def test_get_readiness_returns_404_for_missing_project() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/projects/999999/readiness")

    assert response.status_code == 404


def test_preview_import_detects_chapters() -> None:
    client = TestClient(app)
    text = "\n".join(
        [
            "标题：测试小说",
            "第1章 初遇",
            "第一章正文。",
            "第2章 转折",
            "第二章正文。",
            "第3章 抉择",
            "第三章正文。",
        ]
    )

    response = client.post("/api/v1/import/preview", json={"text": text})

    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "测试小说"
    assert payload["chapter_count"] == 3
    assert payload["can_create_project"] is True
    assert payload["chapters"][0]["title"] == "第1章 初遇"
    assert payload["chapters"][0]["content"] == "第一章正文。"


def test_dashboard_and_script_library_return_backend_data() -> None:
    client = TestClient(app)
    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]
    assert client.post(f"/api/v1/projects/{project_id}/script-jobs").status_code == 202

    dashboard = client.get("/api/v1/projects/dashboard")
    library = client.get("/api/v1/scripts/library")

    assert dashboard.status_code == 200
    assert dashboard.json()["cards"][0]["id"] == project_id
    assert dashboard.json()["stats"][0]["label"] == "全部项目"
    assert library.status_code == 200
    assert library.json()["items"][0]["projectId"] == project_id
    assert library.json()["items"][0]["schemaStatus"] == "校验通过"


def test_templates_route_returns_generation_templates() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/templates")

    assert response.status_code == 200
    templates = response.json()
    assert {template["id"] for template in templates} >= {"tv-drama", "short-drama", "stage-play"}
    assert templates[0]["yamlExample"]


def test_clone_project_copies_chapters_and_script() -> None:
    client = TestClient(app)
    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]
    assert client.post(f"/api/v1/projects/{project_id}/script-jobs").status_code == 202

    clone_response = client.post(f"/api/v1/projects/{project_id}/clone")

    assert clone_response.status_code == 201
    clone = clone_response.json()
    assert clone["id"] != project_id
    assert clone["title"].endswith("副本")
    detail = client.get(f"/api/v1/projects/{clone['id']}")
    assert detail.status_code == 200
    assert len(detail.json()["chapters"]) == 3
    assert client.get(f"/api/v1/projects/{clone['id']}/script").status_code == 200


def test_add_scene_updates_saved_yaml() -> None:
    client = TestClient(app)
    create_response = client.post("/api/v1/projects", json=_payload())
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]
    assert client.post(f"/api/v1/projects/{project_id}/script-jobs").status_code == 202
    before = client.get(f"/api/v1/projects/{project_id}/script/diagnosis").json()

    response = client.post(
        f"/api/v1/projects/{project_id}/scenes",
        json={
            "chapterTitle": "桃园起义",
            "sceneTitle": "新增冲突场",
            "location": "桃园",
            "time": "夜晚",
            "characters": "刘备、关羽",
            "action": "刘备和关羽确认下一步行动。",
        },
    )

    assert response.status_code == 200
    assert "新增冲突场" in response.json()["yaml"]
    after = client.get(f"/api/v1/projects/{project_id}/script/diagnosis").json()
    assert after["summary"]["scene_count"] == before["summary"]["scene_count"] + 1

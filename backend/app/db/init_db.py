from app.db.session import Base, engine
from app.models import novel_script, project, user  # noqa: F401
from sqlalchemy import inspect, text


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_project_columns()
    _ensure_user_columns()
    _ensure_job_columns()


def _ensure_project_columns() -> None:
    inspector = inspect(engine)
    if "projects" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("projects")}
    missing_columns = []
    if "generation_settings_json" not in columns:
        missing_columns.append("ADD COLUMN generation_settings_json TEXT")
    if "deleted_at" not in columns:
        missing_columns.append("ADD COLUMN deleted_at DATETIME")

    if not missing_columns:
        return

    with engine.begin() as connection:
        for statement in missing_columns:
            connection.execute(text(f"ALTER TABLE projects {statement}"))


def _ensure_user_columns() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("users")}
    missing_columns = []
    if "llm_provider" not in columns:
        missing_columns.append("ADD COLUMN llm_provider VARCHAR(80)")
    if "llm_base_url" not in columns:
        missing_columns.append("ADD COLUMN llm_base_url VARCHAR(500)")
    if "llm_api_key" not in columns:
        missing_columns.append("ADD COLUMN llm_api_key TEXT")
    if "llm_model" not in columns:
        missing_columns.append("ADD COLUMN llm_model VARCHAR(255)")

    if not missing_columns:
        return

    with engine.begin() as connection:
        for statement in missing_columns:
            connection.execute(text(f"ALTER TABLE users {statement}"))


def _ensure_job_columns() -> None:
    inspector = inspect(engine)
    if "jobs" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("jobs")}
    if "llm_config_json" in columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE jobs ADD COLUMN llm_config_json TEXT"))

from app.db.session import Base, engine
from app.models import novel_script, project, user  # noqa: F401
from sqlalchemy import inspect, text


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_project_columns()


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

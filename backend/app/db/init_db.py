from app.db.session import Base, engine
from app.models import project  # noqa: F401
from sqlalchemy import inspect, text


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_generation_settings_column()


def _ensure_generation_settings_column() -> None:
    inspector = inspect(engine)
    if "projects" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("projects")}
    if "generation_settings_json" in columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE projects ADD COLUMN generation_settings_json TEXT"))

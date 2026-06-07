from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def _build_engine_kwargs(database_url: str) -> dict:
    kwargs: dict = {}

    if database_url.startswith("sqlite"):
        db_path = database_url.replace("sqlite:///", "", 1)
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs["pool_pre_ping"] = True
        kwargs["pool_recycle"] = 3600
        kwargs["pool_size"] = 10
        kwargs["max_overflow"] = 20

    return kwargs


engine = create_engine(settings.database_url, **_build_engine_kwargs(settings.database_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

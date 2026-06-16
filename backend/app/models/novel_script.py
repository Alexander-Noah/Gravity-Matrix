from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Novel(Base):
    __tablename__ = "novel"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    cleaned_content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    characters: Mapped[list["NovelCharacter"]] = relationship(
        back_populates="novel",
        cascade="all, delete-orphan",
        order_by="NovelCharacter.id",
    )
    scenes: Mapped[list["ScriptScene"]] = relationship(
        back_populates="novel",
        cascade="all, delete-orphan",
        order_by="ScriptScene.id",
    )
    yaml_scripts: Mapped[list["ScriptYaml"]] = relationship(
        back_populates="novel",
        cascade="all, delete-orphan",
        order_by="ScriptYaml.id",
    )


class NovelCharacter(Base):
    __tablename__ = "novel_character"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey("novel.id"), nullable=False, index=True)
    public_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    aliases_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    role: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    novel: Mapped[Novel] = relationship(back_populates="characters")


class ScriptScene(Base):
    __tablename__ = "script_scene"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey("novel.id"), nullable=False, index=True)
    public_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    chapter: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    time: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    atmosphere: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    characters_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_text: Mapped[str] = mapped_column(Text, nullable=False)

    novel: Mapped[Novel] = relationship(back_populates="scenes")
    contents: Mapped[list["SceneContent"]] = relationship(
        back_populates="scene",
        cascade="all, delete-orphan",
        order_by="SceneContent.id",
    )


class SceneContent(Base):
    __tablename__ = "scene_content"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scene_id: Mapped[int] = mapped_column(ForeignKey("script_scene.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor: Mapped[str | None] = mapped_column(String(120), nullable=True)
    speaker: Mapped[str | None] = mapped_column(String(120), nullable=True)
    emotion: Mapped[str | None] = mapped_column(String(120), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    need_review: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    scene: Mapped[ScriptScene] = relationship(back_populates="contents")


class ScriptYaml(Base):
    __tablename__ = "script_yaml"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey("novel.id"), nullable=False, index=True)
    yaml: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    novel: Mapped[Novel] = relationship(back_populates="yaml_scripts")

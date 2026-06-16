from pydantic import BaseModel, Field, model_validator


class ScriptMetadata(BaseModel):
    title: str
    original_novel: str
    author: str | None = None
    language: str = "zh-CN"
    target_format: str = "screenplay"
    template_id: str | None = None
    script_type: str | None = None
    adaptation_style: str | None = None
    total_chapters: int = Field(ge=3)


class Character(BaseModel):
    id: str
    name: str
    role: str
    gender: str = "unknown"
    age: int | None = None
    description: str


class Location(BaseModel):
    id: str
    name: str
    description: str


class DialogueLine(BaseModel):
    speaker_id: str | None = None
    speaker_name: str
    line: str
    emotion: str = "neutral"


class Scene(BaseModel):
    id: str
    title: str
    location_id: str
    time: str
    characters: list[str]
    synopsis: str
    stage_directions: list[str] = Field(default_factory=list)
    dialogue: list[DialogueLine] = Field(default_factory=list)


class ScriptChapter(BaseModel):
    id: str
    title: str
    source_chapter_numbers: list[int]
    summary: str
    scenes: list[Scene]


class AdaptationNotes(BaseModel):
    themes: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    omissions: list[str] = Field(default_factory=list)
    template_rules: list[str] = Field(default_factory=list)


class ScriptBody(BaseModel):
    schema_version: str = "1.0"
    metadata: ScriptMetadata
    characters: list[Character]
    locations: list[Location]
    chapters: list[ScriptChapter]
    adaptation_notes: AdaptationNotes = Field(default_factory=AdaptationNotes)

    @model_validator(mode="after")
    def validate_references(self) -> "ScriptBody":
        character_ids = {character.id for character in self.characters}
        location_ids = {location.id for location in self.locations}

        for chapter in self.chapters:
            if not chapter.scenes:
                raise ValueError(f"Chapter {chapter.id} must include at least one scene.")

            for scene in chapter.scenes:
                if scene.location_id not in location_ids:
                    raise ValueError(f"Scene {scene.id} references missing location {scene.location_id}.")

                missing_characters = [char_id for char_id in scene.characters if char_id not in character_ids]
                if missing_characters:
                    raise ValueError(
                        f"Scene {scene.id} references missing characters: {', '.join(missing_characters)}."
                    )

                for line in scene.dialogue:
                    if line.speaker_id is not None and line.speaker_id not in character_ids:
                        raise ValueError(
                            f"Dialogue in scene {scene.id} references missing speaker {line.speaker_id}."
                        )

        return self


class ScreenplayDocument(BaseModel):
    script: ScriptBody

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.novel_script import Novel, NovelCharacter, SceneContent, ScriptScene, ScriptYaml
from app.schemas.novel_script import (
    CharacterRead,
    CharactersResponse,
    CharactersSaveRequest,
    NovelCreateRequest,
    NovelCreateResponse,
    SceneContentResponse,
    SceneContentSaveRequest,
    SceneRead,
    ScenesResponse,
    ScenesSaveRequest,
    ScriptYamlSaveRequest,
    ScriptYamlSaveResponse,
    YamlResponse,
)
from app.services.novel_parser import (
    build_yaml,
    clean_text,
    extract_characters,
    extract_scenes,
    generate_scene_content,
    split_chapters,
)
from app.services.character_filter import canonicalize_character_list, filter_scene_character_names, normalize_speaker
from app.services.yaml_validator import validate_script_yaml

router = APIRouter(tags=["novel-script"])


@router.post("/novels", response_model=NovelCreateResponse, status_code=201)
def create_novel(payload: NovelCreateRequest, db: Session = Depends(get_db)) -> NovelCreateResponse:
    cleaned = clean_text(payload.content)
    chapters = split_chapters(cleaned)
    novel = Novel(title=payload.title.strip(), content=payload.content, cleaned_content=cleaned)
    db.add(novel)
    db.commit()
    db.refresh(novel)
    return NovelCreateResponse(novel_id=novel.id, title=novel.title, chapter_count=len(chapters))


@router.post("/novels/{novel_id}/extract-characters", response_model=CharactersResponse)
def extract_novel_characters(novel_id: int, db: Session = Depends(get_db)) -> CharactersResponse:
    novel = _require_novel(db, novel_id)
    try:
        characters = extract_characters(novel.cleaned_content)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    db.query(NovelCharacter).filter(NovelCharacter.novel_id == novel.id).delete()
    for character in characters:
        db.add(_character_model(novel.id, character))
    db.commit()
    return CharactersResponse(characters=characters)


@router.put("/novels/{novel_id}/characters", response_model=CharactersResponse)
def save_novel_characters(
    novel_id: int,
    payload: CharactersSaveRequest,
    db: Session = Depends(get_db),
) -> CharactersResponse:
    novel = _require_novel(db, novel_id)
    filtered_characters = [
        CharacterRead.model_validate(item)
        for item in canonicalize_character_list(
            [character.model_dump() for character in payload.characters],
            novel.cleaned_content,
        )
    ]
    db.query(NovelCharacter).filter(NovelCharacter.novel_id == novel_id).delete()
    for character in filtered_characters:
        db.add(_character_model(novel_id, character))
    db.commit()
    return CharactersResponse(characters=filtered_characters)


@router.post("/novels/{novel_id}/extract-scenes", response_model=ScenesResponse)
def extract_novel_scenes(novel_id: int, db: Session = Depends(get_db)) -> ScenesResponse:
    novel = _require_novel(db, novel_id)
    chapters = split_chapters(novel.cleaned_content)
    characters = [_character_to_read(item).model_dump() for item in novel.characters]
    scenes = extract_scenes(chapters, characters)

    db.query(ScriptScene).filter(ScriptScene.novel_id == novel.id).delete()
    for scene in scenes:
        db.add(_scene_model(novel.id, scene))
    db.commit()
    return ScenesResponse(scenes=scenes)


@router.put("/novels/{novel_id}/scenes", response_model=ScenesResponse)
def save_novel_scenes(
    novel_id: int,
    payload: ScenesSaveRequest,
    db: Session = Depends(get_db),
) -> ScenesResponse:
    novel = _require_novel(db, novel_id)
    character_pool = [_character_to_read(item).model_dump() for item in novel.characters]
    sanitized_scenes = []
    for scene in payload.scenes:
        scene_data = scene.model_dump()
        scene_data["characters"] = filter_scene_character_names(scene_data.get("characters") or [], character_pool)
        sanitized_scenes.append(SceneRead.model_validate(scene_data))

    existing = {
        scene.public_id: scene
        for scene in db.query(ScriptScene).filter(ScriptScene.novel_id == novel_id).all()
    }
    incoming_ids = {scene.id for scene in sanitized_scenes}

    for public_id, scene in existing.items():
        if public_id not in incoming_ids:
            db.delete(scene)

    for scene in sanitized_scenes:
        model = existing.get(scene.id)
        if model is None:
            db.add(_scene_model(novel_id, scene))
            continue

        model.chapter = scene.chapter
        model.title = scene.title
        model.location = scene.location
        model.time = scene.time
        model.atmosphere = scene.atmosphere
        model.characters_json = json.dumps(scene.characters, ensure_ascii=False)
        model.summary = scene.summary
        model.source_text = scene.source_text
    db.commit()
    return ScenesResponse(scenes=sanitized_scenes)


@router.post("/scenes/{scene_id}/generate-content", response_model=SceneContentResponse)
def generate_content_for_scene(scene_id: str, db: Session = Depends(get_db)) -> SceneContentResponse:
    scene = _require_scene(db, scene_id)
    characters = [_character_to_read(item).model_dump() for item in scene.novel.characters]
    content = [_sanitize_content_item(item, characters) for item in generate_scene_content(_scene_to_read(scene).model_dump(), characters)]

    db.query(SceneContent).filter(SceneContent.scene_id == scene.id).delete()
    for item in content:
        db.add(
            SceneContent(
                scene_id=scene.id,
                type=item.type,
                actor=item.actor,
                speaker=item.speaker or ("unknown" if item.type == "dialogue" else None),
                emotion=item.emotion,
                text=item.text,
                source_text=item.source_text,
                confidence=item.confidence,
                need_review=item.need_review,
            )
        )
    db.commit()
    return SceneContentResponse(content=content)


@router.put("/scenes/{scene_id}/content", response_model=SceneContentResponse)
def save_scene_content(
    scene_id: str,
    payload: SceneContentSaveRequest,
    db: Session = Depends(get_db),
) -> SceneContentResponse:
    scene = _require_scene(db, scene_id)
    character_pool = [_character_to_read(item).model_dump() for item in scene.novel.characters]
    sanitized_content = [_sanitize_content_item(item, character_pool) for item in payload.content]
    db.query(SceneContent).filter(SceneContent.scene_id == scene.id).delete()
    for item in sanitized_content:
        db.add(
            SceneContent(
                scene_id=scene.id,
                type=item.type,
                actor=item.actor,
                speaker=item.speaker or ("unknown" if item.type == "dialogue" else None),
                emotion=item.emotion,
                text=item.text,
                source_text=item.source_text,
                confidence=item.confidence,
                need_review=item.need_review,
            )
        )
    db.commit()
    return SceneContentResponse(content=sanitized_content)


@router.post("/novels/{novel_id}/generate-yaml", response_model=YamlResponse)
def generate_novel_yaml(novel_id: int, db: Session = Depends(get_db)) -> YamlResponse:
    novel = _require_novel(db, novel_id)
    characters = [_character_to_read(item).model_dump() for item in novel.characters]
    scenes = []
    for scene in novel.scenes:
        scene_data = _scene_to_read(scene).model_dump()
        scene_data["content"] = [_content_to_dict(item) for item in scene.contents]
        scenes.append(scene_data)

    yaml_text = build_yaml(novel.title, characters, scenes)
    valid, errors = validate_script_yaml(yaml_text)
    if not valid:
        raise HTTPException(status_code=422, detail={"message": "YAML Schema 校验失败", "errors": errors})

    script = novel.yaml_scripts[-1] if novel.yaml_scripts else None
    if script is None:
        script = ScriptYaml(novel_id=novel.id, yaml=yaml_text)
        db.add(script)
    else:
        script.yaml = yaml_text
    db.commit()
    db.refresh(script)
    return YamlResponse(yaml=yaml_text, script_id=script.id)


@router.put("/scripts/{script_id}", response_model=ScriptYamlSaveResponse)
def save_script_yaml(
    script_id: int,
    payload: ScriptYamlSaveRequest,
    db: Session = Depends(get_db),
) -> ScriptYamlSaveResponse:
    script = _require_script(db, script_id)
    valid, errors = validate_script_yaml(payload.yaml)
    if not valid:
        raise HTTPException(status_code=422, detail={"message": "YAML Schema 校验失败", "errors": errors})

    script.yaml = payload.yaml
    db.commit()
    db.refresh(script)
    return ScriptYamlSaveResponse(script_id=script.id, yaml=script.yaml)


@router.get("/scripts/{script_id}/download")
def download_script_yaml(script_id: int, db: Session = Depends(get_db)) -> Response:
    script = _require_script(db, script_id)
    filename = f"novel-script-{script.id}.yaml"
    return Response(
        content=script.yaml,
        media_type="application/x-yaml; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _require_novel(db: Session, novel_id: int) -> Novel:
    novel = db.get(Novel, novel_id)
    if novel is None:
        raise HTTPException(status_code=404, detail="小说不存在")
    return novel


def _require_scene(db: Session, scene_id: str) -> ScriptScene:
    scene = db.query(ScriptScene).filter(ScriptScene.public_id == scene_id).first()
    if scene is None:
        raise HTTPException(status_code=404, detail="场景不存在")
    return scene


def _require_script(db: Session, script_id: int) -> ScriptYaml:
    script = db.get(ScriptYaml, script_id)
    if script is None:
        raise HTTPException(status_code=404, detail="剧本 YAML 不存在")
    return script


def _character_model(novel_id: int, character: CharacterRead) -> NovelCharacter:
    return NovelCharacter(
        novel_id=novel_id,
        public_id=character.id,
        name=character.name,
        aliases_json=json.dumps(character.aliases, ensure_ascii=False),
        role=character.role,
        description=character.description,
        is_confirmed=character.is_confirmed,
    )


def _scene_model(novel_id: int, scene: SceneRead) -> ScriptScene:
    return ScriptScene(
        novel_id=novel_id,
        public_id=scene.id,
        chapter=scene.chapter,
        title=scene.title,
        location=scene.location,
        time=scene.time,
        atmosphere=scene.atmosphere,
        characters_json=json.dumps(scene.characters, ensure_ascii=False),
        summary=scene.summary,
        source_text=scene.source_text,
    )


def _character_to_read(character: NovelCharacter) -> CharacterRead:
    return CharacterRead(
        id=character.public_id,
        name=character.name,
        aliases=json.loads(character.aliases_json or "[]"),
        role=character.role,
        description=character.description,
        is_confirmed=character.is_confirmed,
    )


def _scene_to_read(scene: ScriptScene) -> SceneRead:
    return SceneRead(
        id=scene.public_id,
        chapter=scene.chapter,
        title=scene.title,
        location=scene.location,
        time=scene.time,
        atmosphere=scene.atmosphere,
        characters=json.loads(scene.characters_json or "[]"),
        summary=scene.summary,
        source_text=scene.source_text,
    )


def _content_to_dict(content: SceneContent) -> dict:
    data = {
        "type": content.type,
        "text": content.text,
        "source_text": content.source_text,
        "confidence": content.confidence,
        "need_review": content.need_review,
    }
    if content.actor:
        data["actor"] = content.actor
    if content.type == "dialogue":
        data["speaker"] = content.speaker or "unknown"
    elif content.speaker:
        data["speaker"] = content.speaker
    if content.emotion:
        data["emotion"] = content.emotion
    return data


def _sanitize_content_item(item: SceneContentRead, character_pool: list[dict]) -> SceneContentRead:
    data = item.model_dump()
    if data.get("type") == "dialogue":
        speaker = normalize_speaker(data.get("speaker"), character_pool)
        data["speaker"] = speaker or "\u65c1\u767d"
        if speaker is None:
            data["need_review"] = True
            data["confidence"] = min(float(data.get("confidence") or 0.5), 0.6)
    elif data.get("actor"):
        actor = normalize_speaker(data.get("actor"), character_pool)
        data["actor"] = actor
        if actor is None:
            data["need_review"] = True
            data["confidence"] = min(float(data.get("confidence") or 0.5), 0.6)
    return SceneContentRead.model_validate(data)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthLoginRequest,
    AuthRegisterRequest,
    AuthResponse,
    ProfileLlmConfigRead,
    ProfileLlmConfigUpdate,
    ProfileLlmTestRequest,
    ProfileLlmTestResponse,
    ProfileSummaryRead,
    UserRead,
)
from app.services.frontend_data import build_profile_summary
from app.api.routes.projects import FALLBACK_TEMPLATE_ID, SCRIPT_TEMPLATES
from app.services import llm as llm_service

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=AuthResponse, status_code=201)
def register(payload: AuthRegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该邮箱已注册，请直接登录。")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return AuthResponse(
        access_token=create_access_token(user.id),
        user=_user_to_read(user),
    )


@router.post("/auth/login", response_model=AuthResponse)
def login(payload: AuthLoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误。")

    return AuthResponse(
        access_token=create_access_token(user.id),
        user=_user_to_read(user),
    )


@router.get("/auth/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    return _user_to_read(current_user)


@router.get("/profile/llm-config", response_model=ProfileLlmConfigRead)
def get_profile_llm_config(current_user: User = Depends(get_current_user)) -> ProfileLlmConfigRead:
    return _llm_config_to_read(current_user)


@router.put("/profile/llm-config", response_model=ProfileLlmConfigRead)
def update_profile_llm_config(
    payload: ProfileLlmConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileLlmConfigRead:
    current_user.llm_provider = payload.provider.strip() or "openai_compatible"
    current_user.llm_base_url = payload.base_url.strip()
    current_user.llm_model = payload.model.strip()
    if payload.api_key is not None:
        current_user.llm_api_key = payload.api_key.strip() or None
    db.commit()
    db.refresh(current_user)
    return _llm_config_to_read(current_user)


@router.post("/profile/llm-config/test", response_model=ProfileLlmTestResponse)
def test_profile_llm_config(
    payload: ProfileLlmTestRequest,
    current_user: User = Depends(get_current_user),
) -> ProfileLlmTestResponse:
    llm_config = llm_service.build_user_llm_config(current_user)
    if llm_config is None:
        raise HTTPException(status_code=422, detail="请先填写 Base URL、模型名称和 API Key。")

    try:
        with llm_service.llm_config_context(llm_config):
            content = llm_service.call_model_text(payload.prompt)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"大模型连接失败：{exc}") from exc

    return ProfileLlmTestResponse(
        ok=True,
        provider=llm_config["provider"],
        model=llm_config["model"],
        content=content.strip() or "模型已返回空内容，请检查模型能力或提示词。",
    )


@router.get("/profile/summary", response_model=ProfileSummaryRead)
def get_profile_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileSummaryRead:
    template_names = {template.id: template.name for template in SCRIPT_TEMPLATES}
    return ProfileSummaryRead.model_validate(
        build_profile_summary(db, current_user, FALLBACK_TEMPLATE_ID, template_names)
    )


def _user_to_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        name=user.name,
        email=user.email,
        llm_configured=llm_service.is_user_llm_configured(user),
    )


def _llm_config_to_read(user: User) -> ProfileLlmConfigRead:
    return ProfileLlmConfigRead(
        provider=user.llm_provider or "openai_compatible",
        base_url=user.llm_base_url or "",
        model=user.llm_model or "",
        has_api_key=bool(user.llm_api_key),
        configured=llm_service.is_user_llm_configured(user),
    )

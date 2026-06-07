from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import AuthLoginRequest, AuthRegisterRequest, AuthResponse, ProfileSummaryRead, UserRead
from app.services.frontend_data import build_profile_summary
from app.api.routes.projects import FALLBACK_TEMPLATE_ID, SCRIPT_TEMPLATES

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
        user=UserRead.model_validate(user),
    )


@router.post("/auth/login", response_model=AuthResponse)
def login(payload: AuthLoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误。")

    return AuthResponse(
        access_token=create_access_token(user.id),
        user=UserRead.model_validate(user),
    )


@router.get("/auth/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.get("/profile/summary", response_model=ProfileSummaryRead)
def get_profile_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileSummaryRead:
    template_names = {template.id: template.name for template in SCRIPT_TEMPLATES}
    return ProfileSummaryRead.model_validate(
        build_profile_summary(db, current_user, FALLBACK_TEMPLATE_ID, template_names)
    )

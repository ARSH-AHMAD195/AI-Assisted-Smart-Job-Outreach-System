from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from models.user import User
from schemas.user import UserCreate
from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from config import settings


def register_user(db: Session, payload: UserCreate):
    existing = db.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        full_name=payload.full_name.lower(),
        email=payload.email,
        password_hash=hash_password(payload.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    tokens = _generate_tokens(user)

    return tokens, user


def login_user(db: Session, email: str, password: str):
    user = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()

    if not user or not verify_password(password, str(user.password_hash)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tokens = _generate_tokens(user)

    return tokens, user


def refresh_tokens(db: Session, refresh_token: str):
    token_data = decode_token(refresh_token, expected_type="refresh")

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    user = db.execute(
        select(User).where(User.user_id == token_data.sub)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    new_access_token = create_access_token(subject=str(user.user_id))

    new_refresh_token = (
        create_refresh_token(subject=str(user.user_id))
        if settings.get_settings().ROTATE_REFRESH_TOKENS
        else refresh_token
    )

    tokens = {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }

    return tokens, user


def _generate_tokens(user: User):
    return {
        "access_token": create_access_token(str(user.user_id)),
        "refresh_token": create_refresh_token(str(user.user_id)),
        "token_type": "bearer",
    }
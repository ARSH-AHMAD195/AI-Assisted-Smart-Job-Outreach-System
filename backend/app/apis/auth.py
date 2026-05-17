from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database.session import get_db
from schemas.user import (
    UserCreate,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse,
)
from services import auth_service

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    tokens, user = auth_service.register_user(db, payload)


    return TokenResponse(
        **tokens,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    tokens, user = auth_service.login_user(
        db,
        form_data.username,
        form_data.password
    )

    return TokenResponse(
        **tokens,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    tokens, user = auth_service.refresh_tokens(db, payload.refresh_token)

    return TokenResponse(
        **tokens,
        user=UserResponse.model_validate(user),
    )
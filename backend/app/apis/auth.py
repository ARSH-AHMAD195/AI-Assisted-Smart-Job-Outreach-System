import os
import urllib.parse
from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select
from authlib.integrations.starlette_client import OAuth

from app.database.session import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse,
)
from app.services import auth_service
from app.services.auth_service import _generate_tokens

router = APIRouter(prefix="/auth")

# Initialize and Register Google OAuth
oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@router.get("/login/google")
async def login_google(request: Request):
    # Dynamically reads the current base URL (local or Render production)
    backend_url = os.environ.get("BACKEND_URL")
    if backend_url:
        base_url = backend_url.rstrip("/")
    else:
        base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/auth/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/callback")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        backend_url = os.environ.get("BACKEND_URL")
        base_url = backend_url.rstrip("/") if backend_url else str(request.base_url).rstrip("/")
        error_msg = urllib.parse.quote(f"Google authentication failed: {str(e)}")
        return RedirectResponse(url=f"{base_url}/?error={error_msg}")
        
    user_info = token.get('userinfo')
    if not user_info:
        backend_url = os.environ.get("BACKEND_URL")
        base_url = backend_url.rstrip("/") if backend_url else str(request.base_url).rstrip("/")
        return RedirectResponse(url=f"{base_url}/?error=Could+not+retrieve+user+info+from+Google.")

    email = user_info.get("email")
    name = user_info.get("name")

    # 1. Check if user already exists
    user = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()

    # 2. If not, register/create user in the database
    if not user:
        user = User(
            full_name=name.lower() if name else email.split("@")[0].lower(),
            email=email,
            password_hash=None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 3. Generate tokens
    tokens = _generate_tokens(user)
    
    # 4. Redirect to frontend with query parameters containing tokens and user metadata
    backend_url = os.environ.get("BACKEND_URL")
    base_url = backend_url.rstrip("/") if backend_url else str(request.base_url).rstrip("/")
    
    redirect_query = urllib.parse.urlencode({
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "user_id": user.user_id,
        "email": email,
        "full_name": user.full_name
    })
    return RedirectResponse(url=f"{base_url}/?{redirect_query}")



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
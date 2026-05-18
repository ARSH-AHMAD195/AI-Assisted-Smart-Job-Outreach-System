from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from pydantic import BaseModel

from pwdlib import PasswordHash
from app.config import settings


# ----------- PASSWORD HASHING (ARGON2) -----------

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return password_hash.verify(plain, hashed)


# ----------- TOKEN SCHEMA -----------

class TokenData(BaseModel):
    sub: str   # user_id
    type: str  # "access" or "refresh"


# ----------- TOKEN CREATION -----------

def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.get_settings().ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": subject,
        "type": "access",
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.get_settings().SECRET_KEY,
        algorithm=settings.get_settings().ALGORITHM,
    )


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.get_settings().REFRESH_TOKEN_EXPIRE_DAYS
    )

    payload = {
        "sub": subject,
        "type": "refresh",
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.get_settings().SECRET_KEY,
        algorithm=settings.get_settings().ALGORITHM,
    )


# ----------- TOKEN DECODE -----------

def decode_token(token: str, expected_type: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(
            token,
            settings.get_settings().SECRET_KEY,
            algorithms=[settings.get_settings().ALGORITHM],
        )

        # Validate type
        sub = payload.get("sub")
        token_type = payload.get("type")

        if not sub or not isinstance(sub, str) or not token_type or not isinstance(token_type, str) or token_type != expected_type:
            return None

        return TokenData(
            sub=sub,
            type=token_type,
        )

    except JWTError:
        return None
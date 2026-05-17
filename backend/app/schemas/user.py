from uuid import UUID
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ----------- REQUEST SCHEMAS -----------

class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UpdateUserRequest(BaseModel):
    full_name: str
    linkedin_url: Optional[str] = ""
    github_url: Optional[str] = ""
    
# ----------- RESPONSE SCHEMAS -----------

class UserResponse(BaseModel):
    user_id: UUID
    full_name: str
    email: EmailStr
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from schemas.user import UserResponse, UpdateUserRequest
from database.session import get_db
from models.user import User
from dependencies import get_current_user

router = APIRouter(
    prefix="/users"
)

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=UserResponse)
def update_user(payload:UpdateUserRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = current_user

    update_data = payload.model_dump(exclude_unset=True)

    if "email" in update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email cannot be updated here.",
        )
    
    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return user

# @router.post("/resume")
# @router.get("/preferences")
# @router.get("/preferences")
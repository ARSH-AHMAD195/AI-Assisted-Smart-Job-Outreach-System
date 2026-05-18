from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies import get_current_user

from app.services import email_service

from app.schemas.email import (
    EmailGenerateRequest,
    EmailResponse,
    ApproveEmailRequest
)

router = APIRouter(prefix="/emails")

@router.get("/")
def get_all_emails(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    return email_service.get_all_emails_service(
        db=db,
        current_user=current_user
    )

@router.get("/{email_id}")
def get_email(
    email_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    return email_service.get_email_service(
        db=db,
        current_user=current_user,
        email_id=email_id
    )


@router.post("/generate")
def generate_email(
    payload: EmailGenerateRequest, 
    db: Session = Depends(get_db), 
    current_user=Depends(get_current_user)
):
    return email_service.generate(
        db=db, 
        current_user=current_user, 
        payload=payload
    )

@router.post("/{email_id}/send")
def send_generated_email(
    email_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    return email_service.send(
        db=db,
        current_user=current_user,
        email_id=email_id
    )


@router.post("/{email_id}/approve")
def approve_email(
    email_id: str,
    payload: ApproveEmailRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    return email_service.approve(
        db=db,
        current_user=current_user,
        email_id=email_id
    )

@router.delete("/{email_id}")
def delete_email(
    email_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    return email_service.delete_email_service(
        db=db,
        current_user=current_user,
        email_id=email_id
    )
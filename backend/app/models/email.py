import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    ForeignKey,
    DateTime
)

from sqlalchemy.sql import func

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database.session import Base
from datetime import datetime

class Email(Base):
    __tablename__ = "emails"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=str
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id"),
        nullable=False
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id"),
        nullable=False
    )

    subject: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String,
        default="draft"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    user = relationship("User")

    company = relationship("Company")
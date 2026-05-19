from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from app.database.session import Base
from datetime import datetime, timezone
import uuid

class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    linkedin_url = Column(String, default="")
    github_url = Column(String, default="")
    profile_data = Column(JSON, nullable=True)

    @property
    def id(self):
        return self.user_id
from pydantic import BaseModel, EmailStr, field_validator, model_validator, Field
from typing import List, Optional

class ResumeEntry(BaseModel):
    """
    Uniform structure for both Experience and Project entries.
    """
    title: str = "Unknown Role"
    organization: str = "Unknown Organization"
    duration: str = "N/A"
    description: List[str] = Field(default_factory=list)
    tech_stack: List[str] = Field(default_factory=list)

class UserProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    experience: List[ResumeEntry] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    projects: List[ResumeEntry] = Field(default_factory=list)

    @field_validator('age')
    @classmethod
    def validate_age(cls, value):
        if value is not None and not (0 <= value <= 120):
            raise ValueError('Age must be between 0–120')
        return value

    @field_validator('name')
    @classmethod
    def validate_name(cls, value):
        if value:
            cleaned = value.strip()
            if not cleaned:
                return None
            if len(cleaned) > 100:
                raise ValueError("Name too long")
            return cleaned
        return None

    @field_validator('skills', 'interests', 'languages', 'soft_skills', mode='before')
    @classmethod
    def normalize_lists(cls, value):
        if not isinstance(value, list):
            return []
        cleaned = []
        seen = set()
        for item in value:
            if isinstance(item, str):
                item = item.strip()
                if item and item.lower() not in seen:
                    cleaned.append(item.title())
                    seen.add(item.lower())
        return cleaned

    @model_validator(mode='after')
    def allow_empty_profile(self):
        return self

    def completeness_score(self) -> float:
        total_fields = 9
        filled = sum([
            bool(self.name),
            bool(self.email),
            self.age is not None,
            bool(self.skills),
            bool(self.soft_skills),
            bool(self.interests),
            bool(self.projects),
            bool(self.languages),
            bool(self.summary),
        ])
        return (filled / total_fields) * 100

class FinalUserProfile(BaseModel):
    name: str
    email: EmailStr
    age: Optional[int] = None
    phone: str
    address: str
    experience: List[ResumeEntry]
    education: List[str]
    certifications: List[str]
    languages: List[str]
    summary: Optional[str] = None
    skills: List[str]
    soft_skills: List[str]
    interests: List[str]
    projects: List[ResumeEntry]

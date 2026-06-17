"""Profile document."""
from datetime import date, datetime
from typing import Annotated, Any

from beanie import Document, Indexed, PydanticObjectId
from pydantic import BaseModel, EmailStr, Field

from cvapplier.utils.time import utcnow


class Location(BaseModel):
    city: str | None = None
    region: str | None = None
    country: str | None = None
    country_code: str | None = None


class WorkExperience(BaseModel):
    company: str
    title: str
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    current: bool = False
    description: str | None = None


class Education(BaseModel):
    institution: str
    degree: str | None = None
    field: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    gpa: str | None = None


class Certification(BaseModel):
    name: str
    issuer: str | None = None
    issue_date: date | None = None
    url: str | None = None
    expires_at: date | None = None


class LanguageLevel(BaseModel):
    name: str
    level: str


class Profile(Document):
    user_id: Annotated[PydanticObjectId, Indexed(unique=True)]
    source_cv_id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    location: Location = Field(default_factory=Location)
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    languages: list[LanguageLevel] = Field(default_factory=list)
    work_experience: list[WorkExperience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    custom_answers: dict[str, str] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "profiles"
        use_state_management = True

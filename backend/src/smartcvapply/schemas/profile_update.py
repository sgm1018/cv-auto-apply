from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from smartcvapply.schemas.profile_get import (
    CertificationDTO,
    EducationDTO,
    LanguageLevelDTO,
    LocationDTO,
    WorkExperienceDTO,
)


class ProfileUpdateRequest(BaseModel):
    source_cv_id: Optional[str] = None
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=40)
    location: Optional[LocationDTO] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    summary: Optional[str] = Field(default=None, max_length=2000)
    skills: Optional[list[str]] = None
    languages: Optional[list[LanguageLevelDTO]] = None
    work_experience: Optional[list[WorkExperienceDTO]] = None
    education: Optional[list[EducationDTO]] = None
    certifications: Optional[list[CertificationDTO]] = None
    custom_answers: Optional[dict[str, str]] = None

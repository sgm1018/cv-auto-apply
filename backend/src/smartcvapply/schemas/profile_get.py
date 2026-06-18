from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr


class LocationDTO(BaseModel):
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None


class WorkExperienceDTO(BaseModel):
    company: str
    title: str
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    current: bool = False
    description: Optional[str] = None


class EducationDTO(BaseModel):
    institution: str
    degree: Optional[str] = None
    field: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    gpa: Optional[str] = None


class CertificationDTO(BaseModel):
    name: str
    issuer: Optional[str] = None
    issue_date: Optional[date] = None
    url: Optional[str] = None
    expires_at: Optional[date] = None


class LanguageLevelDTO(BaseModel):
    name: str
    level: str


class ProfileResponse(BaseModel):
    user_id: str
    source_cv_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: LocationDTO = LocationDTO()
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    summary: Optional[str] = None
    skills: list[str] = []
    languages: list[LanguageLevelDTO] = []
    work_experience: list[WorkExperienceDTO] = []
    education: list[EducationDTO] = []
    certifications: list[CertificationDTO] = []
    custom_answers: dict[str, str] = {}

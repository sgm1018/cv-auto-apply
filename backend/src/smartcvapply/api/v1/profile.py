"""Profile endpoints."""
from fastapi import APIRouter, Depends

from smartcvapply.core.deps import get_current_user
from smartcvapply.core.exceptions import NotFoundError
from smartcvapply.models.user import User
from smartcvapply.repositories.cv_repository import CVRepository
from smartcvapply.schemas.profile_get import ProfileResponse
from smartcvapply.schemas.profile_update import ProfileUpdateRequest
from smartcvapply.services.onboarding_service import OnboardingService
from smartcvapply.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
async def get_profile(user: User = Depends(get_current_user)) -> ProfileResponse:
    p = await ProfileService().get(str(user.id))
    if p is None:
        raise NotFoundError("Profile not found")
    return _to_dto(p)


@router.patch("", response_model=ProfileResponse)
async def patch_profile(
    body: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
) -> ProfileResponse:
    patch = body.model_dump(exclude_unset=True)
    p = await ProfileService().update(str(user.id), patch)
    await OnboardingService().auto_check_all(str(user.id))
    return _to_dto(p)


@router.put("", response_model=ProfileResponse)
async def put_profile(
    body: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
) -> ProfileResponse:
    patch = body.model_dump(exclude_unset=True)
    p = await ProfileService().update(str(user.id), patch)
    await OnboardingService().auto_check_all(str(user.id))
    return _to_dto(p)


@router.put("/from-cv/{cv_id}", response_model=ProfileResponse)
async def load_from_cv(
    cv_id: str,
    user: User = Depends(get_current_user),
) -> ProfileResponse:
    cv = await CVRepository().get_for_user(str(user.id), cv_id)
    if cv is None:
        raise NotFoundError("CV not found")
    if not cv.parsed_data:
        raise NotFoundError("CV has not been parsed yet")
    patch = {k: v for k, v in cv.parsed_data.items() if v is not None}
    patch["source_cv_id"] = cv_id
    p = await ProfileService().update(str(user.id), patch)
    await OnboardingService().auto_check_all(str(user.id))
    return _to_dto(p)


def _to_dto(p) -> ProfileResponse:
    return ProfileResponse.model_validate(p.model_dump(mode="json"))

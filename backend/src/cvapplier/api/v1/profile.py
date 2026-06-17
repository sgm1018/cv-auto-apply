"""Profile endpoints."""
from fastapi import APIRouter, Depends

from cvapplier.core.deps import get_current_user
from cvapplier.core.exceptions import NotFoundError
from cvapplier.models.user import User
from cvapplier.schemas.profile_get import ProfileResponse
from cvapplier.schemas.profile_update import ProfileUpdateRequest
from cvapplier.services.profile_service import ProfileService

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
    return _to_dto(p)


@router.put("", response_model=ProfileResponse)
async def put_profile(
    body: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
) -> ProfileResponse:
    patch = body.model_dump(exclude_unset=True)
    p = await ProfileService().update(str(user.id), patch)
    return _to_dto(p)


def _to_dto(p) -> ProfileResponse:
    return ProfileResponse.model_validate(p.model_dump(mode="json"))

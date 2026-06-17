"""Users endpoints: GDPR export and delete."""
from fastapi import APIRouter, Depends

from cvapplier.core.deps import get_current_user
from cvapplier.models.user import User
from cvapplier.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/export")
async def export_me(user: User = Depends(get_current_user)) -> dict:
    return await UserService().export(str(user.id))


@router.delete("/me")
async def delete_me(user: User = Depends(get_current_user)) -> dict:
    await UserService().hard_delete(str(user.id))
    return {"ok": True}

"""Profile data access."""
from beanie import PydanticObjectId

from cvapplier.models.profile import Profile


class ProfileRepository:
    async def upsert(self, *, user_id: str, patch: dict) -> Profile:
        oid = PydanticObjectId(user_id)
        existing = await Profile.find_one(Profile.user_id == oid)
        if existing is None:
            p = Profile(user_id=oid, **patch)
            await p.insert()
            return p
        for k, v in patch.items():
            setattr(existing, k, v)
        await existing.save()
        return existing

    async def get_by_user(self, user_id: str) -> Profile | None:
        try:
            oid = PydanticObjectId(user_id)
        except Exception:
            return None
        return await Profile.find_one(Profile.user_id == oid)

    async def delete_by_user(self, user_id: str) -> None:
        p = await self.get_by_user(user_id)
        if p is not None:
            await p.delete()

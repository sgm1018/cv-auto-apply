"""Profile use cases."""
from smartcvapply.models.profile import Profile
from smartcvapply.repositories.profile_repository import ProfileRepository


class ProfileService:
    def __init__(self, repo: ProfileRepository | None = None) -> None:
        self.repo = repo or ProfileRepository()

    async def get(self, user_id: str) -> Profile | None:
        return await self.repo.get_by_user(user_id)

    async def update(self, user_id: str, patch: dict) -> Profile:
        return await self.repo.upsert(user_id=user_id, patch=patch)

    async def delete(self, user_id: str) -> None:
        await self.repo.delete_by_user(user_id)

"""User data access."""
from beanie import PydanticObjectId

from cvapplier.models.user import User


class UserRepository:
    async def create(self, *, email: str, password_hash: str, settings: dict) -> User:
        user = User(email=email.lower(), password_hash=password_hash, settings=settings)
        await user.insert()
        return user

    async def get_by_email(self, email: str) -> User | None:
        return await User.find_one(User.email == email.lower())

    async def get_by_id(self, user_id: str) -> User | None:
        try:
            oid = PydanticObjectId(user_id)
        except Exception:
            return None
        return await User.get(oid)

    async def set_refresh_hash(self, user_id: str, refresh_hash: str | None) -> None:
        user = await self.get_by_id(user_id)
        if user is not None:
            user.refresh_token_hash = refresh_hash
            await user.save()

    async def set_last_login(self, user_id: str) -> None:
        from cvapplier.utils.time import utcnow
        user = await self.get_by_id(user_id)
        if user is not None:
            user.last_login = utcnow()
            await user.save()

    async def update_settings(self, user_id: str, patch: dict) -> None:
        user = await self.get_by_id(user_id)
        if user is None:
            return
        user.settings = {**user.settings, **patch}
        await user.save()

    async def hard_delete(self, user_id: str) -> None:
        user = await self.get_by_id(user_id)
        if user is not None:
            await user.delete()

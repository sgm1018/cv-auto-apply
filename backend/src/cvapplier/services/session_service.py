"""SessionService: list and detail fill sessions."""
from cvapplier.models.fill_session import FillSession
from cvapplier.repositories.feedback_repository import FillSessionRepository


class SessionService:
    def __init__(self, repo: FillSessionRepository | None = None) -> None:
        self.repo = repo or FillSessionRepository()

    async def list_for_user(self, user_id: str, *, limit: int = 50) -> list[FillSession]:
        return await self.repo.list_for_user(user_id, limit=limit)

    async def get_for_user(self, user_id: str, session_id: str) -> FillSession | None:
        return await self.repo.get_for_user(user_id, session_id)

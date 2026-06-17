"""User GDPR: export and hard delete with cascade."""
from beanie import PydanticObjectId

from cvapplier.models.cv import CV
from cvapplier.models.feedback_event import FeedbackEvent
from cvapplier.models.fill_session import FillSession
from cvapplier.models.learned_mapping import LearnedMapping
from cvapplier.models.profile import Profile
from cvapplier.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository | None = None) -> None:
        self.user_repo = user_repo or UserRepository()

    async def export(self, user_id: str) -> dict:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            return {}
        oid = PydanticObjectId(user_id)
        profile = await Profile.find_one(Profile.user_id == oid)
        cvs = await CV.find(CV.user_id == oid).to_list()
        sessions = await FillSession.find(FillSession.user_id == oid).to_list()
        return {
            "user": user.model_dump(mode="json"),
            "profile": profile.model_dump(mode="json") if profile else None,
            "cvs": [c.model_dump(mode="json") for c in cvs],
            "sessions": [s.model_dump(mode="json") for s in sessions],
        }

    async def hard_delete(self, user_id: str) -> None:
        oid = PydanticObjectId(user_id)
        await Profile.find(Profile.user_id == oid).delete()
        await CV.find(CV.user_id == oid).delete()
        await FillSession.find(FillSession.user_id == oid).delete()
        await FeedbackEvent.find(FeedbackEvent.user_id == oid).delete()
        async for m in LearnedMapping.find():
            if m.user_count > 0:
                m.user_count -= 1
                await m.save()
        await self.user_repo.hard_delete(user_id)

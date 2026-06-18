"""FeedbackEvent and FillSession data access."""
from datetime import datetime
from typing import Any

from beanie import PydanticObjectId

from smartcvapply.models.feedback_event import FeedbackEvent
from smartcvapply.models.fill_session import FillSession


class FillSessionRepository:
    async def list_for_user(self, user_id: str, *, limit: int = 50) -> list[FillSession]:
        return await FillSession.find(
            FillSession.user_id == PydanticObjectId(user_id)
        ).sort("-started_at").limit(limit).to_list()

    async def get_for_user(self, user_id: str, session_id: str) -> FillSession | None:
        try:
            oid = PydanticObjectId(session_id)
        except Exception:
            return None
        s = await FillSession.get(oid)
        if s is None or str(s.user_id) != user_id:
            return None
        return s


class FeedbackRepository:
    async def insert_many(self, events: list[FeedbackEvent]) -> None:
        if events:
            await FeedbackEvent.insert_many(events)

    async def aggregate_since(self, user_id: PydanticObjectId | None,
                              *, since: datetime) -> list[dict[str, Any]]:
        match: dict[str, Any] = {"timestamp": {"$gte": since}}
        if user_id is not None:
            match["user_id"] = user_id
        pipeline = [
            {"$match": match},
            {
                "$group": {
                    "_id": {
                        "sig": "$field_signature",
                        "lang": "$language",
                        "action": "$action",
                    },
                    "count": {"$sum": 1},
                    "users": {"$addToSet": "$user_id"},
                }
            },
        ]
        return await FeedbackEvent.aggregate(pipeline).to_list()

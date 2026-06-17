"""Feedback batch endpoint."""
from fastapi import APIRouter, Depends

from cvapplier.core.deps import get_current_user
from cvapplier.models.feedback_event import FeedbackEvent
from cvapplier.models.user import User
from cvapplier.repositories.feedback_repository import FeedbackRepository
from cvapplier.schemas.feedback_batch import FeedbackBatchRequest, FeedbackBatchResponse

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/batch", response_model=FeedbackBatchResponse)
async def post_batch(
    body: FeedbackBatchRequest,
    user: User = Depends(get_current_user),
) -> FeedbackBatchResponse:
    events = [
        FeedbackEvent(
            user_id=user.id,
            session_id=None,
            field_signature=e.field_signature,
            language=e.language,
            source=e.source,
            action=e.action,
            suggested_hash=e.suggested_hash,
            actual_hash=e.actual_hash,
        )
        for e in body.events
    ]
    await FeedbackRepository().insert_many(events)
    return FeedbackBatchResponse(accepted=len(events))

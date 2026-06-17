"""Sessions list and detail."""
from fastapi import APIRouter, Depends, Query

from cvapplier.core.deps import get_current_user
from cvapplier.core.exceptions import NotFoundError
from cvapplier.models.user import User
from cvapplier.schemas.session_detail import SessionDetailResponse
from cvapplier.schemas.session_list import SessionListItem, SessionListResponse
from cvapplier.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
) -> SessionListResponse:
    items = await SessionService().list_for_user(str(user.id), limit=limit)
    return SessionListResponse(
        items=[_to_item(s) for s in items],
    )


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: str,
    user: User = Depends(get_current_user),
) -> SessionDetailResponse:
    s = await SessionService().get_for_user(str(user.id), session_id)
    if s is None:
        raise NotFoundError("Session not found")
    return SessionDetailResponse(
        session_id=str(s.id),
        user_id=str(s.user_id),
        domain=s.domain,
        started_at=s.started_at,
        ended_at=s.ended_at,
        total_fields=s.total_fields,
        resolved_local=s.resolved_local,
        resolved_backend=s.resolved_backend,
        resolved_llm=s.resolved_llm,
        user_edited=s.user_edited,
        failed=s.failed,
        submitted=s.submitted,
    )


def _to_item(s) -> SessionListItem:
    return SessionListItem(
        session_id=str(s.id),
        domain=s.domain,
        started_at=s.started_at,
        ended_at=s.ended_at,
        total_fields=s.total_fields,
        resolved_local=s.resolved_local,
        resolved_backend=s.resolved_backend,
        resolved_llm=s.resolved_llm,
        user_edited=s.user_edited,
        failed=s.failed,
    )

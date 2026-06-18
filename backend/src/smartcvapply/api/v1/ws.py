"""WebSocket /ws/fill endpoint with full MappingService cascade."""
import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from jose import JWTError

from smartcvapply.core.config import get_settings
from smartcvapply.core.security import decode_token
from smartcvapply.models.fill_session import FillSession
from smartcvapply.models.user import User
from smartcvapply.repositories.user_repository import UserRepository
from smartcvapply.services.heuristic_engine import ExtractedField
from smartcvapply.services.mapping_service import MappingService
from smartcvapply.schemas.ws_messages import (
    FillComplete,
    FillRequest,
    ProgressMsg,
)
from smartcvapply.utils.time import utcnow

router = APIRouter(tags=["ws"])


async def _authenticate(token: str) -> User | None:
    s = get_settings()
    try:
        payload = decode_token(token, secret=s.jwt_secret)
    except JWTError:
        return None
    if payload.get("type") != "access":
        return None
    return await UserRepository().get_by_id(payload["sub"])


@router.websocket("/ws/fill")
async def ws_fill(ws: WebSocket, token: str = Query(...)) -> None:
    user = await _authenticate(token)
    if not user:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await ws.accept()
    session = FillSession(user_id=user.id, domain="", url_hash="")
    await session.insert()
    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            if msg.get("type") == "FILL_REQUEST":
                req = FillRequest(**msg)
                session.domain = req.domain
                session.url_hash = req.url_hash
                session.total_fields = len(req.fields)
                await session.save()

                async def ws_send(p: ProgressMsg) -> None:
                    await ws.send_text(p.model_dump_json())

                fields = [
                    ExtractedField(
                        field_id=f.field_id,
                        label=f.label,
                        type=f.type,
                        name=f.name,
                        placeholder=f.placeholder,
                        required=f.required,
                        options=f.options,
                        current_value=f.current_value,
                        context=f.context,
                    )
                    for f in req.fields
                ]
                mapping, counts = await MappingService().resolve_batch(
                    user, fields, language=user.settings.get("language", "en"), ws_send=ws_send,
                )
                session.resolved_local = counts.resolved_local
                session.resolved_backend = counts.resolved_backend
                session.resolved_llm = counts.resolved_llm
                session.failed = counts.failed
                session.ended_at = utcnow()
                await session.save()
                await ws.send_text(FillComplete(
                    session_id=str(session.id), mapping=mapping,
                ).model_dump_json())
    except WebSocketDisconnect:
        session.ended_at = utcnow()
        await session.save()

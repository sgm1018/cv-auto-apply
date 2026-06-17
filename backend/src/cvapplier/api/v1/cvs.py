"""CV endpoints."""
import asyncio

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response

from cvapplier.core.deps import get_current_user
from cvapplier.core.exceptions import NotFoundError
from cvapplier.core.logging import get_logger
from cvapplier.models.cv import CV
from cvapplier.models.user import User
from cvapplier.repositories.cv_repository import CVRepository
from cvapplier.schemas.cv_metadata import CVMetadata
from cvapplier.schemas.cv_parse import CVParseResponse
from cvapplier.schemas.cv_upload import CVUploadResponse
from cvapplier.services.cv_parser_service import CVParserService
from cvapplier.services.cv_service import CVService
from cvapplier.services.profile_service import ProfileService
from cvapplier.services.settings_service import SettingsService
from cvapplier.utils.time import utcnow

log = get_logger(__name__)

router = APIRouter(prefix="/cvs", tags=["cvs"])


@router.post("", response_model=CVUploadResponse)
async def upload_cv(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
) -> CVUploadResponse:
    data = await file.read()
    cv = await CVService().upload(
        user_id=str(user.id),
        filename=file.filename or "cv.pdf",
        mime_type=file.content_type or "application/octet-stream",
        data=data,
    )
    return CVUploadResponse(
        cv_id=str(cv.id),
        parse_status=cv.parse_status,
        filename=cv.filename,
        size_bytes=cv.size_bytes,
    )


@router.get("", response_model=list[CVMetadata])
async def list_cvs(user: User = Depends(get_current_user)) -> list[CVMetadata]:
    items = await CVService().list(str(user.id))
    return [_meta(c) for c in items]


@router.get("/{cv_id}", response_model=CVMetadata)
async def get_cv(cv_id: str, user: User = Depends(get_current_user)) -> CVMetadata:
    cv = await CVRepository().get_for_user(str(user.id), cv_id)
    if cv is None:
        raise NotFoundError("CV not found")
    return _meta(cv)


@router.get("/{cv_id}/file")
async def download_cv(cv_id: str, user: User = Depends(get_current_user)) -> Response:
    try:
        data = await CVService().download(user_id=str(user.id), cv_id=cv_id)
    except FileNotFoundError as e:
        raise NotFoundError(str(e)) from e
    return Response(content=data, media_type="application/octet-stream")


@router.patch("/{cv_id}/primary")
async def set_primary(cv_id: str, user: User = Depends(get_current_user)) -> dict:
    repo = CVRepository()
    cv = await repo.get_for_user(str(user.id), cv_id)
    if cv is None:
        raise NotFoundError("CV not found")
    await CVService().set_primary(str(user.id), cv_id)
    # Auto-parse in background when set as primary
    if cv.parse_status in ("pending", "failed"):
        asyncio.create_task(_auto_parse_cv(cv, user))
    return {"ok": True}


@router.delete("/{cv_id}")
async def delete_cv(cv_id: str, user: User = Depends(get_current_user)) -> dict:
    await CVService().delete(user_id=str(user.id), cv_id=cv_id)
    return {"ok": True}


@router.post("/{cv_id}/parse", response_model=CVParseResponse)
async def parse_cv(cv_id: str, user: User = Depends(get_current_user)) -> CVParseResponse:
    repo = CVRepository()
    cv = await repo.get_for_user(str(user.id), cv_id)
    if cv is None:
        raise NotFoundError("CV not found")
    cv.parse_status = "processing"
    await cv.save()
    try:
        data = await CVService().download(user_id=str(user.id), cv_id=cv_id)
        text = CVParserService.extract_text(cv.mime_type, data)
        api_key = SettingsService().decrypt_api_key(user)
        parsed = await CVParserService.parse_with_llm(
            provider=user.settings.get("llm_provider", "deepseek"),
            model=user.settings.get("llm_model", "deepseek-chat"),
            api_key=api_key,
            api_base=user.settings.get("ollama_base_url") or user.settings.get("custom_endpoint"),
            text=text,
        )
        cv.parse_status = "done"
        cv.parsed_data = parsed
        cv.parsed_at = utcnow()
        await cv.save()
        # Auto-populate profile with parsed data
        patch = {k: v for k, v in parsed.items() if v is not None}
        patch["source_cv_id"] = str(cv.id)
        await ProfileService().update(str(user.id), patch)
        return CVParseResponse(
            cv_id=str(cv.id),
            parse_status="done",
            parsed_data=parsed,
        )
    except Exception as e:
        cv.parse_status = "failed"
        cv.parse_error = str(e)[:500]
        await cv.save()
        return CVParseResponse(
            cv_id=str(cv.id),
            parse_status="failed",
            parse_error=str(e)[:500],
        )


@router.post("/{cv_id}/confirm")
async def confirm_parse(cv_id: str, user: User = Depends(get_current_user)) -> dict:
    repo = CVRepository()
    cv = await repo.get_for_user(str(user.id), cv_id)
    if cv is None:
        raise NotFoundError("CV not found")
    if not cv.parsed_data:
        raise NotFoundError("CV has not been parsed yet")
    patch = {k: v for k, v in cv.parsed_data.items() if v is not None}
    await ProfileService().update(str(user.id), patch)
    return {"ok": True}


async def _auto_parse_cv(cv: CV, user: User) -> None:
    """Background task: parse a CV and update its status."""
    cv.parse_status = "processing"
    await cv.save()
    try:
        data = await CVService().download(user_id=str(user.id), cv_id=str(cv.id))
        text = CVParserService.extract_text(cv.mime_type, data)
        api_key = SettingsService().decrypt_api_key(user)
        parsed = await CVParserService.parse_with_llm(
            provider=user.settings.get("llm_provider", "deepseek"),
            model=user.settings.get("llm_model", "deepseek-chat"),
            api_key=api_key,
            api_base=user.settings.get("ollama_base_url") or user.settings.get("custom_endpoint"),
            text=text,
        )
        cv.parse_status = "done"
        cv.parsed_data = parsed
        cv.parsed_at = utcnow()
        await cv.save()
        # Auto-populate profile with parsed data
        patch = {k: v for k, v in parsed.items() if v is not None}
        patch["source_cv_id"] = str(cv.id)
        await ProfileService().update(str(user.id), patch)
        log.info("cv_parsed", cv_id=str(cv.id), fields=len(parsed))
    except Exception as e:
        cv.parse_status = "failed"
        cv.parse_error = str(e)[:500]
        await cv.save()
        log.warning("cv_parse_failed", cv_id=str(cv.id), error=str(e)[:200])



def _meta(c) -> CVMetadata:
    return CVMetadata(
        cv_id=str(c.id),
        filename=c.filename,
        mime_type=c.mime_type,
        size_bytes=c.size_bytes,
        is_primary=c.is_primary,
        parse_status=c.parse_status,
        parse_error=c.parse_error,
        uploaded_at=c.uploaded_at,
        parsed_at=c.parsed_at,
    )

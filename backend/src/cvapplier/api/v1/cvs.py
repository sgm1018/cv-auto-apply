"""CV endpoints."""
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response

from cvapplier.core.deps import get_current_user
from cvapplier.core.exceptions import NotFoundError
from cvapplier.models.user import User
from cvapplier.repositories.cv_repository import CVRepository
from cvapplier.schemas.cv_metadata import CVMetadata
from cvapplier.schemas.cv_upload import CVUploadResponse
from cvapplier.services.cv_service import CVService

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
    if await repo.get_for_user(str(user.id), cv_id) is None:
        raise NotFoundError("CV not found")
    await CVService().set_primary(str(user.id), cv_id)
    return {"ok": True}


@router.delete("/{cv_id}")
async def delete_cv(cv_id: str, user: User = Depends(get_current_user)) -> dict:
    await CVService().delete(user_id=str(user.id), cv_id=cv_id)
    return {"ok": True}


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

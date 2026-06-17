"""CV data access."""
from beanie import PydanticObjectId

from cvapplier.models.cv import CV


class CVRepository:
    async def create(self, *, user_id: str, file_id: str, filename: str,
                     mime_type: str, size_bytes: int) -> CV:
        cv = CV(
            user_id=PydanticObjectId(user_id),
            file_id=file_id,
            filename=filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
        )
        await cv.insert()
        return cv

    async def get_for_user(self, user_id: str, cv_id: str) -> CV | None:
        try:
            oid = PydanticObjectId(cv_id)
        except Exception:
            return None
        cv = await CV.get(oid)
        if cv is None or str(cv.user_id) != user_id:
            return None
        return cv

    async def list_for_user(self, user_id: str) -> list[CV]:
        return await CV.find(CV.user_id == PydanticObjectId(user_id)).to_list()

    async def set_primary(self, user_id: str, cv_id: str) -> None:
        items = await self.list_for_user(user_id)
        for cv in items:
            cv.is_primary = str(cv.id) == cv_id
            await cv.save()

    async def set_status(self, cv_id: str, *, status: str,
                         parsed_data: dict | None = None,
                         parse_error: str | None = None) -> None:
        from cvapplier.utils.time import utcnow
        cv = await CV.get(PydanticObjectId(cv_id))
        if cv is None:
            return
        cv.parse_status = status  # type: ignore[assignment]
        if parsed_data is not None:
            cv.parsed_data = parsed_data
        if parse_error is not None:
            cv.parse_error = parse_error
        if status == "done":
            cv.parsed_at = utcnow()
        await cv.save()

    async def delete(self, user_id: str, cv_id: str) -> CV | None:
        cv = await self.get_for_user(user_id, cv_id)
        if cv is not None:
            await cv.delete()
        return cv

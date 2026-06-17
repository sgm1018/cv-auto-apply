"""CV use cases: upload with encryption, parse, list, download, delete."""
import os

from cvapplier.core.config import get_settings
from cvapplier.core.storage import ObjectStorage
from cvapplier.models.cv import CV
from cvapplier.repositories.cv_repository import CVRepository
from cvapplier.services.encryption import (
    decrypt_cv_bytes,
    derive_cv_key,
    encrypt_cv_bytes,
)


class CVService:
    MAX_BYTES = 10 * 1024 * 1024

    def __init__(
        self, repo: CVRepository | None = None, storage: ObjectStorage | None = None,
    ) -> None:
        self.repo = repo or CVRepository()
        self.storage = storage or ObjectStorage()

    @staticmethod
    def _suffix_for(mime_type: str) -> str:
        return {
            "application/pdf": ".pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        }.get(mime_type, ".bin")

    @staticmethod
    def _storage_key(user_id: str, file_id: str, suffix: str) -> str:
        return f"cvs/{user_id}/{file_id}{suffix}"

    def _key(self, user_id: str) -> bytes:
        s = get_settings()
        return derive_cv_key(master_key=s.cv_master_key, user_id=user_id)

    async def upload(self, *, user_id: str, filename: str, mime_type: str,
                     data: bytes) -> CV:
        if len(data) > self.MAX_BYTES:
            raise ValueError(f"CV exceeds max size of {self.MAX_BYTES} bytes")
        file_id = os.urandom(16).hex()
        suffix = self._suffix_for(mime_type)
        encrypted = encrypt_cv_bytes(data, key=self._key(user_id))
        await self.storage.put_bytes(
            key=self._storage_key(user_id, file_id, suffix),
            data=encrypted,
            content_type=mime_type,
        )
        return await self.repo.create(
            user_id=user_id, file_id=file_id,
            filename=filename, mime_type=mime_type, size_bytes=len(data),
        )

    async def download(self, *, user_id: str, cv_id: str) -> bytes:
        cv = await self.repo.get_for_user(user_id, cv_id)
        if cv is None:
            raise FileNotFoundError(cv_id)
        suffix = self._suffix_for(cv.mime_type)
        blob = await self.storage.get_bytes(
            key=self._storage_key(user_id, cv.file_id, suffix),
        )
        return decrypt_cv_bytes(blob, key=self._key(user_id))

    async def delete(self, *, user_id: str, cv_id: str) -> None:
        cv = await self.repo.delete(user_id, cv_id)
        if cv is None:
            return
        suffix = self._suffix_for(cv.mime_type)
        try:
            await self.storage.delete(key=self._storage_key(user_id, cv.file_id, suffix))
        except Exception:
            pass

    async def list(self, user_id: str) -> list[CV]:
        return await self.repo.list_for_user(user_id)

    async def set_primary(self, user_id: str, cv_id: str) -> None:
        await self.repo.set_primary(user_id, cv_id)

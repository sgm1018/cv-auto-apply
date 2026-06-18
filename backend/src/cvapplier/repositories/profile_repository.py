"""Profile data access."""
from beanie import PydanticObjectId

from cvapplier.models.profile import (
    Certification,
    Education,
    LanguageLevel,
    Location,
    Profile,
    WorkExperience,
)


class ProfileRepository:
    async def upsert(self, *, user_id: str, patch: dict) -> Profile:
        oid = PydanticObjectId(user_id)
        existing = await Profile.find_one(Profile.user_id == oid)
        if existing is None:
            patch = _coerce_nested(patch)
            p = Profile(user_id=oid, **patch)
            await p.insert()
            return p
        patch = _coerce_nested(patch)
        for k, v in patch.items():
            setattr(existing, k, v)
        await existing.save()
        return existing

    async def get_by_user(self, user_id: str) -> Profile | None:
        try:
            oid = PydanticObjectId(user_id)
        except Exception:
            return None
        return await Profile.find_one(Profile.user_id == oid)

    async def delete_by_user(self, user_id: str) -> None:
        p = await self.get_by_user(user_id)
        if p is not None:
            await p.delete()


_NESTED_COERCIONS: dict[str, type] = {
    "work_experience": WorkExperience,
    "education": Education,
    "certifications": Certification,
    "languages": LanguageLevel,
}


def _coerce_nested(patch: dict) -> dict:
    out = dict(patch)
    for key, model in _NESTED_COERCIONS.items():
        if key in out and isinstance(out[key], list):
            out[key] = [
                model(**item) if isinstance(item, dict) else item
                for item in out[key]
            ]
    if "location" in out and isinstance(out["location"], dict):
        out["location"] = Location(**out["location"])
    return out

"""LearnedMapping data access."""
from datetime import timedelta

from smartcvapply.models.learned_mapping import LearnedMapping
from smartcvapply.utils.time import utcnow


class LearnedMappingRepository:
    async def lookup(self, signatures: list[str], *, language: str) -> dict[str, LearnedMapping]:
        if not signatures:
            return {}
        cursor = LearnedMapping.find({
            "field_signature": {"$in": signatures},
            "language": language,
        })
        items = await cursor.to_list()
        return {m.field_signature: m for m in items}

    async def upsert(self, *, field_signature: str, language: str, target_path: str,
                     transform: str | None = None, confidence: float = 0.85,
                     source: str = "user_confirmed",
                     user_count: int = 0, usage_count: int = 0) -> LearnedMapping:
        existing = await LearnedMapping.find_one(
            LearnedMapping.field_signature == field_signature,
            LearnedMapping.language == language,
        )
        if existing is None:
            m = LearnedMapping(
                field_signature=field_signature,
                language=language,
                target_path=target_path,
                transform=transform,
                confidence=confidence,
                source=source,
                user_count=user_count,
                usage_count=usage_count,
            )
            await m.insert()
            return m
        existing.target_path = target_path
        existing.transform = transform
        existing.confidence = confidence
        existing.source = source
        existing.user_count += user_count
        existing.usage_count += usage_count
        existing.last_used_at = utcnow()
        await existing.save()
        return existing

    async def decay_unused(self, *, threshold_days: int = 30) -> int:
        cutoff = utcnow() - timedelta(days=threshold_days)
        cursor = LearnedMapping.find(LearnedMapping.last_used_at < cutoff)
        count = 0
        async for m in cursor:
            m.confidence *= 0.95
            m.usage_count = int(m.usage_count * 0.95)
            if m.confidence < 0.5:
                await m.delete()
            else:
                await m.save()
            count += 1
        return count

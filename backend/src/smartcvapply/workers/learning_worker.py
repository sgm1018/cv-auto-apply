"""Learning aggregation worker: promotes confirmed mappings, decays unused ones."""
import asyncio
from collections import defaultdict
from datetime import timedelta

from smartcvapply.core.db import create_mongo_client, init_beanie
from smartcvapply.core.logging import configure_logging, get_logger
from smartcvapply.models import FeedbackEvent, LearnedMapping
from smartcvapply.repositories.learned_mapping_repository import LearnedMappingRepository
from smartcvapply.utils.time import utcnow

log = get_logger(__name__)
PROMOTION_THRESHOLD = 3
EDIT_RATIO_LIMIT = 0.3


async def aggregate_and_promote() -> int:
    cutoff = utcnow() - timedelta(days=7)
    buckets: dict[tuple[str, str], dict[str, dict]] = defaultdict(dict)
    pipeline = [
        {"$match": {"timestamp": {"$gte": cutoff}}},
        {
            "$group": {
                "_id": {"sig": "$field_signature", "lang": "$language", "action": "$action"},
                "count": {"$sum": 1},
                "users": {"$addToSet": "$user_id"},
            }
        },
    ]
    async for b in FeedbackEvent.aggregate(pipeline):
        sig = b["_id"]["sig"]
        lang = b["_id"]["lang"]
        buckets[(sig, lang)][b["_id"]["action"]] = b

    promoted = 0
    repo = LearnedMappingRepository()
    for (sig, lang), acts in buckets.items():
        confirmed = acts.get("confirmed", {}).get("count", 0)
        edited = acts.get("edited", {}).get("count", 0)
        rejected = acts.get("rejected", {}).get("count", 0)
        if confirmed < PROMOTION_THRESHOLD:
            continue
        if edited + rejected == 0:
            users = len(acts["confirmed"].get("users", []))
            confidence = min(0.85 + 0.01 * confirmed, 0.98)
            existing = await LearnedMapping.find_one(
                LearnedMapping.field_signature == sig,
                LearnedMapping.language == lang,
            )
            target_path = existing.target_path if existing else sig
            await repo.upsert(
                field_signature=sig, language=lang, target_path=target_path,
                confidence=confidence, source="user_confirmed",
                user_count=users, usage_count=confirmed,
            )
            promoted += 1
        elif confirmed > 0 and edited / confirmed > EDIT_RATIO_LIMIT:
            log.info("candidate_mapping_needs_review", sig=sig, lang=lang,
                     confirmed=confirmed, edited=edited)
    return promoted


async def main() -> None:
    configure_logging()
    client = create_mongo_client()
    await init_beanie(client, document_models=[LearnedMapping, FeedbackEvent])
    while True:
        try:
            promoted = await aggregate_and_promote()
            decayed = await LearnedMappingRepository().decay_unused()
            log.info("learning_tick", promoted=promoted, decayed=decayed)
        except Exception as e:
            log.error("learning_tick_failed", error=str(e))
        await asyncio.sleep(300)


if __name__ == "__main__":
    asyncio.run(main())

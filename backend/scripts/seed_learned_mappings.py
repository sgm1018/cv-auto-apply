"""Seed curated learned_mappings catalog for cold start."""
import asyncio

from smartcvapply.core.db import create_mongo_client, init_beanie
from smartcvapply.core.logging import configure_logging
from smartcvapply.models.learned_mapping import LearnedMapping
from smartcvapply.repositories.learned_mapping_repository import LearnedMappingRepository

CATALOG: list[tuple[str, str, str, str]] = [
    # (signature, language, target_path, transform)
    ("first name", "en", "first_name", ""),
    ("last name", "en", "last_name", ""),
    ("full name", "en", "first_name", ""),
    ("email", "en", "email", ""),
    ("phone", "en", "phone", "phone_e164"),
    ("linkedin", "en", "linkedin_url", ""),
    ("github", "en", "github_url", ""),
    ("portfolio", "en", "portfolio_url", ""),
    ("summary", "en", "summary", ""),
    ("city", "en", "location.city", ""),
    ("country", "en", "location.country", ""),
    ("current company", "en", "work_experience[0].company", ""),
    ("current title", "en", "work_experience[0].title", ""),
    # Spanish variants
    ("nombre", "es", "first_name", ""),
    ("apellido", "es", "last_name", ""),
    ("apellidos", "es", "last_name", ""),
    ("correo electronico", "es", "email", ""),
    ("telefono", "es", "phone", "phone_e164"),
    ("movil", "es", "phone", "phone_e164"),
    ("url linkedin", "es", "linkedin_url", ""),
    ("ciudad", "es", "location.city", ""),
    ("pais", "es", "location.country", ""),
    ("empresa actual", "es", "work_experience[0].company", ""),
    ("puesto actual", "es", "work_experience[0].title", ""),
]


async def main() -> None:
    configure_logging()
    client = create_mongo_client()
    await init_beanie(client, document_models=[LearnedMapping])
    repo = LearnedMappingRepository()
    created = 0
    for sig, lang, path, transform in CATALOG:
        existing = await LearnedMapping.find_one(
            LearnedMapping.field_signature == sig,
            LearnedMapping.language == lang,
        )
        if existing:
            continue
        await repo.upsert(
            field_signature=sig, language=lang, target_path=path,
            transform=transform or None,
            confidence=0.9, source="user_confirmed",
            user_count=0, usage_count=0,
        )
        created += 1
    print(f"Seeded {created} learned_mappings (skipped {len(CATALOG) - created} existing).")


if __name__ == "__main__":
    asyncio.run(main())

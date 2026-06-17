"""CV parser worker stub.

Real implementation uses `unstructured` to extract text and the LLM gateway
to structure it. For v1 the worker just marks CVs as `done` with empty data
to keep the loop running; the structure pipeline is wired in v1.1.
"""
import asyncio

from cvapplier.core.db import create_mongo_client, init_beanie
from cvapplier.core.logging import configure_logging, get_logger
from cvapplier.models import CV
from cvapplier.repositories.cv_repository import CVRepository

log = get_logger(__name__)


async def process_one(cv_id: str) -> None:
    repo = CVRepository()
    await repo.set_status(cv_id, status="processing")
    try:
        # Real work goes here: extract text via unstructured, structure via LLM,
        # update profile, then mark cv as done.
        await repo.set_status(cv_id, status="done", parsed_data={"note": "v1 stub"})
        log.info("cv_parsed_stub", cv_id=cv_id)
    except Exception as e:
        log.error("cv_parse_failed", cv_id=cv_id, error=str(e))
        await repo.set_status(cv_id, status="failed", parse_error=str(e))


async def main() -> None:
    configure_logging()
    client = create_mongo_client()
    await init_beanie(client, document_models=[CV])
    while True:
        pending = await CV.find(CV.parse_status == "pending").limit(5).to_list()
        if not pending:
            await asyncio.sleep(30)
            continue
        for cv in pending:
            await process_one(str(cv.id))


if __name__ == "__main__":
    asyncio.run(main())

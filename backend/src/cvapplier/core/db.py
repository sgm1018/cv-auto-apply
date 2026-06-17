"""MongoDB connection and Beanie initialization."""
from motor.motor_asyncio import AsyncIOMotorClient

from cvapplier.core.config import get_settings
from cvapplier.core.logging import get_logger

log = get_logger(__name__)


def create_mongo_client() -> AsyncIOMotorClient:
    s = get_settings()
    log.info("mongo_client_created", uri=s.mongo_uri)
    return AsyncIOMotorClient(s.mongo_uri, uuidRepresentation="standard")


async def init_beanie(client: AsyncIOMotorClient, *, db_name: str | None = None,
                      document_models: list | None = None) -> None:
    from beanie import init_beanie as _init
    db_name = db_name or get_settings().mongo_db
    await _init(database=client[db_name], document_models=document_models or [])
    log.info("mongo_beanie_ready", db_name=db_name, models=[m.__name__ if hasattr(m, '__name__') else str(m) for m in (document_models or [])])


async def close_mongo(client: AsyncIOMotorClient) -> None:
    log.info("mongo_client_closing")
    client.close()

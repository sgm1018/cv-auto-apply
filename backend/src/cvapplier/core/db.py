"""MongoDB connection and Beanie initialization."""
from motor.motor_asyncio import AsyncIOMotorClient

from cvapplier.core.config import get_settings


def create_mongo_client() -> AsyncIOMotorClient:
    s = get_settings()
    return AsyncIOMotorClient(s.mongo_uri, uuidRepresentation="standard")


async def init_beanie(client: AsyncIOMotorClient, *, db_name: str | None = None,
                      document_models: list | None = None) -> None:
    from beanie import init_beanie as _init
    db_name = db_name or get_settings().mongo_db
    await _init(database=client[db_name], document_models=document_models or [])


async def close_mongo(client: AsyncIOMotorClient) -> None:
    client.close()

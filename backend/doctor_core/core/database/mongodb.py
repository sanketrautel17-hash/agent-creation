from __future__ import annotations

from datetime import timezone
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase

from core.config.settings import Settings, get_settings


class MongoManager:
    def __init__(self) -> None:
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None

    async def connect(self, settings: Optional[Settings] = None) -> None:
        if self._client is not None:
            return
        active_settings = settings or get_settings()
        self._client = AsyncIOMotorClient(active_settings.mongo_url, tz_aware=True, tzinfo=timezone.utc)
        self._database = self._client[active_settings.database_name]

    async def disconnect(self) -> None:
        if self._client is not None:
            self._client.close()
        self._client = None
        self._database = None

    @property
    def database(self) -> AsyncIOMotorDatabase:
        if self._database is None:
            raise RuntimeError("MongoDB is not connected.")
        return self._database

    def collection(self, name: str) -> AsyncIOMotorCollection:
        return self.database[name]


mongo_manager = MongoManager()


def get_database() -> AsyncIOMotorDatabase:
    return mongo_manager.database


def get_collection(name: str) -> AsyncIOMotorCollection:
    return mongo_manager.collection(name)

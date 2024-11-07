import os
from typing import Type

from motor.motor_asyncio import AsyncIOMotorClient

from ..db import BaseDB, ItemT


class MongoDB(BaseDB):
    def __init__(self, url: str | None = None, db: str | None = None):
        if url is None:
            url = os.getenv("MONGO_URI")
        if db is None:
            db = os.getenv("MONGO_DB")

        assert url, "MONGO_URI is not set"
        assert db, "MONGO_DB is not set"
        self.url = url
        self.client = AsyncIOMotorClient(url)
        self.db = self.client[db]

    async def get_by_id(self, table_name: str, key: str, cast_to: Type[ItemT]):
        pass

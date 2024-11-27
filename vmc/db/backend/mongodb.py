import os

from motor.motor_asyncio import AsyncIOMotorClient

from ..db import BaseDB


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

    async def _get_by_id(self, table_name, key):
        return await self.db[table_name].find_one({"_id": key})

    async def _delete_by_id(self, table_name, key):
        return await self.db[table_name].delete_one({"_id": key})

    async def _insert(self, table_name, value):
        if "id" in value:
            value["_id"] = value["id"]
        return await self.db[table_name].insert_one(value)

    async def _update_by_id(self, table_name, key, value):
        return await self.db[table_name].update_one({"_id": key}, {"$set": value})

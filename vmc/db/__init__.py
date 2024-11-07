import os

from vmc.db.backend.disk_storage import DiskStorage
from vmc.db.backend.mongodb import MongoDB
from vmc.db.db import BaseDB, MemoryDB
from vmc.db.storage import Storage
from vmc.utils import LazyObjProxy

db: BaseDB = LazyObjProxy(lambda: _get_db())
storage = LazyObjProxy(lambda: _get_storage())
_db = None
_storage = None


def _get_db():
    global _db
    if _db is None:
        raise ValueError("DB not initialized")
    return _db


def _get_storage():
    global _storage

    if _storage is None:
        raise ValueError("Storage not initialized")
    return _storage


def init_storage(storage: Storage | None = None):
    global _storage

    if storage is None:
        STORAGE_TYPE = os.getenv("VMC_STORAGE_BACKEND", "disk")
        if STORAGE_TYPE == "disk":
            storage = DiskStorage()
        else:
            raise ValueError(f"Unknown storage backend: {STORAGE_TYPE}")
    _storage = storage
    return _storage


def init_db(db: BaseDB | None = None):
    global _db

    if db is None:
        DB_TYPE = os.getenv("VMC_DB_BACKEND", "memory")
        if DB_TYPE == "memory":
            db = MemoryDB()
        elif DB_TYPE == "mongodb":
            db = MongoDB()
        else:
            raise ValueError(f"Unknown DB backend: {DB_TYPE}")
    _db = db
    return _db


__all__ = [
    "db",
    "storage",
    "init_db",
    "init_storage",
    "MemoryDB",
    "MongoDB",
    "DiskStorage",
    "Storage",
]

import os

from vmc.db.backend.disk_storage import DiskStorage
from vmc.db.backend.mongodb import MongoDB
from vmc.db.db import MemoryDB

STORAGE_TYPE = os.getenv("VMC_STORAGE_BACKEND", "disk")
DB_TYPE = os.getenv("VMC_DB_BACKEND", "memory")
if STORAGE_TYPE == "disk":
    storage = DiskStorage()
if DB_TYPE == "mongodb":
    db = MongoDB()
elif DB_TYPE == "memory":
    db = MemoryDB()

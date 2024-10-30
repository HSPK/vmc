import hashlib
import json
import os
from os.path import join as pjoin

import anyio
from fastapi import File, UploadFile

from vmc.db.storage import FileType, Metadata, Storage


class DiskStorage(Storage):
    def __init__(self, storage_dir: str | None = None):
        if storage_dir is None:
            storage_dir = os.getenv("VMC_DISK_STORAGE_DIR", "storage")
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self.metadata_path = pjoin(storage_dir, "metadata.json")
        if not os.path.exists(self.metadata_path):
            with open(self.metadata_path, "w") as f:
                json.dump({}, f)
        with open(self.metadata_path, "r") as f:
            self.metadata: dict[str, Metadata] = json.load(f)

    async def store(
        self,
        file: FileType,
        encoding: str = "utf-8",
        created_at: float | None = None,
    ) -> Metadata:
        if isinstance(file, str):
            file_content = file
        elif isinstance(file, bytes):
            file_content = file
        elif isinstance(file, File):
            file_content = file.read()
        elif isinstance(file, UploadFile):
            file_content = await file.read()
        else:
            raise TypeError("Invalid file type")
        file_content = (
            file_content.encode(encoding=encoding)
            if isinstance(file_content, str)
            else file_content
        )
        md5 = hashlib.md5(file_content).hexdigest()
        if md5 in self.metadata:
            return self.metadata[md5]
        if isinstance(file, str | bytes):
            filename = "file.txt"
            filetype = "txt"
        else:
            filename = file.filename
            filetype = os.path.splitext(filename)[1]
        path = pjoin(self.storage_dir, md5 + filetype)
        os.makedirs(self.storage_dir, exist_ok=True)
        with open(path, "wb") as f:
            f.write(file_content)
        metadata: Metadata = {
            "filename": filename,
            "filetype": filetype,
            "filepath": path,
            "created_at": created_at or anyio.current_time(),
            "updated_at": anyio.current_time(),
            "size": os.path.getsize(path),
            "md5": md5,
            "id": md5,
        }
        self.metadata[md5] = metadata
        with open(self.metadata_path, "w") as f:
            json.dump(self.metadata, f)
        return metadata

    async def get(self, key: str) -> Metadata:
        if key not in self.metadata:
            raise FileNotFoundError(f"File {key} not found")
        return self.metadata[key]

    async def delete(self, key: str):
        if key not in self.metadata:
            raise FileNotFoundError(f"File {key} not found")
        os.remove(self.metadata[key]["filepath"])
        del self.metadata[key]
        with open(self.metadata_path, "w") as f:
            json.dump(self.metadata, f)

    async def list(self) -> list[Metadata]:
        return list(self.metadata.values())

    async def update(self, key: str, file: FileType) -> Metadata:
        if key not in self.metadata:
            return await self.store(key, file)
        old_metadata = self.metadata[key]
        await self.delete(key)
        return await self.store(key, file, old_metadata["created_at"])


if __name__ == "__main__":
    import asyncio

    async def main():
        storage = DiskStorage()
        file = "Hello, World!"
        metadata = await storage.store(file)
        print(metadata)
        metadata = await storage.get(metadata["id"])
        print(metadata)
        await storage.delete(metadata["id"])

        bfile = b"Bytes Hello, World!"
        metadata = await storage.store(bfile)
        print(metadata)
        metadata = await storage.get(metadata["id"])
        print(metadata)

        files = await storage.list()
        print(files)

        await storage.delete(metadata["id"])
        files = await storage.list()
        print(files)

    asyncio.run(main())

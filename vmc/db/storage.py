from typing import TypeVar, Union

from fastapi import File, UploadFile
from typing_extensions import TypedDict

FileType = TypeVar("FileType", bound=Union[File, UploadFile, str, bytes])


class Metadata(TypedDict):
    id: str
    filename: str
    filetype: str
    filepath: str
    created_at: float
    updated_at: float
    size: int
    md5: str


class Storage:
    async def store(self, file: FileType) -> Metadata:
        pass

    async def get(self, key: str) -> Metadata:
        pass

    async def delete(self, key: str):
        pass

    async def list(self) -> list[Metadata]:
        pass

    async def update(self, key: str, file: FileType) -> Metadata:
        pass

import hashlib
import os
from os.path import join as pjoin

import anyio
from fastapi import File, UploadFile

get_mongo_db = None


def get_file_path(_id: str) -> str:
    item = get_mongo_db()["files"].find_one({"_id": _id})
    if not item:
        return None
    return item["path"]


async def store_file(file: UploadFile = File(...), *, return_path: bool = False) -> str:
    file_content = await file.read()
    md5 = hashlib.md5(file_content).hexdigest()
    if get_mongo_db()["files"].find_one({"_id": md5}):
        return md5
    filetype = os.path.splitext(file.filename)[1]
    path = anyio.Path(pjoin("upload", md5 + filetype))
    await path.parent.mkdir(parents=True, exist_ok=True)
    await path.write_bytes(file_content)

    get_mongo_db()["files"].insert_one(
        {
            "_id": md5,
            "filename": file.filename,
            "filetype": filetype,
            "path": path.as_posix(),
        }
    )
    return path.as_posix() if return_path else md5

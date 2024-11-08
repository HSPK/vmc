from typing import Any, List, Type, TypeVar, Union

from pydantic import BaseModel
from typing_extensions import Literal

from vmc.db.schema import Generation, User
from vmc.types.generation import Generation as GenerationType
from vmc.types.generation import GenerationChunk
from vmc.types.generation.message_params import GenerationMessageParam
from vmc.utils import sha256

ItemT = TypeVar(
    "ResponseT",
    bound=Union[
        str,
        int,
        float,
        bool,
        BaseModel,
        List[BaseModel],
    ],
)


def serialize(value: ItemT) -> ItemT:
    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, list):
        return [item.model_dump() if isinstance(item, BaseModel) else item for item in value]
    return value


def deserialize(value: ItemT, cast_to: Type[ItemT]) -> ItemT:
    if isinstance(value, dict):
        return cast_to.model_validate(value)
    if isinstance(value, list):
        return [cast_to.model_validate(item) if isinstance(item, dict) else item for item in value]
    return value


class UserOpMixin:
    async def get_user(self, key: str) -> User:
        return await self.get_by_id("users", key, User)

    async def get_user_by_token(self, token: str) -> User:
        if token.startswith("Bearer "):
            token = token[7:]
        username, password = token.split(":", 1)
        if not username or not password:
            return None

        user = await self.get_user(username)
        if user and user.password == sha256(password):
            return user
        return None

    async def add_user(self, username: str, password: str, role: Literal["admin", "user"]) -> User:
        user = User(id=username, username=username, password=sha256(password), role=role)
        await self.insert("users", user)
        return user

    async def delete_user(self, key: str):
        await self.delete_by_id("users", key)


class GenerationOpMixin:
    async def save_generation(
        self,
        user_id: str,
        model_name: str,
        content: str | list[GenerationMessageParam],
        generation_kwargs: dict,
        generation: GenerationType | list[GenerationChunk],
    ) -> Generation:
        await self.insert(
            "generations",
            Generation(
                user_id=user_id,
                model_name=model_name,
                content=content,
                generation_kwargs=generation_kwargs,
                generation=generation,
            ),
        )

    async def get_generation(self, key: str) -> Generation:
        return await self.get_by_id("generations", key, Generation)

    async def delete_generation(self, key: str):
        await self.delete_by_id("generations", key)

    async def list_generations(self, user_id: str, page: int, page_size: int) -> List[Generation]:
        pass


class BaseDB(UserOpMixin, GenerationOpMixin):
    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def _get_by_id(self, table_name: str, key: str) -> Any:
        pass

    async def _update_by_id(self, table_name: str, key: str, value: Any):
        pass

    async def _delete_by_id(self, table_name: str, key: str):
        pass

    async def _insert(self, table_name: str, value: Any):
        pass

    async def get_by_id(self, table_name: str, key: str, cast_to: Type[ItemT]) -> ItemT:
        data = await self._get_by_id(table_name, key)
        return deserialize(data, cast_to)

    async def insert(self, table_name: str, value: ItemT):
        data = serialize(value)
        await self._insert(table_name, data)

    async def update_by_id(self, table_name: str, key: str, value: ItemT):
        data = serialize(value)
        await self._update_by_id(table_name, key, data)

    async def delete_by_id(self, table_name: str, key: str):
        await self._delete_by_id(table_name, key)


class MemoryDB(BaseDB):
    def __init__(self):
        self.db = {}

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def _get_by_id(self, table_name, key):
        return self.db.get(table_name, {}).get(key)

    async def _update_by_id(self, table_name, key, value):
        self.db.setdefault(table_name, {})[key] = value

    async def _delete_by_id(self, table_name, key):
        self.db.get(table_name, {}).pop(key, None)

    async def _insert(self, table_name, value):
        self.db.setdefault(table_name, {})[value["id"]] = value


if __name__ == "__main__":

    async def test():
        db = MemoryDB()
        await db.connect()
        user = await db.add_user("admin", "admin", "admin")
        print(user)
        user = await db.get_user(user.id)
        print(user)
        await db.delete_user(user.id)
        user = await db.get_user(user.id)
        print(user)

        await db.disconnect()

    import asyncio

    asyncio.run(test())

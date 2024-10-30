from typing import List, Type, TypeVar, Union

from pydantic import BaseModel

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


class BaseDB:
    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def get(self, table_name: str, key: str, cast_to: Type[ItemT]) -> ItemT:
        pass

    async def insert(self, table_name: str, value: ItemT):
        pass

    async def update(self, table_name: str, key: str, value: ItemT):
        pass

    async def delete(self, table_name: str, key: str):
        pass


class MemoryDB:
    def __init__(self):
        self.db = {}

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    def adapt(self, value: ItemT) -> ItemT:
        if isinstance(value, BaseModel):
            return value.model_dump()
        if isinstance(value, list):
            return [item.model_dump() if isinstance(item, BaseModel) else item for item in value]
        return value

    def adapt_back(self, value: ItemT) -> ItemT:
        if isinstance(value, BaseModel):
            return value.model_validate(value)
        if isinstance(value, list):
            return [
                item.model_validate(item) if isinstance(item, BaseModel) else item for item in value
            ]
        return value

    async def get(self, table_name: str, key: str, cast_to: Type[ItemT]) -> ItemT:
        value = self.db[table_name][key]
        return self.adapt_back(value)

    async def insert(self, table_name: str, key: str, value: ItemT):
        if table_name not in self.db:
            self.db[table_name] = {}
        self.db[table_name]

    async def update(self, table_name: str, key: str, value: ItemT):
        pass

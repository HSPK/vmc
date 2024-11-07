import uuid

import pydantic
from typing_extensions import Literal

from vmc.types.generation import Generation as GenerationType
from vmc.types.generation import GenerationChunk


class BaseModel(pydantic.BaseModel):
    id: str = pydantic.Field(default_factory=lambda: str(uuid.uuid4()))


class User(BaseModel):
    username: str
    password: str
    role: Literal["admin", "user"]


class Generation(BaseModel):
    user_id: str
    is_streaming: bool = False
    generation_type: Literal["text", "image"] = "text"
    generation: GenerationType | list[GenerationChunk]

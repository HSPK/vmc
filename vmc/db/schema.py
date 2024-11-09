import time
import uuid

import pydantic
from typing_extensions import Literal

from vmc.types.generation import Generation as GenerationType
from vmc.types.generation import GenerationChunk
from vmc.types.generation.message_params import GenerationMessageParam


class BaseModel(pydantic.BaseModel):
    id: str = pydantic.Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = pydantic.Field(default_factory=lambda: time.time())
    updated_at: float = pydantic.Field(default_factory=lambda: time.time())

    model_config = pydantic.ConfigDict(protected_namespaces=())


class User(BaseModel):
    username: str
    password: str
    role: Literal["admin", "user"]


class Generation(BaseModel):
    user_id: str
    model_name: str
    content: str | list[GenerationMessageParam]
    generation_kwargs: dict
    generation: GenerationType | list[GenerationChunk]

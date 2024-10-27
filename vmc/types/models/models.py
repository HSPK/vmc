from typing import Dict, Literal

from vmc.types.pricing import Pricing

from .._base import BaseModel, BaseOutput


class ModelInfo(BaseModel):
    name: str
    model_class: str
    type: Literal["chat", "embedding", "audio", "reranker"] = "chat"
    pricing: Pricing | None = None
    context_window: int | None = None
    output_dimension: int | None = None
    max_tokens: int | None = None
    description: str | None = None
    knowledge_date: str | None = None
    is_local: bool = False


class ModelInfoOutput(BaseOutput):
    models: Dict[str, ModelInfo]

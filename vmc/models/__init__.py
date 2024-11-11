from typing import Union

from .audio import BaseAudioModel
from .embedding import BaseEmbeddingModel
from .gemini.gemini import Gemini
from .generation import BaseGenerationModel
from .openai.openai import OpenAI
from .rerank import BaseRerankModel
from .tei.tei import TeiEmbedding
from .vmc.vmc import VMC

ModelType = Union[BaseAudioModel, BaseEmbeddingModel, BaseGenerationModel, BaseRerankModel]
model_names = ["VMC", "OpenAI", "Gemini", "TeiEmbedding"]
__all__ = [
    "BaseAudioModel",
    "BaseEmbeddingModel",
    "BaseGenerationModel",
    "BaseRerankModel",
    "VMC",
    "OpenAI",
    "Gemini",
    "TeiEmbedding",
]

import time
from typing import Iterable, List, Union

import torch
from loguru import logger
from sentence_transformers import SentenceTransformer
from typing_extensions import Literal

from vmc.models.embedding import BaseEmbeddingModel
from vmc.models.utils import filter_notgiven
from vmc.types._types import NOT_GIVEN, NotGiven
from vmc.types.embedding.embedding import NO_COST, EmbeddingResponse
from vmc.utils.gpu import torch_gc


class TransformerEmbedding(BaseEmbeddingModel):
    def __init__(
        self,
        backend: Literal["torch", "onnx", "openvino"] = "torch",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")
        logger.debug(f"load {self.model_id} using device: {self.device} at {backend}")
        self.model = SentenceTransformer(
            self.model_id, trust_remote_code=True, device=self.device, backend=backend
        )
        self.model.eval()

    async def embedding(
        self,
        content: Union[str, List[str], Iterable[int], Iterable[Iterable[int]]],
        *,
        normalize_embeddings: bool = True,
        batch_size: int | NotGiven = NOT_GIVEN,
        **kwargs,
    ) -> EmbeddingResponse:
        if kwargs:
            logger.warning(f"{self.model_id} Unused parameters: {kwargs}")
        content = [content] if isinstance(content, str) else content
        created = time.time()
        embeddings = self.model.encode(
            content,
            **filter_notgiven(batch_size=batch_size),
            normalize_embeddings=normalize_embeddings,
        ).tolist()
        torch_gc()
        return EmbeddingResponse(
            embedding=embeddings,
            created=created,
            embed_time=time.time() - created,
            model=self.model_id,
            cost=NO_COST,
        )

import time
from typing import Iterable, List, Union

from loguru import logger
from typing_extensions import Literal

from vmc.models.utils import filter_notgiven
from vmc.serve import is_serve_enabled
from vmc.types._types import NOT_GIVEN, NotGiven
from vmc.types.embedding import EmbeddingResponse
from vmc.utils.utils import torch_gc

from ...embedding import BaseEmbeddingModel

if is_serve_enabled():
    import torch
    from sentence_transformers import SentenceTransformer


class TransformerEmbedding(BaseEmbeddingModel):
    def __init__(
        self,
        torch_dtype: Literal["float16", "float32", "float64", "bfloat16"] = "bfloat16",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if torch.backends.mps.is_available():
            self.device = "mps"
        elif torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"
        torch_dtype = {
            "float16": torch.float16,
            "float32": torch.float32,
            "float64": torch.float64,
            "bfloat16": torch.bfloat16,
        }[torch_dtype]
        self.model = SentenceTransformer(self.model_id, trust_remote_code=True).to(self.device)
        self.model.eval()

    async def embedding(
        self,
        content: Union[str, List[str], Iterable[int], Iterable[Iterable[int]]],
        *,
        batch_size: int | NotGiven = NOT_GIVEN,
        normalize_embeddings: bool | NotGiven = NOT_GIVEN,
        **kwargs,
    ) -> EmbeddingResponse:
        if kwargs:
            logger.warning(f"{self.model_id} Unused parameters: {kwargs}")
        content = [content] if isinstance(content, str) else content
        created = time.time()
        embeddings = self.model.encode(
            content,
            **filter_notgiven(
                batch_size=batch_size,
                normalize_embeddings=normalize_embeddings,
            ),
        ).tolist()
        torch_gc()
        return EmbeddingResponse(
            embeddings=embeddings,
            created=created,
            embed_time=time.time() - created,
            model=self.model_id,
        )

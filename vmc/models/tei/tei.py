import time
from typing import Iterable, List, Union

from loguru import logger

from vmc.models.embedding import BaseEmbeddingModel
from vmc.models.rerank import BaseRerankModel
from vmc.types.embedding import EmbeddingResponse
from vmc.types.rerank import RerankOutput
from vmc.utils.api_client import AsyncAPIClient


class TeiEmbedding(BaseEmbeddingModel, BaseRerankModel):
    def __init__(self, port: int, host: str = "localhost", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = AsyncAPIClient(base_url=f"http://{host}:{port}")

    async def embedding(
        self,
        content: Union[str, List[str], Iterable[int], Iterable[Iterable[int]]],
        **kwargs,
    ) -> EmbeddingResponse:
        if kwargs:
            logger.warning(f"{self.model_id} Unused parameters: {kwargs}")
        created = time.time()
        res = await self.client.post(
            "/embed",
            body={"inputs": content},
            options={"raw_response": True},
            cast_to=list[list[int]],
        )
        return EmbeddingResponse(
            embedding=res.json(),
            created=created,
            embed_time=time.time() - created,
            model=self.model_id,
        )

    async def rerank(self, content: list[list[str]], **kwargs) -> RerankOutput:
        if kwargs:
            logger.warning(f"{self.model_id} Unused parameters: {kwargs}")
        res = await self.client.post(
            "/rerank",
            body={"inputs": content},
            options={"raw_response": True},
            cast_to=list[int],
        )
        return RerankOutput(scores=res.json())

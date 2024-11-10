from typing import Iterable, List, Union

from loguru import logger

from vmc.models.embedding import BaseEmbeddingModel
from vmc.types.embedding import EmbeddingResponse
from vmc.utils.api_client import AsyncAPIClient


class TeiEmbedding(BaseEmbeddingModel):
    def __init__(self, port: int, host: str = "localhost"):
        self.client = AsyncAPIClient(base_url=f"http://{host}:{port}")

    async def embedding(
        self,
        content: Union[str, List[str], Iterable[int], Iterable[Iterable[int]]],
        **kwargs,
    ) -> EmbeddingResponse:
        if kwargs:
            logger.warning(f"{self.model_id} Unused parameters: {kwargs}")
        res = await self.client.post(
            "/embed",
            body={"inputs": content},
            options={"raw_response": True},
            cast_to=list[list[int]],
        )
        return EmbeddingResponse(embedding=res.json())

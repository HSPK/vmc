from typing import Iterable, List, Literal, Union

from vmc.models.utils import filter_notgiven
from vmc.types._types import NOT_GIVEN, NotGiven
from vmc.types.embedding import EmbeddingResponse

from ._base import BaseModel


class BaseEmbeddingModel(BaseModel):
    async def embedding(
        self,
        content: Union[str, List[str], Iterable[int], Iterable[Iterable[int]]],
        *,
        return_spase_embedding: bool | NotGiven = NOT_GIVEN,
        return_original_response: bool | NotGiven = NOT_GIVEN,
        dimensions: int | NotGiven = NOT_GIVEN,
        encoding_format: Literal["float", "base64"] | NotGiven = NOT_GIVEN,
        user: str | NotGiven = NOT_GIVEN,
        task_type: str | NotGiven = NOT_GIVEN,
        title: str | NotGiven = NOT_GIVEN,
        **kwargs,
    ) -> EmbeddingResponse:
        raise NotImplementedError("embedding is not implemented")

    async def _embedding(
        self,
        content: Union[str, List[str], Iterable[int], Iterable[Iterable[int]]],
        *,
        return_spase_embedding: bool | NotGiven = NOT_GIVEN,
        return_original_response: bool | NotGiven = NOT_GIVEN,
        dimensions: int | NotGiven = NOT_GIVEN,
        encoding_format: Literal["float", "base64"] | NotGiven = NOT_GIVEN,
        user: str | NotGiven = NOT_GIVEN,
        task_type: str | NotGiven = NOT_GIVEN,
        title: str | NotGiven = NOT_GIVEN,
        **kwargs,
    ) -> EmbeddingResponse:
        await self.callback.on_embedding_start(content, kwargs)
        res = await self.embedding(
            **filter_notgiven(
                content=content,
                return_spase_embedding=return_spase_embedding,
                return_original_response=return_original_response,
                dimensions=dimensions,
                encoding_format=encoding_format,
                user=user,
                task_type=task_type,
                title=title,
                **kwargs,
            )
        )
        await self.callback.on_embedding_end(res)
        return res

from vmc.callback import callback
from vmc.types.rerank import RerankOutput

from ._base import BaseModel


class BaseRerankModel(BaseModel):
    async def rerank(self, content: list[list[str]], **kwargs) -> RerankOutput:
        raise NotImplementedError("rerank method is not implemented")

    async def _rerank(self, content: list[list[str]], **kwargs) -> RerankOutput:
        await callback.on_rerank_start(self, content, **kwargs)
        res = await self.rerank(content, **kwargs)
        await callback.on_rerank_end(self, res)
        return res

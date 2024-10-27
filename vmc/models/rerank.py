from vmc.types.rerank import RerankOutput

from ._base import BaseModel


class BaseRerankModel(BaseModel):
    async def rerank(self, content: list[list[str]], **kwargs):
        raise NotImplementedError("rerank method is not implemented")

    async def _rerank(self, content: list[list[str]], **kwargs) -> RerankOutput:
        await self.callback.on_rerank_start(content, kwargs)
        res = await self.rerank(content, **kwargs)
        await self.callback.on_rerank_end(res)
        return res

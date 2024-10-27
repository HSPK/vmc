from typing import (
    TYPE_CHECKING,
    Union,
)

import anyio
from loguru import logger

from vmc.types.embedding import EmbeddingResponse
from vmc.types.generation import (
    ContentType,
    Generation,
)
from vmc.types.rerank import RerankOutput

if TYPE_CHECKING:
    from ._base import BaseModel


class Callback:
    def __init__(self, run_in_backgroud: bool = False):
        self.run_in_backgroud = run_in_backgroud

    async def on_chat_start(
        self, model: "BaseModel", content: Union[str, list[ContentType]], **kwargs
    ):
        pass

    async def on_chat_end(self, model: "BaseModel", output: Generation):
        pass

    async def on_embedding_start(self, model: "BaseModel", content: str | list[str], **kwargs):
        pass

    async def on_embedding_end(self, model: "BaseModel", output: EmbeddingResponse):
        pass

    async def on_rerank_start(self, model: "BaseModel", content: list[list[str]], **kwargs):
        pass

    async def on_rerank_end(self, model: "BaseModel", output: RerankOutput):
        pass


class CallbackProxy:
    def __init__(self, callbacks: list[Callback] = []):
        self.background_callbacks = []
        self.callbacks = callbacks
        for c in self.callbacks:
            if c.run_in_backgroud:
                self.background_callbacks.append(c)
            else:
                self.callbacks.append(c)

    def _on_event(self, name: str):
        async def _on_event(*args, **kwargs):
            # backgroud tasks don't accept kwargs for now
            if self.background_callbacks and kwargs:
                assert False, "Background tasks don't accept kwargs, please use args instead"
            async with anyio.create_task_group() as tg:
                for c in self.background_callbacks:
                    if hasattr(c, name):
                        tg.start_soon(getattr(c, name), *args)

            for c in self.callbacks:
                if hasattr(c, name):
                    try:
                        await getattr(c, name)(*args, **kwargs)
                    except Exception as e:
                        logger.error(f"Error in callback {c.__class__.__name__} {name}: {e}")
            return

        return _on_event

    def __getattr__(self, name: str):
        if name.startswith("on_"):
            return self._on_event(name)
        return super().__getattr__(name)

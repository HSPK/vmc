import asyncio
from typing import TYPE_CHECKING, Union

from fastapi import Request
from loguru import logger

from vmc.types.audio import Transcription
from vmc.types.embedding import EmbeddingResponse
from vmc.types.generation import Generation, GenerationChunk
from vmc.types.generation.message_params import GenerationMessageParam
from vmc.types.rerank import RerankOutput

if TYPE_CHECKING:
    from vmc.models._base import BaseModel


class VMCCallback:
    def __init__(self, *, run_in_background: bool = False):
        self.run_in_background = run_in_background

    async def on_startup(self, title: str | None = None, message: str | None = None, **kwargs):
        pass

    async def on_shutdown(self, title: str | None = None, message: str | None = None, **kwargs):
        pass

    async def on_generation_start(
        self, model: "BaseModel", content: Union[str, list[GenerationMessageParam]], **kwargs
    ):
        pass

    async def on_generation_end(
        self,
        model: "BaseModel",
        content: Union[str, list[GenerationMessageParam]],
        generation_kwargs: dict,
        output: Generation | list[GenerationChunk],
        **kwargs,
    ):
        pass

    async def on_embedding_start(self, model: "BaseModel", content: str | list[str], **kwargs):
        pass

    async def on_embedding_end(self, model: "BaseModel", output: EmbeddingResponse):
        pass

    async def on_rerank_start(self, model: "BaseModel", content: list[list[str]], **kwargs):
        pass

    async def on_rerank_end(self, model: "BaseModel", output: RerankOutput):
        pass

    async def on_transcribe_start(self, model: "BaseModel", file: str, **kwargs):
        pass

    async def on_transcribe_end(self, model: "BaseModel", output: Transcription):
        pass

    async def on_exception(self, request: Request, exc: Exception, **kwargs):
        pass


class VMCCallbackGroup:
    def __init__(self, callbacks: list[VMCCallback]):
        self.callbacks = callbacks

    async def _on_callback(self, name: str, *args, **kwargs):
        if not self.callbacks:
            return
        background_tasks = []
        foreground_tasks = []
        for callback in self.callbacks:
            if callback.run_in_background:
                background_tasks.append(getattr(callback, name))
            else:
                foreground_tasks.append(getattr(callback, name))
        try:
            tasks = [asyncio.create_task(task(*args, **kwargs)) for task in background_tasks]
            if kwargs.get("gather_background", False):
                await asyncio.gather(*tasks)
            await asyncio.gather(*(task(*args, **kwargs) for task in foreground_tasks))
        except Exception as e:
            logger.error(f"Error in callback {name}: {e}")

    def __getattr__(self, name: str):
        if name.startswith("on"):

            async def _callback(*args, **kwargs):
                await self._on_callback(name, *args, **kwargs)

            return _callback
        return super().__getattr__(name)

    def add(self, callback: VMCCallback):
        self.callbacks.append(callback)

    def remove(self, callback: VMCCallback):
        self.callbacks.remove(callback)

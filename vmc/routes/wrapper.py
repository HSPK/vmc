from fastapi.responses import StreamingResponse

from vmc.exception import exception_handler
from vmc.models.openai.response_adapter import (
    restore_completion,
    restore_completion_chunk,
    restore_embedding,
)
from vmc.proxy.model import ProxyModel


class FastAPIWrapper:
    def __init__(self, model: ProxyModel):
        self.model = model
        self.embedding = model._embedding
        self.rerank = model._rerank
        self.tokenize = model._tokenize
        self.transcribe = model._transcribe

    async def generate(self, *args, **kwargs):
        async def _streaming():
            try:
                async for token in await self.model._generate(*args, **kwargs):
                    yield token.to_event()
            except Exception as e:
                msg = await exception_handler(e)
                yield msg.to_event()
                return

        if kwargs.get("stream", False):
            return StreamingResponse(
                _streaming(),
                media_type="text/event-stream",
                headers={"X-Accel-Buffering": "no"},
            )
        return await self.model._generate(*args, **kwargs)

    async def generate_openai(self, *args, **kwargs):
        async def _streaming():
            try:
                async for token in await self.model._generate(*args, **kwargs):
                    chunk = restore_completion_chunk(token)
                    yield f"data: {chunk.model_dump_json()}\n\n"
            except Exception as e:
                msg = await exception_handler(e)
                yield msg.to_event()
                return

        if kwargs.get("stream", False):
            return StreamingResponse(
                _streaming(),
                media_type="text/event-stream",
                headers={"X-Accel-Buffering": "no"},
            )
        return restore_completion(await self.model._generate(*args, **kwargs))

    async def embedding_openai(self, *args, **kwargs):
        return restore_embedding(await self.model._embedding(*args, **kwargs))


def wrap_fastapi(model: ProxyModel) -> FastAPIWrapper:
    if model.forward:
        """Direct forward response from VMC Server"""
        return model
    else:
        return FastAPIWrapper(model)

from rich import print

from vmc.callback.base import VMCCallback


class LoggingCallback(VMCCallback):
    async def on_startup(self):
        print("✅ Server started!")

    async def on_shutdown(self):
        print("❌ Server stopped!")

    async def on_generation_start(self, *args, **kwargs):
        print("🚀 Generation started!")

    async def on_generation_end(self, *args, **kwargs):
        print("🎉 Generation finished!")

    async def on_generation_failed(self, *args, **kwargs):
        print("❌ Generation failed!")

    async def on_embedding_start(self, model, content, **kwargs):
        print("🚀 Embedding started!")

    async def on_embedding_end(self, model, output):
        print("🎉 Embedding finished!")

    async def on_rerank_start(self, model, content, **kwargs):
        print("🚀 Rerank started!")

    async def on_rerank_end(self, model, output):
        print("🎉 Rerank finished!")


class SaveGenerationToDB(VMCCallback):
    async def on_generation_finish(self, *args, **kwargs):
        print("🎉 Saved to DB")

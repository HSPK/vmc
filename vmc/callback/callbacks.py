from rich import print

from vmc.callback.base import VMCCallback
from vmc.context.user import current_user
from vmc.db import db


class LoggingCallback(VMCCallback):
    async def on_startup(self, title=None, message=None, **kwargs):
        print("✅ On Server start!")

    async def on_shutdown(self, title=None, message=None, **kwargs):
        print("❌ Server stopped!")

    async def on_generation_start(self, *args, **kwargs):
        print(f"🚀 Generation for {current_user.username} started!")

    async def on_generation_end(self, *args, **kwargs):
        print(f"🎉 Generation for {current_user.username} finished!")

    async def on_generation_failed(self, *args, **kwargs):
        print("❌ Generation failed!")

    async def on_embedding_start(self, model, content, **kwargs):
        print(f"🚀 Embedding for {current_user.username} started!")

    async def on_embedding_end(self, model, output):
        print(f"🎉 Embedding for {current_user.username} finished!")

    async def on_rerank_start(self, model, content, **kwargs):
        print("🚀 Rerank started!")

    async def on_rerank_end(self, model, output):
        print("🎉 Rerank finished!")


class SaveGenerationToDB(VMCCallback):
    def __init__():
        super().__init__(run_in_background=True)

    async def on_generation_end(self, model, content, generation_kwargs, output, **kwargs):
        db.save_generation(
            user_id=current_user.id,
            model_name=model.config.name,
            content=content,
            generation_kwargs=generation_kwargs,
            generation=output,
        )

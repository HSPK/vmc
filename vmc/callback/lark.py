import os

from fastapi import Request
from slark import AsyncLark

from vmc.callback.base import VMCCallback
from vmc.context.user import current_user


class LarkNotify(VMCCallback):
    def __init__(self, webhook_url: str | None = None):
        super().__init__(run_in_background=True)
        webhook_url = webhook_url or os.getenv("LARK_WEBHOOK")
        assert webhook_url, "Lark Webhook URL is required"
        self.lark = AsyncLark(webhook=webhook_url)

    async def on_startup(self, title=None, message=None, **kwargs):
        await self.lark.webhook.post_success_card(msg=message, title=title)

    async def on_shutdown(self, title=None, message=None, **kwargs):
        await self.lark.webhook.post_success_card(msg=message, title=title)

    async def on_exception(self, request: Request, exc: Exception, **kwargs):
        await self.lark.webhook.post_error_card(
            msg=exc.msg if hasattr(exc, "msg") else str(exc),
            traceback=kwargs.get("tb", ""),
            title=f"{exc.__class__.__name__} (from {current_user.username})",
        )

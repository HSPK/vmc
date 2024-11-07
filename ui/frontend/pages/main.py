from contextlib import contextmanager
from dataclasses import dataclass

from nicegui import ui

from ui.frontend.components.footer import ChatFooter
from ui.frontend.components.header import ChatHeader
from ui.frontend.components.history_drawer import HistoryDrawer
from ui.frontend.components.log_drawer import LogDrawer
from ui.frontend.components.meesage_container import MessageContainer


@dataclass
class Context:
    history_drawer: HistoryDrawer
    log_drawer: LogDrawer
    footer: ChatFooter
    content: MessageContainer


class Callback:
    async def on_conv_click(self, conv_id):
        pass

    async def on_conv_rename(self, conv_id, title):
        pass

    async def on_conv_delete(self, conv_id):
        pass

    async def on_message_send(
        self, context: Context, msg: ui.input, llm_filter, dont_show_user_message: bool = False
    ):
        pass

    async def on_details_click(self, message_id, log_drawer: LogDrawer):
        pass


@contextmanager
def frame(callback: Callback):
    """Custom page frame to share the same styling and behavior across all pages"""
    ui.colors(primary="teal")
    ui.query(".nicegui-content").classes("flex w-full h-full")
    history_drawer = HistoryDrawer(
        on_conv_click=callback.on_conv_click,
        on_conv_rename=callback.on_conv_rename,
        on_conv_delete=callback.on_conv_delete,
    )
    ChatHeader(history_drawer=history_drawer)
    log_drawer = LogDrawer()

    async def on_message_send(*args, **kwargs):
        await callback.on_message_send(context, *args, **kwargs)

    footer = ChatFooter(on_message_send=on_message_send)
    with MessageContainer() as content:
        context = Context(
            history_drawer=history_drawer, log_drawer=log_drawer, footer=footer, content=content
        )
        yield context

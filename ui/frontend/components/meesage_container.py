from nicegui import ui

from ui.db.schema import ChatMessage
from ui.frontend.components.message import Message


class MessageContainer(ui.element):
    def __init__(self, tag="div", *, _client=None):
        super().__init__(tag, _client=_client)
        self.classes("w-full h-full overflow-scroll-y max-w-3xl mx-auto")

    def render_messages(self, messages: list[ChatMessage], log_drawer, on_details_click=None):
        with self:
            for message in messages:
                Message(message, log_drawer=log_drawer, on_details_click=on_details_click)

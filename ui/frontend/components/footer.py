from typing import Callable

from nicegui import ui


class ChatFooter(ui.footer):
    def __init__(
        self,
        *,
        on_message_send: Callable[[ui.input, bool, bool], None],
        value=True,
        fixed=True,
        bordered=False,
        elevated=False,
        wrap=True,
    ):
        super().__init__(value=value, fixed=fixed, bordered=bordered, elevated=elevated, wrap=wrap)
        self.classes("bg-white")
        self._on_send = on_message_send
        with self, ui.column().classes("w-full max-w-3xl mx-auto pb-2"):
            self.build()

    async def send(self, dont_show_user_message: bool = False):
        if not self.text.value.strip():
            ui.notify("Input is empty", type="warning")
            return
        self.text.disable()
        await self._on_send(
            self.text,
            llm_filter=self.llm_filter.value,
            dont_show_user_message=dont_show_user_message,
        )
        self.text.enable()

    def build(self):
        def on_change():
            if not text.value.strip():
                send_btn.classes(
                    "text-gray-400", remove="text-secondary hover:!bg-teal-500 hover:!text-white"
                )
            else:
                send_btn.classes(
                    "text-secondary hover:!bg-teal-500 hover:!text-white", remove="text-gray-400"
                )

        with ui.input(placeholder="Ask a question...", on_change=on_change).props(
            "rounded outlined bg-color=white color=secondary autofocus"
        ).classes("flex w-full item-aligned text-base") as text:
            self.text = text

            with text.add_slot("prepend"):
                ui.icon("upload", size="sm").classes(
                    "self-center cursor-pointer rounded-3xl p-2 -mr-2 text-secondary  bg-white hover:!bg-teal-500 hover:!text-white"
                )
            send_btn = (
                ui.icon("send", size="sm")
                .classes("self-center cursor-pointer rounded-3xl p-2 text-gray-400 bg-white")
                .on("click", self.send)
            )
        with ui.row(wrap=False, align_items="start").classes(
            "w-full flex items-center no-wrap my-[-0.6rem]"
        ):
            ui.markdown("FOP图表生成器(测试)").classes("font-bold ml-3 italic text-gray-700")
            self.llm_filter = (
                ui.checkbox("LLM 列过滤")
                .props("left-label color=secondary keep-color size=xs")
                .classes("ml-auto mr-3 text-gray-700")
            )

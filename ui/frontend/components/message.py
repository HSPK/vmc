from pathlib import Path
from typing import Literal

from nicegui import ui
from PIL.Image import Image

from ui.db import db
from ui.db.schema import ChatMessage
from ui.db.utils import iso_to_beijing

bot_avatar = "https://robohash.org/1?bgset=bg2"


def escape_markdown(text: str) -> str:
    return text.replace("_", "\\_")


class Message(ui.row):
    def __init__(self, msg: ChatMessage, log_drawer=None, on_details_click=None):
        super().__init__(wrap=False)
        self.classes("my-6 w-fit -space-x-2 md:space-x-0")
        self.log_drawer = log_drawer
        self.log_opened = False
        self.on_details_click = on_details_click
        self.msg_id = msg.id

        with self:
            if msg.avatar:
                ui.image(msg.avatar).classes("w-7 h-7 md:w-10 md:h-10 rounded-full my-4")
            with ui.column().classes("-space-y-2 w-fit") as self.items_container:
                self.content = ui.column().classes(
                    "group -space-y-4 w-fit rounded-xl px-4 py-2 bg-gray-50 flex-grow"
                )
                self.spinner = ui.spinner(type="dots", size="2em").classes("mx-4 my-2 hidden")
        if msg.sent:
            self.classes("ml-auto")
            self.content.classes("bg-slate-100")
        self._last_markdown = None
        self.render_message(msg)

    def render_message(self, msg: ChatMessage):
        if not msg.text.strip() and not msg.blocks:
            self.content.set_visibility(False)
            return
        with self.content:
            if msg.text:
                ui.markdown(escape_markdown(msg.text)).classes("text-base").classes(
                    "bg-gray-50" if not msg.sent else "bg-slate-100"
                )
            if msg.blocks:
                for block in msg.blocks:
                    if block.type == "text":
                        ui.markdown(escape_markdown(block.text)).classes("text-base").classes(
                            "bg-gray-50" if not msg.sent else "bg-slate-100"
                        )
                    elif block.type == "image":
                        ui.image(block.url).classes("max-w-72 md:max-w-2xl")
                    elif block.type == "code":
                        ui.code(block.code, language=block.lang).classes(
                            "bg-gray-50 max-w-72 md:max-w-2xl"
                        )

        self.finish(msg)

    def show_spinner(self):
        self.spinner.classes(remove="hidden")

    def hide_spinner(self):
        self.spinner.classes("hidden")

    def update_text(self, text, mode: Literal["append", "replace"] = "append"):
        self.content.set_visibility(True)
        if self._last_markdown:
            text = self._last_markdown.content + text if mode == "append" else text
            self._last_markdown.set_content(text)
        else:
            with self.content:
                self._last_markdown = ui.markdown(escape_markdown(text)).classes(
                    "text-base bg-gray-50"
                )

    def clear_content(self):
        self.content.clear()
        self.content.set_visibility(False)
        self._last_markdown = None

    def add_code(self, code: str, lang: str = "python"):
        self.content.set_visibility(True)
        with self.content:
            ui.code(code, language=lang).classes("bg-gray-50 max-w-72 md:max-w-2xl")
            self._last_markdown = None

    def add_image(self, image: str | Path | Image):
        self.content.set_visibility(True)
        with self.content:
            ui.image(image).classes("max-w-72 md:max-w-2xl")
            self._last_markdown = None

    def finish(self, msg: ChatMessage):
        if msg.sent:
            return
        with self.items_container:
            self._build_actions(msg)

    def _build_actions(self, msg: ChatMessage):
        async def download():
            if msg.image:
                ui.download(msg.image)
            else:
                ui.notify("Nothing to download")

        def copy():
            ui.clipboard.write(msg.text)
            ui.notify("Copied to clipboard")

        async def on_like():
            msg.feedback.upvote = True
            msg.feedback.downvote = False
            like_btn.classes("text-green-500")
            dislike_btn.classes(remove="text-red-500")
            await db.upvote(conv_id=msg.conv_id, message_id=msg.id)

        async def on_dislike():
            msg.feedback.upvote = False
            msg.feedback.downvote = True
            like_btn.classes(remove="text-green-500")
            dislike_btn.classes("text-red-500")
            await db.downvote(conv_id=msg.conv_id, message_id=msg.id)

        async def toggle_log():
            if self.log_opened:
                self.log_drawer.hide()
            else:
                await self.on_details_click(message_id=self.msg_id, log_drawer=self.log_drawer)
                self.log_drawer.show()
            self.log_opened = not self.log_opened

        with ui.row().classes("w-fit px-2 -space-x-2 items-center"):
            _style = "text-gray-400 cursor-pointer rounded-lg p-1 hover:bg-gray-200"
            like_style = "text-green-500" if msg.feedback.upvote else "text-gray-400"
            dislike_style = "text-red-500" if msg.feedback.downvote else "text-gray-400"
            with ui.icon("thumb_up", size="xs").classes(_style + " " + like_style).on(
                "click", on_like
            ) as like_btn:
                ui.tooltip("Like").classes("text-white bg-slate-700 text-xs")
            with ui.icon("thumb_down", size="xs").classes(_style + " " + dislike_style).on(
                "click", on_dislike
            ) as dislike_btn:
                ui.tooltip("Dislike").classes("text-white bg-slate-700 text-xs")
            with ui.icon("info", size="xs").classes(_style).on("click", toggle_log).on(
                "blur", self.log_drawer.hide
            ):
                ui.tooltip("Details").classes("text-white bg-slate-700 text-xs")
            with ui.icon("content_copy", size="xs").classes(_style).on("click", copy):
                ui.tooltip("Copy to clipboard").classes("text-white bg-slate-700 text-xs")
            if msg.image:
                with ui.icon("download", size="xs").classes(_style).on("click", download):
                    ui.tooltip("Download").classes("text-white bg-slate-700 text-xs")
            ui.markdown(f"{iso_to_beijing(msg.create_time)}").classes(
                "text-md italic font-sans text-gray-500"
            )
        ui.run_javascript("window.scrollTo(0, document.body.scrollHeight)")

import anyio
import anyio.to_thread
from nicegui import APIRouter, ui

from ui.callback import PipelineCallback
from ui.db import db
from ui.db.schema import BotMessage, Conversation, UserMessage
from ui.frontend.components.message import Message
from ui.frontend.pages import main
from ui.frontend.users import user
from ui.tasks.create_title import task_create_title

router = APIRouter(prefix="/conv")


class Callback(main.Callback):
    async def on_conv_click(self, conv_id):
        ui.navigate.to(router.prefix + "/" + conv_id)

    async def on_conv_rename(self, conv_id, title):
        await db.rename_conv(conv_id, title)

    async def on_conv_delete(self, conv_id):
        await db.delete_conv(conv_id)

    async def on_details_click(self, message_id: str, log_drawer: main.LogDrawer):
        log_drawer.log.clear()
        log = await db.get_log(message_id)
        log_drawer.log.push(log)


class WelcomeCallback(Callback):
    async def _on_text_send(self, text: str | None = None, **kwargs):
        conv_id = await db.new_conv(user.user_id, text)
        async with anyio.create_task_group() as tg:
            tg.start_soon(task_create_title, text, conv_id)

        ui.navigate.to(router.prefix + "/" + conv_id)

    async def on_message_send(
        self, context, msg: ui.input, llm_filter, dont_show_user_message=False
    ):
        await self._on_text_send(
            msg.value, llm_filter=llm_filter, dont_show_user_message=dont_show_user_message
        )


def serialize_state(state: dict) -> dict:
    import dataclasses

    import pydantic

    ret = {
        k: v for k, v in state.items() if k not in ["schema", "table_dfs", "table_desc_dfs", "fig"]
    }
    for k in ret:
        if isinstance(ret[k], pydantic.BaseModel):
            ret[k] = ret[k].dict()
        if dataclasses.is_dataclass(ret[k]):
            ret[k] = dataclasses.asdict(ret[k])
    return ret


class ChatCallback(Callback):
    def __init__(self, conv: Conversation):
        super().__init__()
        self.conv = conv

    async def on_message_send(
        self,
        context: main.Context,
        msg: ui.input | None = None,
        llm_filter: bool = False,
        input_text="",
        dont_show_user_message=False,
    ):
        conv = self.conv
        if msg:
            input_text = msg.value
            msg.value = ""
        with context.content:
            if not dont_show_user_message:
                user_msg = UserMessage(conv_id=conv.id, text=input_text)
                Message(
                    user_msg, log_drawer=context.log_drawer, on_details_click=self.on_details_click
                )
                await db.append_message(conv.id, user_msg)
            bot_msg = BotMessage(conv_id=conv.id, text="", avatar=db.bot_avatar)
            ui_bot_message = Message(
                msg=bot_msg, log_drawer=context.log_drawer, on_details_click=self.on_details_click
            )
            ui_bot_message.show_spinner()

        cb = PipelineCallback(context, ui_bot_message, bot_msg)

        ui_bot_message.finish(cb.text_message)
        ui_bot_message.hide_spinner()


@router.page("/")
async def welcome_page():
    c = WelcomeCallback()
    with main.frame(c) as context:
        convs = await db.conversations(user.user_id)
        context.history_drawer.set_convs(convs)
        with ui.column().classes("mx-auto mt-40 w-2/3 h-full"):
            ui.button("Start a new conversation").on_click(c._on_text_send).props(
                "rounded dense"
            ).classes("px-4 py-2")
            ui.label("Or start from examples").classes("text-gray-500 mx-1 -my-1")
            with ui.column().classes("w-full -space-y-1 mx-1 items-start text-start"):
                for example in await db.examples():
                    ui.button(example).props("dense outline").classes("px-3").on(
                        "click", lambda example=example: c._on_text_send(example)
                    )


@router.page("/{conv_id}")
async def example_page(conv_id: str | None = None):
    conv = await db.get_conv(user_id=user.user_id, conv_id=conv_id)
    if conv is None:
        ui.notify("Conversation not found, redirecting to welcome page")
        return ui.navigate.to(router.prefix)

    callback = ChatCallback(conv)
    with main.frame(callback=callback) as context:
        from nicegui import background_tasks

        context.history_drawer.set_convs(await db.conversations(user.user_id))
        # TODO: render messages in background
        context.content.render_messages(
            conv.messages,
            log_drawer=context.log_drawer,
            on_details_click=callback.on_details_click,
        )
        if conv.need_reply():
            context.footer.text.value = conv.messages[-1].text

            async def task():
                with context.content:
                    await context.footer.send(dont_show_user_message=True)

            background_tasks.create(task())

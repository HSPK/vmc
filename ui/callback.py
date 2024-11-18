import json
import time
import uuid

from nicegui import ui
from ragkit.pipeline import TransformListener

from ui.db.schema import ChatMessage
from ui.frontend.components.message import Message
from ui.frontend.pages.main import Context


class PipelineCallback(TransformListener):
    def __init__(self, context: Context, ui_message: Message, text_message: ChatMessage):
        self.context = context
        self.ui_message = ui_message
        self.text_message = text_message
        self.log = context.log_drawer.log

        self.times = []
        self.log_text = ""
        self.figure_shown = False
        self.code_shown = False
        self.design_shown = True
        self.summary_shown = False
        self.answer_shown = False
        self.rewritten_question_shown = False
        self.code_printed = False

    async def on_transform_enter(self, transform, state):
        if not self.times:
            print(f"[Question] {state['question']}")
        print(f"[Processing] {transform.name}")
        self.times.append(time.time())
        self.log.push(f"[Processing] {transform.name}")
        self.log_text += f"[Processing] {transform.name}\n"
        text = transform.description.strip()
        if text:
            self.ui_message.update_text(text + "\n\n")
            self.text_message.update_text(text + "\n\n")
            ui.run_javascript("window.scrollTo(0, document.body.scrollHeight)")

    async def on_transform_exit(self, transform, state):
        last_time = self.times.pop()
        log_text = f"[Exit] {transform.name}({time.time() - last_time:.2f}s used)"
        print(log_text)
        self.log.push(log_text)
        self.log_text += log_text + "\n"
        if len(self.times) == 0:
            state["log"] = self.log_text

        if "chart_design" in state and not self.design_shown:
            json_text = json.dumps(state["chart_design"], indent=2, ensure_ascii=False)
            self.design_shown = True
            self.ui_message.add_code(json_text)
            self.text_message.update_code(json_text, lang="json")
        if "fig" in state and not self.figure_shown:
            self.figure_shown = True
            fig = state["fig"]
            fig_name = "tmp/" + str(uuid.uuid4()) + ".png"
            fig.savefig(fig_name)
            self.ui_message.add_image(fig_name)
            self.text_message.update_image(fig_name)
        if "code" in state and not self.code_printed:
            print(state["code"])
            self.code_printed = True
        if "code" in state and not self.code_shown:
            self.code_shown = True
            code = state["code"]
            self.ui_message.add_code(code)
            self.text_message.update_code(code)
        if "summary" in state and not self.summary_shown:
            self.summary_shown = True
            text = state["summary"]
            self.ui_message.update_text(text)
            self.text_message.update_text(text)
        if "answer" in state and not self.answer_shown:
            self.answer_shown = True
            text = state["answer"]
            self.ui_message.update_text(text)
            self.text_message.update_text(text)
        if "rewritten_question" in state and not self.rewritten_question_shown:
            self.rewritten_question_shown = True
            text = state["rewritten_question"]
            text = f"猜您想问：{text}\n\n"
            self.ui_message.update_text(text)
            self.text_message.update_text(text)
        ui.run_javascript("window.scrollTo(0, document.body.scrollHeight)")

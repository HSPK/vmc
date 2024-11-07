import uuid
import warnings
from typing import Literal, Union

import pydantic
from pydantic import Field

from ui.db.utils import iso_datetime


class BaseModel(pydantic.BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    create_time: str = Field(default_factory=iso_datetime)
    update_time: str = Field(default_factory=iso_datetime)


class Feedback(pydantic.BaseModel):
    upvote: bool = False
    downvote: bool = False


class MessageBlock(pydantic.BaseModel):
    type: Literal["text", "image", "code", "chart"] = "text"


class MessageTextBlock(MessageBlock):
    type: Literal["text"] = "text"
    text: str


class MessageImageBlock(MessageBlock):
    type: Literal["image"] = "image"
    url: str


class MessageCodeBlock(MessageBlock):
    type: Literal["code"] = "code"
    code: str
    lang: str = "python"


class MessageChartBlock(MessageBlock):
    type: Literal["chart"] = "chart"
    chart: str
    data: dict


BlockType = Union[MessageTextBlock, MessageImageBlock, MessageCodeBlock, MessageChartBlock]


class ChatMessage(BaseModel):
    conv_id: str = ""
    text: str = ""
    sent: bool = False
    avatar: str | None = None
    feedback: Feedback = Feedback()
    image: str | None = None
    blocks: list[BlockType] = []

    def update_text(self, text: str, mode: Literal["append", "replace"] = "append"):
        if len(self.blocks) == 0:
            self.blocks.append(MessageTextBlock(text=text))
        else:
            last_block = self.blocks[-1]
            if last_block.type == "text":
                if mode == "append":
                    last_block.text += text
                else:
                    last_block.text = text
            else:
                self.blocks.append(MessageTextBlock(text=text))

    def update_code(self, code: str, lang: str = "python"):
        self.blocks.append(MessageCodeBlock(code=code, lang=lang))

    def update_image(self, url: str):
        self.blocks.append(MessageImageBlock(url=url))
        if self.image is None:
            warnings.warn("The image attribute is deprecated, use the image block instead.")
        self.image = url

    def update_chart(self, chart: str, data: dict):
        self.blocks.append(MessageChartBlock(chart=chart, data=data))


class UserMessage(ChatMessage):
    sent: bool = True


class BotMessage(ChatMessage):
    sent: bool = False


class Conversation(BaseModel):
    user_id: str
    title: str
    messages: list[ChatMessage]

    def summary(self):
        return ConvSummary(
            id=self.id,
            user_id=self.user_id,
            title=self.title,
            last_message=self.messages[-1].text,
            last_message_time=self.messages[-1].update_time,
        )

    def need_reply(self):
        """Check if the conversation needs a reply immediately when is new."""
        return self.messages[-1].sent


class ConvSummary(BaseModel):
    user_id: str
    title: str
    last_message: str
    last_message_time: str

from typing import Any, Dict, Iterable, List, Optional, TypeAlias, Union

from typing_extensions import Literal

from .._base import BaseModel


class ImageURL(BaseModel):
    url: str
    """Either a URL of the image or the base64 encoded image data."""

    detail: Literal["auto", "low", "high"]
    """Specifies the detail level of the image.

    Learn more in the
    [Vision guide](https://platform.openai.com/docs/guides/vision/low-or-high-fidelity-image-understanding).
    """


class ContentPartText(BaseModel):
    text: str
    """The text content."""

    type: Literal["text"] = "text"
    """The type of the content part."""


class ContentPartImage(BaseModel):
    image_url: ImageURL

    type: Literal["image"] = "image"
    """The type of the content part."""


class ContentPartRefusal(BaseModel):
    refusal: str
    """The refusal message generated by the model."""

    type: Literal["refusal"] = "refusal"
    """The type of the content part."""


UserContentType: TypeAlias = Union[ContentPartText, ContentPartImage]
AIContentType = Union[ContentPartText, ContentPartRefusal]


class BaseMessage(BaseModel):
    role: str
    content: str


class SystemMessage(BaseMessage):
    role: str = "system"


class UserMessage(BaseMessage):
    role: str = "user"
    name: Optional[str] = None
    content: Union[str, Iterable[UserContentType]]


class Function(BaseModel):
    arguments: str
    """
    The arguments to call the function with, as generated by the model in JSON
    format. Note that the model does not always generate valid JSON, and may
    hallucinate parameters not defined by your function schema. Validate the
    arguments in your code before calling your function.
    """

    name: str
    """The name of the function to call."""


class ChatCompletionMessageToolCallParam(BaseModel):
    id: str
    """The ID of the tool call."""

    function: Function
    """The function that the model called."""

    type: Literal["function"] = "function"
    """The type of the tool. Currently, only `function` is supported."""


class AIMessage(BaseMessage):
    role: str = "assistant"
    content: Union[str, Iterable[AIContentType], None] = None
    name: Optional[str] = None
    refusal: Optional[str] = None
    tool_calls: Iterable[ChatCompletionMessageToolCallParam] = []


class ToolMessage(BaseMessage):
    role: str = "tool"
    content: Union[str, Iterable[ContentPartText]]
    tool_call_id: str


ContentType = Union[SystemMessage, UserMessage, AIMessage, ToolMessage]


def convert_dicts_to_messages(dicts: List[Dict[str, Any]]) -> List[ContentType]:
    """Convert a list of dicts to a list of messages"""
    messages = []
    for d in dicts:
        if d["role"] == "system":
            messages.append(SystemMessage(**d))
        elif d["role"] == "user":
            messages.append(UserMessage(**d))
        elif d["role"] == "assistant":
            messages.append(AIMessage(**d))
        elif d["role"] == "tool":
            messages.append(ToolMessage(**d))
        else:
            messages.append(ContentType(**d))
    return messages
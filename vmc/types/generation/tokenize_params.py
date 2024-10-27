from typing_extensions import Iterable, Literal, TypedDict, Union

from .message_params import GenerationMessageParam


class TokenizeParams(TypedDict, total=False):
    content: Union[str, Iterable[str], Iterable[GenerationMessageParam]]
    model: str
    allowed_special: Union[Literal["all"], Iterable[str]]
    disallowed_special: Union[Literal["all"], Iterable[str]]
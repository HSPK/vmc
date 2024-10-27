from typing import Dict, Iterable, List, Literal, Optional, TypeAlias, Union

from typing_extensions import Required, TypedDict

from ..shared_params.response_format import (
    ResponseFormatJSONObject,
    ResponseFormatJSONSchema,
    ResponseFormatText,
)
from .message_params import GenerationMessageParam
from .tool_choice_option_param import ChatCompletionToolChoiceOptionParam
from .tool_param import ChatCompletionToolParam

ResponseFormat: TypeAlias = Union[
    ResponseFormatText, ResponseFormatJSONObject, ResponseFormatJSONSchema
]


class GenerationParams(TypedDict, total=False):
    content: Union[str, List[GenerationMessageParam]]
    model: Required[str]
    frequency_penalty: Optional[float]
    logit_bias: Optional[Dict[str, int]]
    logprobs: Optional[bool]
    max_completion_tokens: Optional[int]
    max_tokens: Optional[int]
    metadata: Optional[Dict[str, str]]
    n: Optional[int]
    parallel_tool_calls: bool
    presence_penalty: Optional[float]
    response_format: ResponseFormat
    seed: Optional[int]
    service_tier: Optional[Literal["auto", "default"]]
    stop: Union[Optional[str], List[str]]
    temperature: Optional[float]
    tool_choice: ChatCompletionToolChoiceOptionParam
    tools: Iterable[ChatCompletionToolParam]
    top_logprobs: Optional[int]
    top_p: Optional[float]
    user: str
    stream: bool
    return_original_response: bool


class BatchGenerationParams(GenerationParams):
    content: Union[List[str], List[List[GenerationMessageParam]]]

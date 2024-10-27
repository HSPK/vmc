import os
from io import TextIOWrapper
from typing import Any, Dict, Iterable, List, Literal, Optional, Union

import httpx

from vmcc.types import (
    ContentType,
    EmbeddingResponse,
    Generation,
    GenerationChunk,
    ModelInfoOutput,
    RerankOutput,
    TokenizeOutput,
    Transcription,
)
from vmcc.types.generation.generation_params import (
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
    ResponseFormat,
)

from ._async_client import AsyncAPIClient
from ._constants import DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT
from .types._types import NOT_GIVEN, NotGiven


def filter_not_given(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in kwargs.items() if v is not NOT_GIVEN}


class AsyncVMC:
    def __init__(
        self,
        host: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: Optional[int] = DEFAULT_MAX_RETRIES,
        timeout: Optional[httpx.Timeout] = DEFAULT_TIMEOUT,
    ):
        base_url = host or os.getenv("VMC_BASE_URL")
        username = username or os.getenv("VMC_USERNAME")
        password = password or os.getenv("VMC_PASSWORD")
        if not base_url:
            raise ValueError("host URL is required")
        params = {
            "base_url": base_url,
            "max_retries": max_retries,
            "timeout": timeout,
            "auth_headers": {"Authorization": f"{username}:{password}"},
        }
        self._default_model = model
        self._client = AsyncAPIClient(**params)
        self._get = self._client.get
        self._post = self._client.post
        self._stream = self._client.stream

    async def _process_prompt(self, content: ContentType):
        if isinstance(content, str):
            content = await self._replace_image_with_id(content)
        return content

    async def _upload_image(self, image_path: str):
        res = await self._post(
            "image/upload",
            options={"files": {"file": open(image_path, "rb")}},
            cast_to=Dict,
        )
        return res.json()["id"]

    async def _replace_image_with_id(self, s: str):
        """extract image path from a markdown string"""
        import re

        match = re.fullmatch(r"!\[(.*?)\]\((.*?)\)", s)
        if not match:
            return s
        image_path = match.group(2)
        if not os.path.exists(image_path):
            return s
        image_id = await self._upload_image(image_path)
        return f"![{match.group(1)}]({image_id})"

    async def tokenize(
        self,
        prompt: ContentType,
        model: Optional[str] = None,
        params: Optional[Dict[str, Any]] = {},
        timeout: Optional[httpx.Timeout] = None,
        **kwargs,
    ) -> int:
        res = self._post(
            "tokenize",
            body={
                "prompt": self._process_prompt(prompt),
                "model": model or self._default_model,
                "params": {**params, **kwargs},
            },
            cast_to=TokenizeOutput,
            options={"timeout": timeout},
        )
        return res.n_tokens

    async def generate(
        self,
        content: Union[str, Iterable[ContentType]],
        *,
        frequency_penalty: Optional[float] | NotGiven = NOT_GIVEN,
        logit_bias: Optional[Dict[str, int]] | NotGiven = NOT_GIVEN,
        logprobs: Optional[bool] | NotGiven = NOT_GIVEN,
        max_completion_tokens: Optional[int] | NotGiven = NOT_GIVEN,
        max_tokens: Optional[int] | NotGiven = NOT_GIVEN,
        metadata: Optional[Dict[str, str]] | NotGiven = NOT_GIVEN,
        n: Optional[int] | NotGiven = NOT_GIVEN,
        parallel_tool_calls: bool | NotGiven = NOT_GIVEN,
        presence_penalty: Optional[float] | NotGiven = NOT_GIVEN,
        response_format: ResponseFormat | NotGiven = NOT_GIVEN,
        seed: Optional[int] | NotGiven = NOT_GIVEN,
        service_tier: Optional[Literal["auto", "default"]] | NotGiven = NOT_GIVEN,
        stop: Union[Optional[str], List[str]] | NotGiven = NOT_GIVEN,
        store: Optional[bool] | NotGiven = NOT_GIVEN,
        temperature: Optional[float] | NotGiven = NOT_GIVEN,
        tool_choice: ChatCompletionToolChoiceOptionParam | NotGiven = NOT_GIVEN,
        tools: Iterable[ChatCompletionToolParam] | NotGiven = NOT_GIVEN,
        top_logprobs: Optional[int] | NotGiven = NOT_GIVEN,
        top_p: Optional[float] | NotGiven = NOT_GIVEN,
        user: str | NotGiven = NOT_GIVEN,
        timeout: float | httpx.Timeout | None = None,
        return_original_response: bool | NotGiven = NOT_GIVEN,
        **kwargs,
    ) -> Generation:
        return await self._post(
            "generate",
            body=filter_not_given(
                {
                    "content": self._process_prompt(content),
                    "model": self._default_model,
                    "frequency_penalty": frequency_penalty,
                    "logit_bias": logit_bias,
                    "logprobs": logprobs,
                    "max_completion_tokens": max_completion_tokens,
                    "max_tokens": max_tokens,
                    "metadata": metadata,
                    "n": n,
                    "parallel_tool_calls": parallel_tool_calls,
                    "presence_penalty": presence_penalty,
                    "response_format": response_format,
                    "seed": seed,
                    "service_tier": service_tier,
                    "stop": stop,
                    "store": store,
                    "temperature": temperature,
                    "tool_choice": tool_choice,
                    "tools": tools,
                    "top_logprobs": top_logprobs,
                    "top_p": top_p,
                    "user": user,
                    "return_original_response": return_original_response,
                    **kwargs,
                }
            ),
            cast_to=Generation,
            options={"timeout": timeout},
        )

    async def stream(
        self,
        content: Union[str, Iterable[ContentType]],
        *,
        frequency_penalty: Optional[float] | NotGiven = NOT_GIVEN,
        logit_bias: Optional[Dict[str, int]] | NotGiven = NOT_GIVEN,
        logprobs: Optional[bool] | NotGiven = NOT_GIVEN,
        max_completion_tokens: Optional[int] | NotGiven = NOT_GIVEN,
        max_tokens: Optional[int] | NotGiven = NOT_GIVEN,
        metadata: Optional[Dict[str, str]] | NotGiven = NOT_GIVEN,
        n: Optional[int] | NotGiven = NOT_GIVEN,
        parallel_tool_calls: bool | NotGiven = NOT_GIVEN,
        presence_penalty: Optional[float] | NotGiven = NOT_GIVEN,
        response_format: ResponseFormat | NotGiven = NOT_GIVEN,
        seed: Optional[int] | NotGiven = NOT_GIVEN,
        service_tier: Optional[Literal["auto", "default"]] | NotGiven = NOT_GIVEN,
        stop: Union[Optional[str], List[str]] | NotGiven = NOT_GIVEN,
        store: Optional[bool] | NotGiven = NOT_GIVEN,
        temperature: Optional[float] | NotGiven = NOT_GIVEN,
        tool_choice: ChatCompletionToolChoiceOptionParam | NotGiven = NOT_GIVEN,
        tools: Iterable[ChatCompletionToolParam] | NotGiven = NOT_GIVEN,
        top_logprobs: Optional[int] | NotGiven = NOT_GIVEN,
        top_p: Optional[float] | NotGiven = NOT_GIVEN,
        user: str | NotGiven = NOT_GIVEN,
        timeout: float | httpx.Timeout | None = None,
        return_original_response: bool | NotGiven = NOT_GIVEN,
        **kwargs,
    ):
        async for t in await self._stream(
            "generate",
            body=filter_not_given(
                {
                    "content": self._process_prompt(content),
                    "model": self._default_model,
                    "frequency_penalty": frequency_penalty,
                    "logit_bias": logit_bias,
                    "logprobs": logprobs,
                    "max_completion_tokens": max_completion_tokens,
                    "max_tokens": max_tokens,
                    "metadata": metadata,
                    "n": n,
                    "parallel_tool_calls": parallel_tool_calls,
                    "presence_penalty": presence_penalty,
                    "response_format": response_format,
                    "seed": seed,
                    "service_tier": service_tier,
                    "stop": stop,
                    "store": store,
                    "temperature": temperature,
                    "tool_choice": tool_choice,
                    "tools": tools,
                    "top_logprobs": top_logprobs,
                    "top_p": top_p,
                    "user": user,
                    "return_original_response": return_original_response,
                    "stream": True,
                    **kwargs,
                }
            ),
            cast_to=GenerationChunk,
            options={"timeout": timeout},
        ):
            yield t

    async def embedding(
        self,
        content: Union[str, List[str]],
        *,
        model: str,
        encoding_format: Literal["float", "base64"] | NotGiven = NOT_GIVEN,
        user: str | NotGiven = NOT_GIVEN,
        dimensions: int | NotGiven = NOT_GIVEN,
        return_sparse: bool | NotGiven = NOT_GIVEN,
        timeout: float | httpx.Timeout | None = None,
        **kwargs,
    ) -> EmbeddingResponse:
        return await self._post(
            "embedding",
            body=filter_not_given(
                {
                    "content": content,
                    "model": model,
                    "encoding_format": encoding_format,
                    "user": user,
                    "dimensions": dimensions,
                    "return_sparse": return_sparse,
                    **kwargs,
                }
            ),
            cast_to=EmbeddingResponse,
            options={"timeout": timeout},
        )

    async def rerank(
        self,
        sentences: List[List[str]],
        *,
        model: str,
        apply_softmax: bool | NotGiven = NOT_GIVEN,
        timeout: Optional[httpx.Timeout] = None,
        **kwargs,
    ) -> RerankOutput:
        return await self._post(
            "rerank",
            body=filter_not_given(
                {
                    "sentences": sentences,
                    "model": model,
                    "apply_softmax": apply_softmax,
                    **kwargs,
                }
            ),
            cast_to=RerankOutput,
            options={"timeout": timeout},
        )

    async def transcribe(
        self,
        file: Union[str, TextIOWrapper],
        *,
        model: str,
        language: str | NotGiven = NOT_GIVEN,
        temperature: float | NotGiven = NOT_GIVEN,
        timeout: Optional[httpx.Timeout] = None,
    ) -> Transcription:
        model = model or self.model
        if isinstance(file, str):
            file = open(file, "rb")

        return await self._post(
            "audio/transcriptions",
            files={"file": file},
            data=filter_not_given(
                {
                    "model": model,
                    "language": language,
                    "temperature": temperature,
                }
            ),
            cast_to=Transcription,
            options={"timeout": timeout},
        )

    async def get_supported_models(self) -> ModelInfoOutput:
        response = await self._get("models", cast_to=ModelInfoOutput)
        return response.models

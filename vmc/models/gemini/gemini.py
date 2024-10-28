import os
import time
from contextlib import nullcontext
from typing import (
    AsyncGenerator,
    Iterable,
    List,
    Optional,
    Union,
)

import google.generativeai as genai
import httpx
from google.generativeai.types.content_types import ContentsType
from google.generativeai.types.generation_types import GenerationConfigType
from loguru import logger

from vmc.models.embedding import BaseEmbeddingModel
from vmc.models.generation import BaseGenerationModel
from vmc.types import NOT_GIVEN, NotGiven
from vmc.types.embedding import EmbeddingResponse
from vmc.types.errors.errors import BadParamsError
from vmc.types.generation.generation import Generation
from vmc.types.generation.generation_chunk import GenerationChunk
from vmc.types.generation.generation_params import ResponseFormat
from vmc.types.generation.message_params import GenerationMessageParam
from vmc.types.generation.tokenize import TokenizeOutput
from vmc.types.generation.tool_param import ChatCompletionToolParam
from vmc.utils.proxy import use_proxy

from .response_adapter import adapt_generation, adapt_generation_chunk, gen_generation_id


def filter_notgiven(**kwargs):
    return {k: v for k, v in kwargs.items() if v is not NOT_GIVEN}


class Gemini(BaseGenerationModel, BaseEmbeddingModel):
    def __init__(self, max_retries: int = 3, use_proxy: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_retries = max_retries
        self.use_proxy = use_proxy

    def validate_credential(self, credential: dict[str, str]):
        assert "api_key" in credential or os.environ.get(
            "GOOGLE_API_KEY"
        ), "api_key or GOOLE_API_KEY is required"
        return True

    @property
    def client(self):
        genai.configure(**self.set_credential())
        return genai.GenerativeModel(self.model_id)

    def prepare_contents(
        self,
        content: Union[str, List[GenerationMessageParam]],
        tools: Iterable[ChatCompletionToolParam],
    ) -> ContentsType:
        role_map = {"user": "user", "bot": "bot", "system": "model", "assistant": "model"}

        if isinstance(content, str):
            return [{"role": "user", "parts": [content]}]
        new_content = []
        for c in content:
            if not isinstance(c, GenerationMessageParam):
                raise BadParamsError("content must be of type GenerationMessageParam")
            role = role_map.get(c["role"])
            if role is None:
                raise BadParamsError(f"Invalid role {c['role']}")
            new_content.append({"role": role, "parts": [c["content"]]})
        return new_content

    def prepare_generation_args(
        self,
        max_tokens: Optional[int] | NotGiven = NOT_GIVEN,
        n: Optional[int] | NotGiven = NOT_GIVEN,
        response_format: ResponseFormat | NotGiven = NOT_GIVEN,
        stop: Union[Optional[str], List[str]] | NotGiven = NOT_GIVEN,
        temperature: Optional[float] | NotGiven = NOT_GIVEN,
        tools: Iterable[ChatCompletionToolParam] | NotGiven = NOT_GIVEN,
        top_p: Optional[float] | NotGiven = NOT_GIVEN,
        top_k: Optional[int] | NotGiven = NOT_GIVEN,
    ):
        generation_config: GenerationConfigType = {}

        if n is not NOT_GIVEN:
            generation_config["candidate_count"] = n
        if max_tokens is not NOT_GIVEN:
            generation_config["max_output_tokens"] = max_tokens
        if response_format is not NOT_GIVEN:
            if response_format["type"] == "text":
                generation_config["response_mime_type"] = "text/plain"
            elif response_format["type"] == "json_object":
                generation_config["response_mime_type"] = "application/json"
            elif response_format["type"] == "json_schema":
                generation_config["response_mime_type"] = "application/json"
                generation_config["response_schema"] = response_format["json_schema"]
        if temperature is not NOT_GIVEN:
            generation_config["temperature"] = temperature
        if stop is not NOT_GIVEN:
            generation_config["stop_sequences"] = stop
        if top_p is not NOT_GIVEN:
            generation_config["top_p"] = top_p
        if top_k is not NOT_GIVEN:
            generation_config["top_k"] = top_k
        return generation_config

    async def generate(
        self,
        content: Union[str, Iterable[GenerationMessageParam]],
        max_tokens: Optional[int] | NotGiven = NOT_GIVEN,
        n: Optional[int] | NotGiven = NOT_GIVEN,
        response_format: ResponseFormat | NotGiven = NOT_GIVEN,
        stop: Union[Optional[str], List[str]] | NotGiven = NOT_GIVEN,
        temperature: Optional[float] | NotGiven = NOT_GIVEN,
        tools: Iterable[ChatCompletionToolParam] | NotGiven = NOT_GIVEN,
        top_p: Optional[float] | NotGiven = NOT_GIVEN,
        top_k: Optional[int] | NotGiven = NOT_GIVEN,
        timeout: float | httpx.Timeout | None = None,
        return_original_response: bool = False,
        **kwargs,
    ) -> Generation:
        if kwargs:
            logger.warning(f"{self.model_id} Unused parameters: {kwargs}")
        generation_config = self.prepare_generation_args(
            max_tokens=max_tokens,
            n=n,
            response_format=response_format,
            stop=stop,
            temperature=temperature,
            tools=tools,
            top_p=top_p,
            top_k=top_k,
        )

        created = time.time()
        context = nullcontext() if not self.use_proxy else use_proxy()
        with context:
            res = await self.client.generate_content_async(
                contents=self.prepare_contents(content, tools),
                generation_config=generation_config,
                request_options={"timeout": timeout},
            )
        return adapt_generation(
            res,
            model=self.model_id,
            pricing=self.pricing,
            created=created,
            return_raw_response=return_original_response,
        )

    async def stream(
        self,
        content: Union[str, Iterable[GenerationMessageParam]],
        max_tokens: Optional[int] | NotGiven = NOT_GIVEN,
        n: Optional[int] | NotGiven = NOT_GIVEN,
        response_format: ResponseFormat | NotGiven = NOT_GIVEN,
        stop: Union[Optional[str], List[str]] | NotGiven = NOT_GIVEN,
        temperature: Optional[float] | NotGiven = NOT_GIVEN,
        tools: Iterable[ChatCompletionToolParam] | NotGiven = NOT_GIVEN,
        top_p: Optional[float] | NotGiven = NOT_GIVEN,
        top_k: Optional[int] | NotGiven = NOT_GIVEN,
        timeout: float | httpx.Timeout | None = None,
        return_original_response: bool = False,
        stream: bool = True,
        **kwargs,
    ) -> AsyncGenerator[GenerationChunk, None]:
        if kwargs:
            logger.warning(f"{self.model_id} Unused parameters: {kwargs}")
        generation_config = self.prepare_generation_args(
            max_tokens=max_tokens,
            n=n,
            response_format=response_format,
            stop=stop,
            temperature=temperature,
            tools=tools,
            top_p=top_p,
            top_k=top_k,
        )

        created = time.time()
        context = nullcontext() if not self.use_proxy else use_proxy()
        gid = gen_generation_id()
        with context:
            async for chunk in await self.client.generate_content_async(
                contents=self.prepare_contents(content, tools),
                generation_config=generation_config,
                request_options={"timeout": timeout},
                stream=stream,
            ):
                yield adapt_generation_chunk(
                    chunk,
                    id=gid,
                    model=self.model_id,
                    pricing=self.pricing,
                    created=created,
                    return_raw_response=return_original_response,
                )

    async def tokenize(
        self,
        content: Union[str, Iterable[str], Iterable[GenerationMessageParam]],
        **kwargs,
    ) -> TokenizeOutput:
        if kwargs:
            logger.warning(f"{self.model_id} Unused parameters: {kwargs}")
        res = await self.client.count_tokens_async(contents=self.prepare_contents(content, []))
        return TokenizeOutput(tokens=[], length=res.total_tokens)

    async def embedding(
        self,
        content: Union[str, List[str], Iterable[int], Iterable[Iterable[int]]],
        *,
        dimensions: int | NotGiven = NOT_GIVEN,
        task_type: str | NotGiven = NOT_GIVEN,
        title: str | NotGiven = NOT_GIVEN,
        **kwargs,
    ) -> EmbeddingResponse:
        if kwargs:
            logger.warning(f"{self.model_id} Unused parameters: {kwargs}")
        created = time.time()
        genai.configure(**self.set_credential())
        res = await genai.embed_content_async(
            model=self.model_id,
            content=content,
            **filter_notgiven(
                task_type=task_type,
                title=title,
                output_dimensionality=dimensions,
            ),
        )
        return EmbeddingResponse(
            created=created,
            embed_time=time.time() - created,
            embedding=res["embedding"],
            model=self.model_id,
        )

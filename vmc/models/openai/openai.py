import os
import time
from typing import (
    AbstractSet,
    AsyncGenerator,
    Collection,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    Union,
)

import httpx
import tiktoken
from loguru import logger
from openai import AsyncAzureOpenAI, AsyncOpenAI
from openai._types import Body, Headers, Query
from openai.types.chat import completion_create_params
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_stream_options_param import ChatCompletionStreamOptionsParam
from openai.types.chat.chat_completion_tool_choice_option_param import (
    ChatCompletionToolChoiceOptionParam,
)
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
from openai.types.chat_model import ChatModel

from vmc.models.embedding import BaseEmbeddingModel
from vmc.models.generation import BaseGenerationModel
from vmc.types import NOT_GIVEN, NotGiven
from vmc.types.embedding import EmbeddingResponse
from vmc.types.errors.errors import ModelNotFoundError
from vmc.types.generation import Generation, GenerationChunk, TokenizeOutput
from vmc.types.generation.message_params import GenerationMessageParam

from .response_adapter import adapt_completion, adapt_completion_chunk, adapt_embedding


class OpenAIConfig:
    max_retries: int = 5
    base_url: str | None = None

    model: Union[str, ChatModel]
    frequency_penalty: Optional[float] | None = None
    max_completion_tokens: Optional[int] | None = None
    max_tokens: Optional[int] | None = None
    parallel_tool_calls: bool | None = None
    presence_penalty: Optional[float] | None = None
    response_format: completion_create_params.ResponseFormat | None = None
    seed: Optional[int] | None = None
    service_tier: Optional[Literal["auto", "default"]] | None = None
    stop: Union[Optional[str], List[str]] | None = None
    store: Optional[bool] | None = None
    stream: Optional[Literal[False]] | Literal[True] | None = None
    stream_options: Optional[ChatCompletionStreamOptionsParam] | None = None
    temperature: Optional[float] | None = None
    tool_choice: ChatCompletionToolChoiceOptionParam | None = None
    tools: Iterable[ChatCompletionToolParam] | None = None
    top_logprobs: Optional[int] | None = None
    top_p: Optional[float] | None = None
    user: str | None = None
    timeout: httpx.Timeout = httpx.Timeout(timeout=600.0, connect=30.0)


def filter_notgiven(**kwargs):
    return {k: v for k, v in kwargs.items() if v is not NOT_GIVEN}


class OpenAI(BaseGenerationModel, BaseEmbeddingModel):
    def __init__(
        self,
        max_retries: int | None = None,
        timeout: httpx.Timeout | None = None,
        use_proxy: bool = False,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.max_retries = max_retries or OpenAIConfig.max_retries
        self.timeout = timeout or OpenAIConfig.timeout
        self.use_proxy = use_proxy

    def validate_credential(self, credential: dict[str, str]):
        assert (
            "OPENAI_API_KEY" in os.environ or "api_key" in credential
        ), "OpenAI API key is required"

    def prepare_content(
        self, content: Union[str, List[GenerationMessageParam]]
    ) -> ChatCompletionMessageParam:
        if isinstance(content, str):
            return [{"role": "user", "content": content}]
        return content

    async def generate(
        self,
        content: Union[str, Iterable[GenerationMessageParam]],
        frequency_penalty: Optional[float] | NotGiven = NOT_GIVEN,
        logit_bias: Optional[Dict[str, int]] | NotGiven = NOT_GIVEN,
        logprobs: Optional[bool] | NotGiven = NOT_GIVEN,
        max_completion_tokens: Optional[int] | NotGiven = NOT_GIVEN,
        max_tokens: Optional[int] | NotGiven = NOT_GIVEN,
        metadata: Optional[Dict[str, str]] | NotGiven = NOT_GIVEN,
        n: Optional[int] | NotGiven = NOT_GIVEN,
        parallel_tool_calls: bool | NotGiven = NOT_GIVEN,
        presence_penalty: Optional[float] | NotGiven = NOT_GIVEN,
        response_format: completion_create_params.ResponseFormat | NotGiven = NOT_GIVEN,
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
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
        return_original_response: bool = False,
        **kwargs,
    ) -> Generation:
        if kwargs:
            logger.warning(f"{self.model_id} Unused arguments: {kwargs}")
        created = time.time()
        completion = await self.client.chat.completions.create(
            **filter_notgiven(
                messages=self.prepare_content(content),
                model=self.model_id,
                frequency_penalty=frequency_penalty,
                logit_bias=logit_bias,
                logprobs=logprobs,
                max_completion_tokens=max_completion_tokens,
                max_tokens=max_tokens,
                metadata=metadata,
                n=n,
                parallel_tool_calls=parallel_tool_calls,
                presence_penalty=presence_penalty,
                response_format=response_format,
                seed=seed,
                service_tier=service_tier,
                stop=stop,
                store=store,
                temperature=temperature,
                tool_choice=tool_choice,
                tools=tools,
                top_logprobs=top_logprobs,
                top_p=top_p,
                user=user,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            )
        )
        return adapt_completion(
            completion, self.pricing, created=created, return_original=return_original_response
        )

    @property
    def client(self):
        credential = self.set_credential()
        httpx_client = None
        if self.use_proxy and os.getenv("_HTTP_PROXY", None) and os.getenv("_HTTPS_PROXY", None):
            httpx_client = httpx.AsyncClient(
                proxies={
                    "http_proxy://": os.getenv("_HTTP_PROXY", None),
                    "https_proxy://": os.getenv("_HTTPS_PROXY", None),
                }
            )
        client_type = credential.get("client_type", "openai")
        if client_type == "openai":
            return AsyncOpenAI(
                api_key=credential.get("api_key"),
                base_url=credential.get("base_url"),
                max_retries=self.max_retries,
                timeout=self.timeout,
                http_client=httpx_client,
            )
        elif client_type == "azure":
            return AsyncAzureOpenAI(
                azure_endpoint=credential.get("azure_endpoint"),
                azure_deployment=credential.get("azure_deployment"),
                api_version=credential.get("api_version"),
                api_key=credential.get("api_key"),
                organization=credential.get("organization"),
                max_retries=self.max_retries,
                timeout=self.timeout,
                http_client=httpx_client,
            )
        else:
            raise ValueError(f"Invalid client type: {client_type}")

    async def tokenize(
        self,
        content: Union[str, Iterable[GenerationMessageParam], Iterable[str]],
        *,
        allowed_special: Union[Literal["all"], AbstractSet[str]] = set(),
        disallowed_special: Union[Literal["all"], Collection[str]] = "all",
        **kwargs,
    ):
        if kwargs:
            logger.warning(f"{self.model_id} Unused arguments: {kwargs}")
        is_content_str = isinstance(content, str)
        if is_content_str:
            content = [content]
        tokens = []
        length = []
        try:
            enc = tiktoken.encoding_for_model(self.model_id)
        except Exception:
            raise ModelNotFoundError(msg=f"Tokenizer not found for model {self.model_id}") from None
        for c in content:
            assert isinstance(c, str), f"Invalid content type: {type(c)}"
            _tokens = enc.encode(
                c, allowed_special=allowed_special, disallowed_special=disallowed_special
            )
            tokens.append(_tokens)
            length.append(len(_tokens))
        if is_content_str:
            tokens = tokens[0]
            length = length[0]
        return TokenizeOutput(tokens=tokens, length=length)

    async def stream(
        self,
        content: Union[str, Iterable[GenerationMessageParam]],
        frequency_penalty: Optional[float] | NotGiven = NOT_GIVEN,
        logit_bias: Optional[Dict[str, int]] | NotGiven = NOT_GIVEN,
        logprobs: Optional[bool] | NotGiven = NOT_GIVEN,
        max_completion_tokens: Optional[int] | NotGiven = NOT_GIVEN,
        max_tokens: Optional[int] | NotGiven = NOT_GIVEN,
        metadata: Optional[Dict[str, str]] | NotGiven = NOT_GIVEN,
        n: Optional[int] | NotGiven = NOT_GIVEN,
        parallel_tool_calls: bool | NotGiven = NOT_GIVEN,
        presence_penalty: Optional[float] | NotGiven = NOT_GIVEN,
        response_format: completion_create_params.ResponseFormat | NotGiven = NOT_GIVEN,
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
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
        return_original_response: bool = False,
        **kwargs,
    ) -> AsyncGenerator[GenerationChunk, None]:
        if kwargs:
            logger.warning(f"{self.model_id} Unused arguments: {kwargs}")
        created = time.time()
        first_chunk = None
        last_chunk = None
        async for chunk in await self.client.chat.completions.create(
            **filter_notgiven(
                messages=self.prepare_content(content),
                model=self.model_id,
                frequency_penalty=frequency_penalty,
                logit_bias=logit_bias,
                logprobs=logprobs,
                max_completion_tokens=max_completion_tokens,
                max_tokens=max_tokens,
                metadata=metadata,
                n=n,
                parallel_tool_calls=parallel_tool_calls,
                presence_penalty=presence_penalty,
                response_format=response_format,
                seed=seed,
                service_tier=service_tier,
                stop=stop,
                store=store,
                stream=True,
                stream_options={"include_usage": True},
                temperature=temperature,
                tool_choice=tool_choice,
                tools=tools,
                top_logprobs=top_logprobs,
                top_p=top_p,
                user=user,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            )
        ):
            if not first_chunk:
                first_chunk = chunk
                last_chunk = chunk
                continue
            yield adapt_completion_chunk(
                chunk=last_chunk,
                pricing=self.pricing,
                created=created,
                usage=chunk.usage,
                return_original=return_original_response,
            )
            last_chunk = chunk
        if first_chunk == last_chunk:
            yield adapt_completion_chunk(
                chunk=last_chunk,
                pricing=self.pricing,
                created=created,
                usage=last_chunk.usage,
                return_original=return_original_response,
            )

    async def embedding(
        self,
        content: Union[str, List[str], Iterable[int], Iterable[Iterable[int]]],
        *,
        return_spase_embedding: bool | NotGiven = NOT_GIVEN,
        return_original_response: bool | NotGiven = NOT_GIVEN,
        dimensions: int | NotGiven = NOT_GIVEN,
        encoding_format: Literal["float", "base64"] | NotGiven = NOT_GIVEN,
        user: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
        **kwargs,
    ) -> EmbeddingResponse:
        if kwargs:
            logger.warning(f"{self.model_id} Unused arguments: {kwargs}")
        assert not return_spase_embedding, "Sparse embeddings are not supported"
        created = time.time()
        embedding = await self.client.embeddings.create(
            input=content,
            **filter_notgiven(
                model=self.model_id,
                dimensions=dimensions,
                encoding_format=encoding_format,
                user=user,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
        )
        return adapt_embedding(
            embedding,
            pricing=self.pricing,
            created=created,
            return_original=return_original_response,
        )

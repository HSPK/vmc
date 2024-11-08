from abc import ABC
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

from vmc.callback import callback
from vmc.models.utils import filter_notgiven
from vmc.types import NOT_GIVEN, NotGiven
from vmc.types.generation.generation import Generation
from vmc.types.generation.generation_chunk import GenerationChunk
from vmc.types.generation.generation_params import ResponseFormat
from vmc.types.generation.message_params import GenerationMessageParam
from vmc.types.generation.tokenize import TokenizeOutput
from vmc.types.generation.tool_choice_option_param import ChatCompletionToolChoiceOptionParam
from vmc.types.generation.tool_param import ChatCompletionToolParam

from ._base import BaseModel


class BaseGenerationModel(BaseModel, ABC):
    """
    BaseChatModel: Base class for chat/completion models
    """

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
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
        return_original_response: bool | NotGiven = NOT_GIVEN,
        **kwargs,
    ) -> Generation:
        raise NotImplementedError(f"Chat method not implemented for {self.__class__.__name__}")

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
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
        return_original_response: bool | NotGiven = NOT_GIVEN,
        stream: bool = False,
        **kwargs,
    ) -> AsyncGenerator[GenerationChunk, None]:
        raise NotImplementedError(f"Chat method not implemented for {self.__class__.__name__}")

    async def _generate(
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
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
        return_original_response: bool | NotGiven = NOT_GIVEN,
        stream: bool = False,
        **kwargs,
    ) -> Union[Generation, AsyncGenerator[Generation, None]]:
        """chat api needs to be implemented by the model"""
        params = filter_notgiven(
            content=content,
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
            return_original_response=return_original_response,
            timeout=timeout,
            **kwargs,
        )
        if stream:

            async def streaming(*args, **kwargs) -> AsyncGenerator[GenerationChunk, None]:
                await callback.on_generation_start(model=self, **params)
                tokens = []
                async for t in self.stream(*args, **kwargs):
                    yield t
                    tokens.append(t)
                await callback.on_generation_end(
                    model=self, content=content, generation_kwargs=params, output=tokens
                )

            return streaming(**params)
        await callback.on_generation_start(model=self, **params)
        res = await self.generate(**params)
        await callback.on_generation_end(
            model=self, content=content, generation_kwargs=params, output=res
        )
        return res

    async def tokenize(
        self,
        content: Union[str, Iterable[str], Iterable[GenerationMessageParam]],
        *,
        allowed_special: Union[Literal["all"], AbstractSet[str]] | NotGiven = NOT_GIVEN,
        disallowed_special: Union[Literal["all"], Collection[str]] | NotGiven = NOT_GIVEN,
        **kwargs,
    ) -> TokenizeOutput:
        """chat api needs to be implemented by the model"""
        pass

    async def _tokenize(
        self,
        content: Union[str, Iterable[str], Iterable[GenerationMessageParam]],
        *,
        allowed_special: Union[Literal["all"], AbstractSet[str]] | NotGiven = NOT_GIVEN,
        disallowed_special: Union[Literal["all"], Collection[str]] | NotGiven = NOT_GIVEN,
        **kwargs,
    ) -> TokenizeOutput:
        """chat api needs to be implemented by the model"""
        res = await self.tokenize(
            content,
            **filter_notgiven(
                allowed_special=allowed_special,
                disallowed_special=disallowed_special,
            ),
            **kwargs,
        )
        return res

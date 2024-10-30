import time
import uuid

from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk, CompletionUsage
from openai.types.create_embedding_response import CreateEmbeddingResponse

from vmc.types.embedding import EmbeddingResponse
from vmc.types.embedding.embedding import Cost
from vmc.types.generation.generation import Generation, GenerationCost
from vmc.types.generation.generation_chunk import GenerationChunk
from vmc.types.pricing import Pricing


def compute_cost(pricing: Pricing, input_tokens: int, output_tokens: int) -> GenerationCost:
    prompt_cost = pricing.input * input_tokens
    generated_cost = pricing.output * output_tokens
    total_cost = prompt_cost + generated_cost
    return GenerationCost(
        currency=pricing.currency,
        multiplier=pricing.multiplier,
        prompt_tokens=input_tokens,
        prompt_cost=prompt_cost,
        generated_tokens=output_tokens,
        generated_cost=generated_cost,
        total_cost=total_cost,
        total_tokens=input_tokens + output_tokens,
    )


def compute_embedding_cost(pricing: Pricing, input_tokens: int) -> Cost:
    prompt_cost = pricing.input * input_tokens
    return Cost(
        currency=pricing.currency,
        multiplier=pricing.multiplier,
        prompt_tokens=input_tokens,
        prompt_cost=prompt_cost,
        total_cost=prompt_cost,
        total_tokens=input_tokens,
    )


def adapt_completion(
    completion: ChatCompletion,
    pricing: Pricing,
    created: float,
    end_time: float | None = None,
    return_original: bool = False,
):
    assert completion.choices, "No choices in completion"
    completion_dict = completion.model_dump()
    end_time = time.time() if end_time is None else end_time
    usage = completion.usage

    return Generation(
        id=completion.id or str(uuid.uuid4()),
        choices=completion_dict["choices"],
        created=created,
        generation_time=end_time - created,
        model=completion_dict["model"],
        cost=compute_cost(pricing, usage.prompt_tokens, usage.completion_tokens),
        system_fingerprint=completion_dict.get("system_fingerprint"),
        original_response=completion_dict if return_original else None,
    )


def restore_completion(generation: Generation):
    gen_dict = generation.model_dump()
    if generation.original_response:
        return ChatCompletionChunk.model_validate(generation.original_response)
    return ChatCompletion(
        id=generation.id,
        choices=gen_dict["choices"],
        created=int(generation.created),
        model=generation.model,
        object="chat.completion",
        system_fingerprint=generation.system_fingerprint,
        usage=CompletionUsage(
            prompt_tokens=generation.cost.prompt_tokens,
            completion_tokens=generation.cost.generated_tokens,
            total_tokens=generation.cost.total_tokens,
        ),
    )


def adapt_completion_chunk(
    chunk: ChatCompletionChunk,
    pricing: Pricing,
    created: float,
    end_time: float | None = None,
    usage: CompletionUsage | None = None,
    return_original: bool = False,
):
    assert chunk.choices or usage, "No choices or usage in completion chunk"
    chunk_dict = chunk.model_dump()
    end_time = time.time() if end_time is None else end_time
    cost = compute_cost(pricing, usage.prompt_tokens, usage.completion_tokens) if usage else None
    return GenerationChunk(
        id=chunk.id,
        choices=chunk_dict["choices"],
        created=created,
        generation_time=end_time - created,
        model=chunk_dict["model"],
        cost=cost,
        system_fingerprint=chunk_dict.get("system_fingerprint"),
        original_response=chunk_dict if return_original else None,
    )


def restore_completion_chunk(generation_chunk: GenerationChunk):
    gen_dict = generation_chunk.model_dump()
    if generation_chunk.original_response:
        return ChatCompletionChunk.model_validate(generation_chunk.original_response)
    usage = (
        CompletionUsage(
            prompt_tokens=generation_chunk.cost.prompt_tokens,
            completion_tokens=generation_chunk.cost.generated_tokens,
            total_tokens=generation_chunk.cost.total_tokens,
        )
        if generation_chunk.cost
        else None
    )
    return ChatCompletionChunk(
        id=generation_chunk.id,
        choices=gen_dict["choices"],
        created=int(generation_chunk.created),
        model=generation_chunk.model,
        object="chat.completion.chunk",
        system_fingerprint=generation_chunk.system_fingerprint,
        usage=usage,
    )


def decode_openai_embedding_base64(s):
    import base64

    import numpy as np

    return np.frombuffer(base64.b64decode(s), dtype=np.float32).tolist()


def adapt_embedding(
    embedding: CreateEmbeddingResponse,
    pricing: Pricing,
    created: float,
    end_time: float | None = None,
    return_original: bool = False,
):
    end_time = time.time() if end_time is None else end_time
    return EmbeddingResponse(
        created=created,
        embedding=[
            decode_openai_embedding_base64(e.embedding)
            if isinstance(e.embedding, str)
            else e.embedding
            for e in embedding.data
        ],
        embed_time=end_time - created,
        model=embedding.model,
        cost=compute_embedding_cost(pricing, embedding.usage.prompt_tokens),
        original_response=embedding.model_dump() if return_original else None,
    )


def restore_embedding(embedding: EmbeddingResponse):
    if embedding.original_response:
        return CreateEmbeddingResponse.model_validate(embedding.original_response)
    return CreateEmbeddingResponse(
        data=[
            {"embedding": e, "index": i, "object": "embedding"}
            for i, e in enumerate(embedding.embedding)
        ],
        model=embedding.model,
        object="list",
        usage={
            "prompt_tokens": embedding.cost.prompt_tokens,
            "total_tokens": embedding.cost.total_tokens,
        },
    )

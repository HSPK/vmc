import time
import uuid

from google.ai.generativelanguage_v1beta.types.content import Content
from google.ai.generativelanguage_v1beta.types.generative_service import Candidate
from google.generativeai.types.generation_types import GenerateContentResponse

from vmc.models.utils import compute_cost
from vmc.types.generation.generation import ChatCompletionMessage, Choice, Generation
from vmc.types.generation.generation_chunk import Choice as ChunkChoice
from vmc.types.generation.generation_chunk import ChoiceDelta, GenerationChunk
from vmc.types.pricing import Pricing


def gen_generation_id() -> str:
    return "gemini-" + str(uuid.uuid4())


def adapt_finish_reason(finish_reason: Candidate.FinishReason) -> str:
    if finish_reason == Candidate.FinishReason.STOP:
        return "stop"
    elif finish_reason == Candidate.FinishReason.MAX_TOKENS:
        return "length"
    elif finish_reason == Candidate.FinishReason.SAFETY:
        return "content_filter"
    elif finish_reason == Candidate.FinishReason.RECITATION:
        return "content_filter"
    else:
        return "stop"


def adapt_content(content: Content) -> ChatCompletionMessage:
    role = "user" if content.role == "user" else "assistant"
    text = "\n".join([part.text for part in content.parts])
    return ChatCompletionMessage(role=role, content=text)


def adapt_content_chunk(content: Content) -> ChatCompletionMessage:
    role = "user" if content.role == "user" else "assistant"
    text = "\n".join([part.text for part in content.parts])
    return ChoiceDelta(role=role, content=text)


def adapt_generation(
    res: GenerateContentResponse,
    model: str,
    pricing: Pricing,
    created: float,
    end_time: float | None = None,
    return_raw_response: bool = False,
) -> Generation:
    res.text
    res.candidates[0].content.parts[0].text
    choices = []
    for i, candidate in enumerate(res.candidates):
        choices.append(
            Choice(
                index=i,
                finish_reason=adapt_finish_reason(candidate.finish_reason),
                message=adapt_content(candidate.content),
            )
        )
    end_time = end_time or time.time()
    return Generation(
        id="gemini-" + str(uuid.uuid4()),
        choices=choices,
        created=created,
        generation_time=end_time - created,
        model=model,
        cost=compute_cost(
            pricing,
            res.usage_metadata.prompt_token_count,
            output_tokens=res.usage_metadata.candidates_token_count,
        ),
        original_response=res.to_dict() if return_raw_response else None,
    )


def adapt_generation_chunk(
    res: GenerateContentResponse,
    id: str,
    model: str,
    pricing: Pricing,
    created: float,
    end_time: float | None = None,
    return_raw_response: bool = False,
) -> GenerationChunk:
    res.text
    res.candidates[0].content.parts[0].text
    choices = []
    for i, candidate in enumerate(res.candidates):
        choices.append(
            ChunkChoice(
                index=i,
                finish_reason=adapt_finish_reason(candidate.finish_reason),
                delta=adapt_content_chunk(candidate.content),
            )
        )
    end_time = end_time or time.time()
    return GenerationChunk(
        id=id,
        choices=choices,
        created=created,
        generation_time=end_time - created,
        model=model,
        cost=compute_cost(
            pricing,
            res.usage_metadata.prompt_token_count,
            output_tokens=res.usage_metadata.candidates_token_count,
        )
        if res.usage_metadata
        else None,
        original_response=res.to_dict() if return_raw_response else None,
    )

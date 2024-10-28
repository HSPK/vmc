from typing import Annotated, Optional

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from loguru import logger
from openai.types.audio import TranscriptionCreateParams
from openai.types.chat.completion_create_params import CompletionCreateParams
from openai.types.embedding_create_params import EmbeddingCreateParams

from vmc.exception import exception_handler
from vmc.models.local.whisper.whisper import BaseAudioModel
from vmc.models.openai.response_adapter import (
    restore_completion,
    restore_completion_chunk,
    restore_embedding,
)
from vmc.types.embedding import EmbeddingParams as VMCEmbeddingParams
from vmc.types.generation import GenerationParams
from vmc.virtual import vmm

router = APIRouter(prefix="/v1")


def remove_keys(d: dict, keys: set):
    return {k: v for k, v in d.items() if k not in keys}


def adapt_completion_params(params: CompletionCreateParams) -> GenerationParams:
    keys = list(GenerationParams.__annotations__.keys())
    d = {k: v for k, v in params.items() if k in keys}
    return GenerationParams(**d, content=params["messages"])


def adapt_embedding_params(params: EmbeddingCreateParams) -> VMCEmbeddingParams:
    keys = list(VMCEmbeddingParams.__annotations__.keys())
    d = {k: v for k, v in params.items() if k in keys}
    return VMCEmbeddingParams(**d, content=params["input"])


async def _stream_generator(params: GenerationParams):
    try:
        model = await vmm.get(params["model"], type="chat")
        async for token in await model._generate(**remove_keys(params, {"model"})):
            chunk = restore_completion_chunk(token)
            yield f"data: {chunk.model_dump_json()}\n\n"
    except Exception as e:
        msg = await exception_handler(e)
        yield msg.to_event()
        return


@router.post("/chat/completions")
async def chat_completion(req: CompletionCreateParams):
    params = adapt_completion_params(req)
    if params.get("stream", False):
        return StreamingResponse(
            _stream_generator(params),
            media_type="text/event-stream",
            headers={"X-Accel-Buffering": "no"},
        )

    model = await vmm.get(params["model"], type="chat")

    res = await model._generate(**remove_keys(params, {"model"}))
    return restore_completion(res)


@router.post("/audio/transcriptions")
async def transciption(
    file: Annotated[UploadFile, File()],
    model: Annotated[str, Form()],
    language: Annotated[Optional[str], Form()] = None,
    temperature: Annotated[Optional[float], Form()] = None,
):
    req = TranscriptionCreateParams(
        file=await file.read(), model=model, language=language, temperature=temperature
    )
    logger.info(f"transcription request: {req['model']}, {file.filename}")
    model: BaseAudioModel = await vmm.get(model, type="audio")
    return model._transcribe(**req)


@router.post("/embeddings")
async def embeddings(req: EmbeddingCreateParams):
    params = adapt_embedding_params(req)
    model = await vmm.get(params["model"], type="embedding")
    embedding = await model._embedding(**remove_keys(params, {"model"}))
    return restore_embedding(embedding)


@router.get("/models")
async def model():
    return {
        "object": "list",
        "data": [
            {
                "id": model_name,
                "object": "model",
                "created": 1686935002,
                "owned_by": "vmcc",
            }
            for model_name in vmm.models.keys()
        ],
    }

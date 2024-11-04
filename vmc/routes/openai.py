from typing import Annotated, Optional

from fastapi import APIRouter, File, Form, UploadFile
from openai.types.audio import TranscriptionCreateParams
from openai.types.chat.completion_create_params import CompletionCreateParams
from openai.types.embedding_create_params import EmbeddingCreateParams

from vmc.proxy import vmm
from vmc.routes.wrapper import wrap_fastapi
from vmc.types.embedding import EmbeddingParams as VMCEmbeddingParams
from vmc.types.generation import GenerationParams

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


@router.post("/chat/completions")
async def chat_completion(req: CompletionCreateParams):
    params = adapt_completion_params(req)
    model = wrap_fastapi(await vmm.get(params["model"], type="chat"))
    return await model.generate_openai(**remove_keys(params, {"model"}))


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
    audio = wrap_fastapi(await vmm.get(req.model, type="audio"))
    return audio.transcribe(**remove_keys(req, {"model"}))


@router.post("/embeddings")
async def embeddings(req: EmbeddingCreateParams):
    params = adapt_embedding_params(req)
    model = wrap_fastapi(await vmm.get(params["model"], type="embedding"))
    return await model.embedding_openai(**remove_keys(params, {"model"}))


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

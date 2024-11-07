from typing import Annotated, Optional

from fastapi import APIRouter, File, Form, UploadFile
from openai.types.audio.transcription_create_params import TranscriptionCreateParams

from vmc.db import storage
from vmc.proxy import vmm
from vmc.routes.wrapper import wrap_fastapi
from vmc.types._base import BaseOutput
from vmc.types.embedding import EmbeddingParams
from vmc.types.generation import GenerationParams
from vmc.types.generation.tokenize_params import TokenizeParams
from vmc.types.image.upload import ImageUploadOutput
from vmc.types.models import ModelInfoOutput
from vmc.types.rerank import RerankParams

router = APIRouter()


def remove_keys(d: dict, keys: set):
    return {k: v for k, v in d.items() if k not in keys}


@router.post("/generate")
async def generate(params: GenerationParams):
    model = wrap_fastapi(await vmm.get(params["model"], "chat"))
    return await model.generate(**remove_keys(params, {"model"}))


@router.post("/embedding")
async def embedding(params: EmbeddingParams):
    model = wrap_fastapi(await vmm.get(params["model"], "embedding"))
    return await model.embedding(**remove_keys(params, {"model"}))


@router.post("/rerank")
async def rerank(params: RerankParams):
    model = wrap_fastapi(await vmm.get(params["model"], "reranker"))
    return await model.rerank(**remove_keys(params, {"model"}))


@router.get("/models")
async def get_models():
    return ModelInfoOutput(models=vmm.models)


@router.post("/tokenize")
async def tokenize(params: TokenizeParams):
    model = wrap_fastapi(await vmm.get(params["model"], "chat"))
    return await model.tokenize(**remove_keys(params, {"model"}))


@router.post("/audio/transcriptions")
async def transciption(
    file: Annotated[UploadFile, File()],
    model: Annotated[str, Form()],
    language: Annotated[Optional[str], Form()] = None,
    temperature: Annotated[Optional[float], Form()] = None,
):
    metadata = await storage.store(file)

    req = TranscriptionCreateParams(
        file=metadata["filepath"],
        model=model,
        language=language,
        temperature=temperature,
    )
    audio = wrap_fastapi(await vmm.get(req.model, "audio"))
    return await audio.transcribe(**remove_keys(req, {"model"}))


@router.post("/image/upload")
async def image_upload(file: UploadFile = File(...)):
    metadata = await storage.store(file)
    return ImageUploadOutput(id=metadata["id"])


@router.get("/health")
async def health():
    return BaseOutput(msg="ok")

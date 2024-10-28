from typing import Annotated, Optional

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from loguru import logger
from openai.types.audio.transcription_create_params import TranscriptionCreateParams

from vmc.db.storage import store_file
from vmc.exception import exception_handler
from vmc.models.local.whisper.whisper import BaseAudioModel
from vmc.models.rerank import BaseRerankModel
from vmc.types._base import BaseOutput
from vmc.types.embedding import EmbeddingParams
from vmc.types.generation import GenerationParams
from vmc.types.generation.tokenize_params import TokenizeParams
from vmc.types.image.upload import ImageUploadOutput
from vmc.types.models import ModelInfoOutput
from vmc.types.rerank import RerankParams
from vmc.virtual import vmm

router = APIRouter()


def remove_keys(d: dict, keys: set):
    return {k: v for k, v in d.items() if k not in keys}


async def _streaming(params: GenerationParams):
    try:
        model = await vmm.get(params["model"], "chat")

        tokens = []
        async for token in await model._generate(**remove_keys(params, {"model"})):
            yield token.to_event()
            tokens.append(token.dict())
    except Exception as e:
        msg = await exception_handler(e)
        yield msg.to_event()
        return


@router.post("/generate")
async def generate(params: GenerationParams):
    if params.get("stream", False):
        return StreamingResponse(
            _streaming(params),
            media_type="text/event-stream",
            headers={"X-Accel-Buffering": "no"},
        )

    model = await vmm.get(params["model"], "chat")
    return await model._generate(**remove_keys(params, {"model"}))


@router.post("/embedding")
async def embedding(params: EmbeddingParams):
    model = await vmm.get(params["model"], "embedding")
    return await model._embedding(**remove_keys(params, {"model"}))


@router.post("/rerank")
async def rerank(params: RerankParams):
    model: BaseRerankModel = await vmm.get(params["model"], "reranker")
    return await model._rerank(**remove_keys(params, {"model"}))


@router.get("/models")
async def get_models():
    return ModelInfoOutput(models=vmm.models)


@router.post("/tokenize")
async def tokenize(params: TokenizeParams):
    model = await vmm.get(params["model"], "chat")

    return await model._tokenize(**remove_keys(params, {"model"}))


@router.post("/audio/transcriptions")
async def transciption(
    file: Annotated[UploadFile, File()],
    model: Annotated[str, Form()],
    language: Annotated[Optional[str], Form()] = None,
    temperature: Annotated[Optional[float], Form()] = None,
):
    req = TranscriptionCreateParams(
        file=await store_file(file, return_path=True),
        model=model,
        language=language,
        temperature=temperature,
    )
    logger.info(f"[Transcription] {req['model']}, {file.filename}")
    model: BaseAudioModel = await vmm.get(req["model"], "audio")
    return model._transcribe(req)


@router.post("/image/upload")
async def image_upload(file: UploadFile = File(...)):
    return ImageUploadOutput(id=await store_file(file))


@router.get("/alive")
async def ping():
    return BaseOutput(msg="vmc is alive")

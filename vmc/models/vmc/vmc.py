from typing import Any, AsyncGenerator, Dict, List, Union

import requests
from openai.types.audio.transcription_create_params import TranscriptionCreateParams
from vmcc import VMC

from vmc.models.audio import BaseAudioModel
from vmc.models.embedding import BaseEmbeddingModel
from vmc.models.generation import BaseGenerationModel
from vmc.models.rerank import BaseRerankModel
from vmc.types.audio import Transcription
from vmc.types.embedding import EmbeddingResponse
from vmc.types.generation import ContentType, Generation, GenerationChunk
from vmc.types.rerank import RerankOutput


class VMCModel(BaseGenerationModel, BaseAudioModel, BaseRerankModel, BaseEmbeddingModel):
    host: str = "http://127.0.0.1"
    model_id: str

    client: Any = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = VMC(host=self.host, user_name="", user_password="")

    def alive(self) -> bool:
        try:
            res = requests.get(f"{self.host}/ping")
        except Exception:
            return False
        return res.status_code == 200

    async def _achat(self, prompt: Union[str, List[ContentType]], parameters) -> Generation:
        return await self.client.achat(
            prompt,
            self.model_id,
            parameters.pop("history", []),
            parameters.pop("return_type", "text"),
            parameters.pop("schema", None),
            parameters,
        )

    async def _astream(
        self,
        prompt: Union[str, List[ContentType]],
        parameters,
    ) -> AsyncGenerator[GenerationChunk, None]:
        self._pop_custom_parameters(parameters)
        async for chunk in self.client.astream_chat(
            prompt,
            self.model_id,
            parameters.pop("history", []),
            parameters,
        ):
            yield chunk

    async def _aget_embeddings(
        self, prompt: str | List[str], parameters: Dict[str, Any]
    ) -> EmbeddingResponse:
        return await self.client.aget_embeddings(prompt, self.model_id, parameters)

    async def _atranscribe(self, req: TranscriptionCreateParams) -> Transcription:
        return await self.client.atranscribe(
            req["file"], req["model"], req["language"], req["temperature"]
        )

    async def _apredict(
        self, sentences: List[List[str]], parameters: Dict[str, Any]
    ) -> RerankOutput:
        return await self.client.across_embedding(sentences, self.model_id, parameters)

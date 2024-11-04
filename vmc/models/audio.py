from vmc.callback import callback
from vmc.types.audio import Transcription

from ._base import BaseModel


class BaseAudioModel(BaseModel):
    async def transcribe(self, file: str, **kwargs) -> Transcription:
        raise NotImplementedError("transcribe is not implemented")

    async def _transcribe(self, file: str, **kwargs) -> Transcription:
        await callback.on_transcribe_start(model=self, file=file, **kwargs)
        res = await self.transcribe(file, **kwargs)
        await callback.on_transcribe_end(model=self, output=res)
        return res

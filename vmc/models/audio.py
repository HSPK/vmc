from vmc.types.audio import Transcription

from ._base import BaseModel


class BaseAudioModel(BaseModel):
    async def transcribe(self, file: str, **kwargs) -> Transcription:
        raise NotImplementedError("transcribe is not implemented")

    async def _transcribe(self, file: str, **kwargs) -> Transcription:
        await self.callback.on_transcribe_start(file, kwargs)
        res = await self.transcribe(file, **kwargs)
        await self.callback.on_transcribe_end(res)
        return res

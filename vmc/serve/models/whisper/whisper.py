import torch
from openai.types.audio.transcription_create_params import TranscriptionCreateParams
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor

from vmc.models.audio import BaseAudioModel
from vmc.types.audio import Transcription


class Whisper(BaseAudioModel):
    model_id: str
    pipeline: object = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        from transformers import pipeline

        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            self.model_id, torch_dtype=torch.float16, trust_remote_code=True
        ).cuda()
        processer = AutoProcessor.from_pretrained(self.model_id, trust_remote_code=True)
        self.pipeline = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processer.tokenizer,
            feature_extractor=processer.feature_extractor,
            max_new_tokens=512,
            chunk_length_s=30,
            batch_size=16,
            return_timestamps=True,
            torch_dtype=torch.float16,
        )

    def transcribe(self, req: TranscriptionCreateParams) -> Transcription:
        return Transcription(text=self.pipeline(req["file"])["text"])

import time
import uuid
from threading import Thread
from typing import (
    AsyncGenerator,
    Iterable,
    Optional,
    Union,
)

import torch
from loguru import logger
from transformers import (
    AutoModel,
    AutoModelForCausalLM,
    AutoTokenizer,
    PreTrainedModel,
    TextIteratorStreamer,
)
from typing_extensions import Literal

from vmc.models.generation import BaseGenerationModel
from vmc.models.utils import filter_notgiven
from vmc.types import NOT_GIVEN, NotGiven
from vmc.types.generation.generation import (
    ChatCompletionMessage,
    Choice,
    Generation,
    GenerationCost,
)
from vmc.types.generation.generation_chunk import Choice as ChunkChoice
from vmc.types.generation.generation_chunk import ChoiceDelta, GenerationChunk
from vmc.types.generation.message_params import GenerationMessageParam
from vmc.types.generation.tokenize import TokenizeOutput
from vmc.types.pricing import Currency


class TransformerGeneration(BaseGenerationModel):
    def __init__(
        self,
        model_class: Literal["AutoModel", "AutoModelForCausalLM"] = "AutoModelForCausalLM",
        torch_dtype: Literal["float16", "float32", "float64", "bfloat16"] = "bfloat16",
        max_length: Optional[int] = None,
        device_map: Optional[bool] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")
        torch_dtype = {
            "float16": torch.float16,
            "float32": torch.float32,
            "float64": torch.float64,
            "bfloat16": torch.bfloat16,
        }[torch_dtype]
        model_kwargs = {"trust_remote_code": True, "torch_dtype": torch_dtype}
        if device_map is not None:
            model_kwargs["device_map"] = device_map
        if model_class == "AutoModel":
            self.model: PreTrainedModel = AutoModel.from_pretrained(self.model_id, **model_kwargs)
        else:
            self.model: PreTrainedModel = AutoModelForCausalLM.from_pretrained(
                self.model_id, **model_kwargs
            )
        if device_map is None:
            self.model.to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, trust_remote_code=True)
        self.max_length = max_length

    def prepare_input(self, content: Union[str, Iterable[GenerationMessageParam]]):
        if isinstance(content, str):
            content = [{"role": "user", "content": content}]
        input_dict = self.tokenizer.apply_chat_template(
            conversation=content,
            return_tensors="pt",
            add_generation_prompt=True,
            max_length=self.max_length,
            return_dict=True,
        )
        return input_dict

    async def generate(
        self,
        content: Union[str, Iterable[GenerationMessageParam]],
        frequency_penalty: Optional[float] | NotGiven = NOT_GIVEN,
        max_tokens: Optional[int] | NotGiven = NOT_GIVEN,
        temperature: Optional[float] | NotGiven = NOT_GIVEN,
        top_p: Optional[float] | NotGiven = NOT_GIVEN,
        skip_special_tokens: bool | NotGiven = NOT_GIVEN,
        **kwargs,
    ) -> Generation:
        if kwargs:
            logger.warning(f"{self.model_id} Unused kwargs: {kwargs}")
        created = time.time()
        inputs = self.prepare_input(content)
        input_ids = inputs["input_ids"]
        response_ids = self.model.generate(
            **inputs.to(self.device),
            **filter_notgiven(
                frequency_penalty=frequency_penalty,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            ),
        )
        if skip_special_tokens is NOT_GIVEN:
            skip_special_tokens = True
        response_text = self.tokenizer.decode(
            response_ids[0][len(input_ids[0]) :], skip_special_tokens=skip_special_tokens
        )
        prompt_tokens = input_ids.size(1)
        completion_tokens = response_ids.size(1) - prompt_tokens
        if max_tokens is not NOT_GIVEN and completion_tokens > max_tokens:
            finish_reason = "length"
        else:
            finish_reason = "stop"
        return Generation(
            id=f"{self.config.name}-{str(uuid.uuid4())}",
            choices=[
                Choice(
                    finish_reason=finish_reason,
                    index=0,
                    message=ChatCompletionMessage(role="assistant", content=response_text),
                )
            ],
            created=created,
            generation_time=time.time() - created,
            model=self.model_id,
            cost=GenerationCost(
                currency=Currency.CNY,
                multiplier=0,
                prompt_tokens=prompt_tokens,
                prompt_cost=0,
                generated_tokens=completion_tokens,
                generated_cost=0,
                total_cost=0,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )

    async def stream(
        self,
        content: Union[str, Iterable[GenerationMessageParam]],
        frequency_penalty: Optional[float] | NotGiven = NOT_GIVEN,
        max_tokens: Optional[int] | NotGiven = NOT_GIVEN,
        temperature: Optional[float] | NotGiven = NOT_GIVEN,
        top_p: Optional[float] | NotGiven = NOT_GIVEN,
        stream: bool = True,
        **kwargs,
    ) -> AsyncGenerator[GenerationChunk, None]:
        if kwargs:
            logger.warning(f"{self.model_id} Unused kwargs: {kwargs}")
        created = time.time()
        inputs = self.prepare_input(content)
        streamer = TextIteratorStreamer(
            self.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
        )
        generation_kwargs = {
            **inputs.to(self.device),
            **filter_notgiven(
                frequency_penalty=frequency_penalty,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            ),
            "streamer": streamer,
        }
        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()
        id = f"{self.config.name}-{str(uuid.uuid4())}"

        for new_text in streamer:
            yield GenerationChunk(
                id=id,
                choices=[
                    ChunkChoice(
                        delta=ChoiceDelta(role="assistant", content=new_text),
                        index=0,
                        finish_reason="stop",
                    )
                ],
                created=created,
                generation_time=time.time() - created,
                model=self.model_id,
            )
        yield GenerationChunk(
            id=id,
            choices=[
                ChunkChoice(
                    delta=ChoiceDelta(role="assistant", content=""),
                    index=0,
                    finish_reason="stop",
                )
            ],
            created=created,
            generation_time=time.time() - created,
            model=self.model_id,
            cost=GenerationCost(
                currency=Currency.CNY,
                multiplier=0,
                prompt_tokens=inputs["input_ids"].size(1),
                prompt_cost=0,
                generated_tokens=0,
                generated_cost=0,
                total_cost=0,
                total_tokens=0,
            ),
        )

    async def tokenize(
        self, content: Union[str, Iterable[str], Iterable[GenerationMessageParam]], **kwargs
    ) -> TokenizeOutput:
        if kwargs:
            logger.warning(f"{self.model_id} Unused kwargs: {kwargs}")
        tokens = self.prepare_input(content)["input_ids"]
        return TokenizeOutput(tokens=tokens, length=[len(tok) for tok in tokens])

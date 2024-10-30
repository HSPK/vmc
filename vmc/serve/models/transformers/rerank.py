import torch
from sentence_transformers import CrossEncoder

from vmc.models.rerank import BaseRerankModel
from vmc.models.utils import filter_notgiven
from vmc.types._types import NOT_GIVEN, NotGiven
from vmc.types.rerank import RerankOutput
from vmc.utils.gpu import torch_gc


class TransformerReranker(BaseRerankModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")
        self.model = CrossEncoder(self.model_id, device=self.device)

    async def rerank(
        self,
        content: list[list[str]],
        *,
        batch_size: int | NotGiven = NOT_GIVEN,
        apply_softmax: bool | NotGiven = NOT_GIVEN,
        **kwargs,
    ):
        scores = self.model.predict(
            content, **filter_notgiven(batch_size=batch_size, apply_softmax=apply_softmax)
        ).tolist()
        torch_gc()
        return RerankOutput(scores=scores)

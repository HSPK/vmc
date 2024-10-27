from typing import List

from .._base import BaseOutput


class RerankOutput(BaseOutput):
    scores: List[float]

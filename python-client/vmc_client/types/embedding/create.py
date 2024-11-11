from typing import List, Union

from typing_extensions import Literal, Required, TypedDict


class EmbeddingParams(TypedDict, total=False):
    content: Required[Union[str, List[str], List[int], List[List[int]]]]
    model: Required[str]
    return_spase_embedding: bool
    return_original_response: bool
    dimensions: int
    encoding_format: Literal["float", "base64"]
    user: str
    task_type: str
    title: str
    batch_size: int
    normalize_embeddings: bool

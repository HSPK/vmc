from typing import List, Union

from typing_extensions import Literal, Required, TypedDict


class EmbeddingParams(TypedDict, total=False):
    content: Required[Union[str, List[str]]]
    model: Required[str]
    encoding_format: Literal["float", "base64"]
    user: str
    dimensions: int
    return_sparse: bool

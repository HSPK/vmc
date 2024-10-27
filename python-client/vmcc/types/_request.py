from typing import Dict, Iterable, Union

import httpx
from typing_extensions import Literal, TypedDict

from ._base import BaseModel


class RequestOptions(TypedDict):
    headers: Dict
    timeout: httpx.Timeout
    params: Dict
    max_retries: int
    no_auth: bool
    raw_response: bool
    files: Dict
    data: Dict
    content: Union[bytes, str, Iterable[bytes], Iterable[str]]
    stream_prefix: str


class FinalRequestOptions(BaseModel):
    method: Literal["get", "post", "put", "delete", "patch"]
    url: str
    headers: Dict = {}
    params: Dict = {}
    max_retries: Union[int, None] = None
    timeout: Union[httpx.Timeout, None] = None
    json_data: Union[Dict, None] = None
    files: Union[Dict, None] = None
    data: Union[Dict, None] = None
    content: Union[bytes, str, Iterable[bytes], Iterable[str], None] = None
    no_auth: bool = False
    raw_response: bool = False
    stream: bool = False
    stream_prefix: str = "data:"

    def get_max_retries(self, max_retries: int) -> int:
        return self.max_retries if self.max_retries is not None else max_retries

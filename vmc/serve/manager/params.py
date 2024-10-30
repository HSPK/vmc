import pydantic
from fastapi.responses import JSONResponse
from typing_extensions import Literal, Required, TypedDict


class ServeParams(TypedDict, total=False):
    name: Required[str]
    """custom name for the model"""

    port: Required[int]
    host: str
    model_id: str
    method: Literal["config", "tf", "vllm", "ollama"]
    type: Literal["chat", "embedding", "audio", "reranker"]
    init_args: dict
    api_key: str
    backend: Literal["torch", "onnx", "openvino"]
    device_map_auto: bool
    gpu_limit: int


class StopParams(TypedDict):
    name: Required[str]


class StatusCode:
    SUCCESS = 0
    SERVE_ERROR = 1
    STOP_ERROR = 2
    LIST_ERROR = 3


class BaseResponse(pydantic.BaseModel):
    code: int = 0
    msg: str = "success"
    model_config = pydantic.ConfigDict(extra="allow", protected_namespaces=())

    def to_response(self):
        return JSONResponse(
            content=self.model_dump(),
            status_code=200 if self.code == StatusCode.SUCCESS else 500,
        )


class ServeResponse(BaseResponse):
    model_id: str
    serve_port: int

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

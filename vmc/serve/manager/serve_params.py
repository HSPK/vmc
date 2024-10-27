import pydantic
from typing_extensions import Literal, Required, TypedDict


class ServeParams(TypedDict, total=False):
    name: Required[str]
    """custom name for the model"""
    model_id: str
    """model id, e.g. 'facebook/dpr-question_encoder-single-nq-base', use `name` if empty"""
    serve_method: Literal["transformers", "ollama", "vllm"]
    serve_host: str
    vllm_cmd_args: list[str]
    ollama_cmd_args: list[str]


class BaseResponse(pydantic.BaseModel):
    code: int = 0
    msg: str = "success"
    model_config = pydantic.ConfigDict(extra="allow", protected_namespaces=())


class ServeResponse(BaseResponse):
    model_id: str
    serve_port: int

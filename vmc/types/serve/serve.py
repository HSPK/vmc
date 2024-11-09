from .._base import BaseModel, BaseOutput


class ServeResponse(BaseOutput):
    port: int
    pid: int


class ListServerInfo(BaseModel):
    params: dict
    pid: int


class ListServerResponse(BaseOutput):
    servers: dict[str, ListServerInfo]

import pydantic
from fastapi.responses import JSONResponse
from typing_extensions import ClassVar


class BaseModel(pydantic.BaseModel):
    model_config: ClassVar[pydantic.ConfigDict] = pydantic.ConfigDict(
        extra="allow",
        use_enum_values=True,
        protected_namespaces=(),
        arbitrary_types_allowed=True,
    )

    def to_event(self, prefix: str = "data: ", sep: str = "\n\n") -> str:
        return f"{prefix}{self.model_dump_json()}{sep}"


class BaseOutput(BaseModel):
    status_code: int = 200
    code: int = 0
    msg: str = "success"

    def to_response(self) -> JSONResponse:
        return JSONResponse(
            self.model_dump(exclude=["status_code"]),
            status_code=self.status_code,
        )

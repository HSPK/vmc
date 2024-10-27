import pydantic


class BaseModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
        protected_namespaces=(),
        use_enum_values=True,
    )


class BaseOutput(BaseModel):
    code: int = 200
    msg: str = "success"


class ErrorMessage(BaseOutput):
    code: int = 500
    msg: str = "failed"

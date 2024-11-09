from .._base import BaseOutput


class ErrorMessage(BaseOutput):
    code: int = 500
    msg: str = "failed"

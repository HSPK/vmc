from .._base import BaseOutput


class TokenizeOutput(BaseOutput):
    tokens: list[list[int]] | list[int]
    length: list[int] | int

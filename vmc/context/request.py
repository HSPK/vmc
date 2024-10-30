from contextvars import ContextVar

from fastapi import Request

request: ContextVar[Request] = ContextVar("request", default=None)

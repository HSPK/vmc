from contextvars import ContextVar
from typing import Dict

# The context variable for the current request.
request_params: ContextVar[Dict] = ContextVar("request_params", default={})

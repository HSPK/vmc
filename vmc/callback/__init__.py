from vmc.utils import LazyObjProxy

from .base import VMCCallback, VMCCallbackGroup
from .callbacks import LoggingCallback, SaveGenerationToDB
from .lark import LarkNotify

callback: VMCCallback = LazyObjProxy(lambda: _get_callback())

_callback = None


def _get_callback():
    if _callback is None:
        raise ValueError("Callback not initialized")
    return _callback


def set_callback(callback: VMCCallbackGroup):
    global _callback
    _callback = callback


__all__ = ["VMCCallback", "VMCCallbackGroup", "LoggingCallback", "SaveGenerationToDB", "LarkNotify"]

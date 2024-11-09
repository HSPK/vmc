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


def init_callback(cb_ids: list[str]):
    callbacks = []
    for cb_id in cb_ids:
        if cb_id == "logging":
            callbacks.append(LoggingCallback())
        elif cb_id == "db_save":
            callbacks.append(SaveGenerationToDB(run_in_background=True))
        elif cb_id == "lark":
            callbacks.append(LarkNotify())
        else:
            raise ValueError(f"Unknown callback: {cb_id}")
    set_callback(VMCCallbackGroup(callbacks))


__all__ = ["VMCCallback", "VMCCallbackGroup", "LoggingCallback", "SaveGenerationToDB", "LarkNotify"]

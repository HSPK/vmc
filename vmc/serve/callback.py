import os

from vmc.callback import (
    LarkNotify,
    LoggingCallback,
    SaveGenerationToDB,
    VMCCallback,
    VMCCallbackGroup,
    set_callback,
)
from vmc.proxy import init_vmm, vmm
from vmc.proxy.manager import VirtualModelManager


class ServeAppLifeSpan(VMCCallback):
    async def on_startup(self, title=None, message=None, **kwargs):
        name = os.getenv("SERVE_NAME")
        model_id = os.getenv("SERVE_MODEL_ID")
        method = os.getenv("SERVE_METHOD", "config")
        type = os.getenv("SERVE_TYPE")
        backend = os.getenv("SERVE_BACKEND", "torch")
        device_map_auto = os.getenv("SERVE_DEVICE_MAP_AUTO", "False")
        device_map_auto = device_map_auto.lower() == "true"
        assert name, "SERVE_NAME is not set"

        if not model_id:
            model_id = name
        init_vmm(
            await VirtualModelManager.from_serve(
                name=name,
                model_id=model_id,
                method=method,
                type=type,
                backend=backend,
                device_map_auto=device_map_auto,
            )
        )

    async def on_shutdown(self, title=None, message=None, **kwargs):
        name = os.getenv("SERVE_NAME")
        type = os.getenv("SERVE_TYPE")
        await vmm.offload(name, type=type)


def init_callback(cb_ids: list[str]):
    callbacks = []
    for cb_id in cb_ids:
        if cb_id == "lifespan":
            callbacks.append(ServeAppLifeSpan())
        elif cb_id == "logging":
            callbacks.append(LoggingCallback())
        elif cb_id == "db_save":
            callbacks.append(SaveGenerationToDB(run_in_background=True))
        elif cb_id == "lark":
            callbacks.append(LarkNotify())
        else:
            raise ValueError(f"Unknown callback: {cb_id}")
    set_callback(VMCCallbackGroup(callbacks))

from vmc.callback import (
    LarkNotify,
    LoggingCallback,
    SaveGenerationToDB,
    VMCCallback,
    VMCCallbackGroup,
    set_callback,
)
from vmc.proxy import init_vmm
from vmc.proxy.manager import VirtualModelManager


class ProxyAppLifeSpan(VMCCallback):
    async def on_startup(self, title=None, message=None, **kwargs):
        print("✅ Setting up models...")
        init_vmm(VirtualModelManager.from_yaml(None))
        print("✅ Initializing Database...")
        print("✅ Done!")


def init_callback(cb_ids: list[str]):
    callbacks = []
    for cb_id in cb_ids:
        if cb_id == "lifespan":
            callbacks.append(ProxyAppLifeSpan())
        elif cb_id == "logging":
            callbacks.append(LoggingCallback())
        elif cb_id == "db_save":
            callbacks.append(SaveGenerationToDB(run_in_background=True))
        elif cb_id == "lark":
            callbacks.append(LarkNotify())
        else:
            raise ValueError(f"Unknown callback: {cb_id}")
    set_callback(VMCCallbackGroup(callbacks))

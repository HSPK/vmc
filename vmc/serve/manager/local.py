from vmc.models import VMC
from vmc.serve.manager.client import MangerClient
from vmc.types.model_config import ModelConfig
from vmc.utils import find_available_port

client = MangerClient()


async def load_local_model(model: ModelConfig):
    assert await client.health(), "Manager is not running"
    port = find_available_port()
    load_method = model.load_method or "tf"
    res = await client.serve(
        name=model.name,
        port=port,
        model_id=model.init_kwargs.get("model_id"),
        method=model.load_method or "tf",
        type=model.type,
        backend=model.backend,
        device_map_auto=model.device_map_auto,
    )
    port = res["port"]
    if load_method == "tf":
        return VMC(port=port)
    else:
        raise NotImplementedError(f"{load_method} is not supported")

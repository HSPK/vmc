from vmc.models import VMC
from vmc.serve.manager.client import ManagerClient
from vmc.types.model_config import ModelConfig
from vmc.utils import find_available_port

_client: ManagerClient = None


async def load_local_model(model: ModelConfig):
    global _client
    if _client is None:
        _client = ManagerClient()
    await _client.health()
    port = find_available_port()
    load_method = model.load_method or "tf"
    res = await _client.serve(
        name=model.name,
        port=port,
        model_id=model.init_kwargs.get("model_id"),
        method=model.load_method or "tf",
        type=model.type,
        backend=model.backend,
        device_map_auto=model.device_map_auto,
        gpu_limit=model.gpu_limit,
    )
    port = res.port
    if load_method == "tf":
        return VMC(port=port)
    else:
        raise NotImplementedError(f"{load_method} is not supported")

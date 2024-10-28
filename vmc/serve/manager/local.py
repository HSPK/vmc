import os

from vmcc import AsyncVMC

from vmc.serve.manager.client import serve_model
from vmc.types.model_config import ModelConfig


async def load_local_model(
    model: ModelConfig, serve_host: str | None = None, serve_port: int | None = None
):
    serve_host = serve_host or os.getenv("VMC_SERVE_HOST")
    serve_port = serve_port or os.getenv("VMC_SERVE_PORT")
    assert serve_host, "serve_host is not provided"
    assert serve_port, "serve_port is not provided"

    port = serve_model(model.name, gpu_limit=model.gpu_limit)
    return AsyncVMC(host=f"http://{serve_host}:{port}", model_id=model.name, config=model)

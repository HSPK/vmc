import os

from typing_extensions import Unpack

from vmc.serve.manager.params import ServeParams
from vmc.types._base import BaseOutput
from vmc.types.serve.serve import ListServerResponse, ServeResponse
from vmc.utils.api_client import DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT, AsyncAPIClient


class ManagerClient:
    def __init__(self, host: str | None = None, port: int | None = None):
        host = host or os.getenv("VMC_MANAGER_HOST")
        port = port or os.getenv("VMC_MANAGER_PORT")
        assert host, "VMC_MANAGER_HOST is not set"
        assert port, "VMC_MANAGER_PORT is not set"
        self.client = AsyncAPIClient(
            base_url=f"http://{host}:{port}",
            max_retries=DEFAULT_MAX_RETRIES,
            timeout=DEFAULT_TIMEOUT,
        )

    async def serve(self, **kwargs: Unpack[ServeParams]):
        return await self.client.post("/serve", body=kwargs, cast_to=ServeResponse)

    async def stop(self, name: str):
        return await self.client.post("/stop", body={"name": name}, cast_to=BaseOutput)

    async def list(self):
        return await self.client.get("/list", cast_to=ListServerResponse)

    async def health(self):
        return await self.client.get("/health", cast_to=BaseOutput)

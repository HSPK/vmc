import os

import httpx
from typing_extensions import Unpack

from vmc.serve.manager.params import ServeParams, StatusCode
from vmc.types.errors.errors import ServeError


class ManagerClient:
    def __init__(self, host: str | None = None, port: int | None = None):
        host = host or os.getenv("VMC_MANAGER_HOST")
        port = port or os.getenv("VMC_MANAGER_PORT")
        assert host, "VMC_MANAGER_HOST is not set"
        assert port, "VMC_MANAGER_PORT is not set"
        self.base_url = f"http://{host}:{port}"
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=300)

    async def serve(self, **kwargs: Unpack[ServeParams]):
        try:
            response = await self.client.post("/serve", json=kwargs)
            response.raise_for_status()
            assert "code" in response.json(), "Invalid response"
            assert response.json()["code"] == StatusCode.SUCCESS, response.json()["msg"]
            return response.json()
        except Exception as e:
            raise ServeError(msg=str(e))

    async def stop(self, name: str):
        try:
            response = await self.client.post("/stop", json={"name": name})
            response.raise_for_status()
            assert "code" in response.json(), "Invalid response"
            assert response.json()["code"] == StatusCode.SUCCESS, response.json()["msg"]
            return response.json()
        except Exception as e:
            raise ServeError(msg=str(e))

    async def list(self):
        try:
            response = await self.client.get("/list")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ServeError(msg=str(e))

    async def health(self):
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ServeError(msg=str(e))

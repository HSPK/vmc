import httpx
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from vmc.context.request import request
from vmc.context.user import current_user
from vmc.types.errors import VMCException


class VMC:
    def __init__(self, port: int, host: str = "localhost"):
        self.host = host
        self.port = port
        self.client = httpx.AsyncClient(base_url=f"http://{self.host}:{self.port}", timeout=60)

    def __getattr__(self, name):
        """Redirects all calls to the VMC server"""
        if name in ["health"]:
            return super().__getattribute__(name)

        async def _(**kwargs):
            req = request.get()
            headers = req.headers.mutablecopy()
            headers["X-VMC-Logging-User"] = current_user.username
            http_req = self.client.build_request(
                req.method,
                url=req.url.path,
                content=req.scope["body"],
                headers=headers,
            )
            try:
                res = await self.client.send(http_req, stream=True)
            except Exception:
                raise VMCException(
                    http_code=500,
                    vmc_code=500,
                    msg="Failed to connect to VMC Serve Server, please reload it.",
                )
            return StreamingResponse(
                content=res.aiter_text(),
                headers=res.headers,
                status_code=res.status_code,
                background=BackgroundTask(res.close),
            )

        return _

    async def health(self):
        try:
            res = await self.client.get("health")
            res.raise_for_status()
            assert "msg" in res.json()
            assert res.json()["msg"] == "ok"
        except Exception:
            return False
        return True

import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from vmc.exception import exception_handler
from vmc.routes import openai, vmc
from vmc.types.errors._base import VMCException
from vmc.types.errors.message import ErrorMessage
from vmc.types.errors.status_code import HTTP_CODE as s
from vmc.types.errors.status_code import VMC_CODE as v


def create_app():
    api_key = os.getenv("SERVE_API_KEY")
    name = os.getenv("SERVE_NAME")
    model_id = os.getenv("SERVE_MODEL_ID")
    method = os.getenv("SERVE_METHOD", "config")
    type = os.getenv("SERVE_TYPE", "chat")
    backend = os.getenv("SERVE_BACKEND", "torch")
    device_map_auto = os.getenv("SERVE_DEVICE_MAP_AUTO", "False")
    device_map_auto = device_map_auto.lower() == "true"

    assert name, "SERVE_NAME is not set"
    if not model_id:
        model_id = name

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        import rich

        from vmc.virtual import set_vmm, vmm
        from vmc.virtual.manager import VirtualModelManager

        rich.print(f"✅ {type}/{name} loading({method})...")
        set_vmm(
            await VirtualModelManager.from_serve(
                name=name,
                model_id=model_id,
                method=method,
                type=type,
                backend=backend,
                device_map_auto=device_map_auto,
            )
        )
        rich.print(f"✅ {type}/{name} loaded({method})...")

        yield
        rich.print(f"❌ {type}/{name} unloading...")
        await vmm.offload(name, type=type)

    app = FastAPI(lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation exceptions"""
        return ErrorMessage(
            status_code=s.BAD_REQUEST,
            code=v.BAD_PARAMS,
            msg=json.dumps(jsonable_encoder(exc.errors())),
        ).to_response()

    @app.exception_handler(VMCException)
    async def handle_vmc_exception(request: Request, exc: VMCException):
        msg = await exception_handler(exc)
        return msg.to_response()

    @app.exception_handler(Exception)
    async def handle_exception(request: Request, exc: Exception):
        msg = await exception_handler(exc)
        return msg.to_response()

    @app.middleware("http")
    async def validate_token(request: Request, call_next):
        if not api_key:
            return await call_next(request)
        if request.headers.get("Authorization").replace("Bearer ", "") != api_key:
            return ErrorMessage(
                status_code=s.UNAUTHORIZED, code=v.UNAUTHORIZED, msg="Unauthorized"
            ).to_response()
        return await call_next(request)

    app.include_router(openai.router)
    app.include_router(vmc.router)

    return app

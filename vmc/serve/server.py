import json
import os
from contextlib import asynccontextmanager

import rich
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from vmc.callback import callback, init_callback
from vmc.context.user import set_user
from vmc.db import init_db, init_storage
from vmc.db.schema import User
from vmc.exception import exception_handler
from vmc.proxy import vmm
from vmc.routes import openai, vmc
from vmc.serve import SERVER_STARTED_MSG
from vmc.serve.vmm import init_serve_vmm
from vmc.types.errors._base import VMCException
from vmc.types.errors.message import ErrorMessage
from vmc.types.errors.status_code import HTTP_CODE as s
from vmc.types.errors.status_code import VMC_CODE as v
from vmc.utils import get_version

API_KEY = os.getenv("SERVE_API_KEY")


async def app_startup():
    await init_serve_vmm()
    init_storage()
    init_db()


async def app_shutdown():
    name = os.getenv("SERVE_NAME")
    type = os.getenv("SERVE_TYPE")
    await vmm.offload(name, type=type)


async def on_startup():
    callbacks = os.getenv("VMC_SERVE_CALLBACKS")
    if not callbacks:
        callbacks = os.getenv("VMC_CALLBACKS")
    callbacks = callbacks.split(",")
    init_callback(callbacks)
    serve_model_name = os.getenv("SERVE_NAME")
    await app_startup()
    await callback.on_startup(
        title=f"VMC Serve({get_version()}) For {serve_model_name} Started",
        message="For more information, please visit xxx",
    )
    rich.print(SERVER_STARTED_MSG)


async def on_shutdown():
    await app_shutdown()
    serve_model_name = os.getenv("SERVE_NAME")
    await callback.on_shutdown(
        title=f"VMC Serve({get_version()}) For {serve_model_name} Stopped",
        message="Stopped",
        gather_background=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    await on_startup()
    yield
    await on_shutdown()


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
    if API_KEY and request.headers.get("Authorization").replace("Bearer ", "") != API_KEY:
        return ErrorMessage(
            status_code=s.UNAUTHORIZED, code=v.UNAUTHORIZED, msg="Unauthorized"
        ).to_response()
    logging_username = request.headers.get(
        "X-VMC-Logging-User", os.getenv("VMC_SERVE_DEFAULT_USER", "vmc")
    )
    set_user(User(id=logging_username, username=logging_username, password="vmc", role="user"))
    return await call_next(request)


app.include_router(openai.router)
app.include_router(vmc.router)

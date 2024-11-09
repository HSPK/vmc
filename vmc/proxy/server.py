import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from openai._exceptions import OpenAIError
from zhipuai import ZhipuAIError

from vmc.callback import callback, init_callback
from vmc.context.request import request as request_context
from vmc.context.user import set_user
from vmc.db import db, init_db, init_storage
from vmc.exception import exception_handler
from vmc.proxy import init_vmm
from vmc.proxy.manager import VirtualModelManager
from vmc.routes import openai, vmc
from vmc.types.errors._base import VMCException
from vmc.types.errors.message import ErrorMessage
from vmc.types.errors.status_code import HTTP_CODE as s
from vmc.types.errors.status_code import VMC_CODE as v
from vmc.utils import get_version


async def app_startup():
    print("✅ Setting up models...")
    init_vmm(VirtualModelManager.from_yaml(None))
    print("✅ Initializing Database...")
    init_db()
    init_storage()
    print("✅ Setting up callbacks...")
    callbacks = os.getenv("VMC_PROXY_CALLBACKS")
    if not callbacks:
        callbacks = os.getenv("VMC_CALLBACKS")
    callbacks = callbacks.split(",")
    init_callback(callbacks)
    await callback.on_startup(
        title=f"VMC Proxy v{get_version()} Started",
        message="For more information, please visit xxx",
    )
    await db.add_user("admin", "admin", "admin")
    print("✅ Done!")


async def app_shutdown():
    await callback.on_shutdown(
        title=f"VMC Proxy v{get_version()} Stopped", message="Stopped", gather_background=True
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    await app_startup()
    yield
    await app_shutdown()


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
        status_code=s.BAD_REQUEST, code=v.BAD_PARAMS, msg=json.dumps(jsonable_encoder(exc.errors()))
    ).to_response()


@app.exception_handler(Exception)
async def handle_exception(request: Request, exc: Exception):
    msg = await exception_handler(exc)
    return msg.to_response()


IGNORE_PATHS = ["/docs", "/openapi.json"]


async def check_user(auth: str | None):
    if not auth:
        return None
    user = await db.get_user_by_token(auth)
    if not user:
        return None
    set_user(user)
    return user


@app.middleware("http")
async def validate_token(request: Request, call_next):
    request.scope["body"] = await request.body()
    request_context.set(request)
    if request.url.path in IGNORE_PATHS:
        return await call_next(request)
    if await check_user(request.headers.get("Authorization")):
        return await call_next(request)
    return ErrorMessage(
        status_code=s.UNAUTHORIZED, code=v.UNAUTHORIZED, msg="Unauthorized"
    ).to_response()


async def default_exception_handler(request: Request, exc: Exception):
    msg = await exception_handler(exc)
    return msg.to_response()


app.add_exception_handler(VMCException, default_exception_handler)
app.add_exception_handler(OpenAIError, default_exception_handler)
app.add_exception_handler(ZhipuAIError, default_exception_handler)

app.include_router(openai.router)
app.include_router(vmc.router)

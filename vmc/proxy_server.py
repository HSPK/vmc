import json

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

app = FastAPI()
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
    return await call_next(request)


app.include_router(openai.router)
app.include_router(vmc.router)

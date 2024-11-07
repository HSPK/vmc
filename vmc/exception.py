import traceback

import openai
import zhipuai
from loguru import logger

from vmc.callback import callback
from vmc.types import errors as err
from vmc.types.errors import ErrorMessage
from vmc.types.errors.status_code import HTTP_CODE as s
from vmc.types.errors.status_code import VMC_CODE as v

__exception_map = {
    openai.APITimeoutError: (s.API_TIMEOUT, v.API_TIMEOUT),
    openai.APIConnectionError: (s.API_CONNECTION_ERROR, v.API_CONNECTION_ERROR),
    openai.BadRequestError: (s.BAD_PARAMS, v.BAD_PARAMS),
    openai.AuthenticationError: (s.UNAUTHORIZED, v.UNAUTHORIZED),
    zhipuai.APIAuthenticationError: (s.UNAUTHORIZED, v.UNAUTHORIZED),
    openai.NotFoundError: (s.MODEL_NOT_FOUND, v.MODEL_NOT_FOUND),
    openai.RateLimitError: (s.API_RATE_LIMIT, v.API_RATE_LIMIT),
}


async def exception_handler(exc: Exception):
    tb = traceback.format_exc()
    await callback.on_exception(None, exc, tb=tb)
    if isinstance(exc, err.VMCException):
        return ErrorMessage(status_code=exc.code, code=exc.vmc_code, msg=exc.msg)
    if exc.__class__ in __exception_map:
        code, vmc_code = __exception_map[exc.__class__]
        return ErrorMessage(status_code=code, code=vmc_code, msg=str(exc))
    code, vmc_code = s.INTERNAL_ERROR, v.INTERNAL_ERROR
    logger.exception(exc)
    return ErrorMessage(status_code=code, code=vmc_code, msg=str(exc) + "\n" + tb)

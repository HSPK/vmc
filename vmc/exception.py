import traceback

import openai
import zhipuai
from loguru import logger

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


def _replace_markdown_image(text: str):
    import re

    return re.sub(r"!\[(.*?)\]\((.*?)\)", r"Image: \1", text)


async def exception_handler(exec: Exception):
    if isinstance(exec, err.VMCException):
        return ErrorMessage(status_code=exec.code, code=exec.vmc_code, msg=exec.msg)
    if exec.__class__ in __exception_map:
        code, vmc_code = __exception_map[exec.__class__]
        return ErrorMessage(status_code=code, code=vmc_code, msg=str(exec))
    code, vmc_code = s.INTERNAL_ERROR, v.INTERNAL_ERROR
    tb = traceback.format_exc()
    logger.exception(exec)
    return ErrorMessage(status_code=code, code=vmc_code, msg=str(exec) + "\n" + tb)

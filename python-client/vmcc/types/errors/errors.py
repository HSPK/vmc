from ._base import VMCException
from .status_code import HTTP_CODE, VMC_CODE


class AuthenticationError(VMCException):
    """AuthError: Exception for authentication error"""

    def __init__(
        self,
        http_code: int = HTTP_CODE.UNAUTHORIZED,
        vmc_code: int = VMC_CODE.UNAUTHORIZED,
        msg: str = "Authentication Error",
        **kwargs,
    ):
        super().__init__(http_code, vmc_code=vmc_code, msg=msg, **kwargs)


class ModelNotFoundError(VMCException):
    """ModelNotFoundError: Exception for model not found"""

    def __init__(
        self,
        http_code: int = HTTP_CODE.MODEL_NOT_FOUND,
        vmc_code: int = VMC_CODE.MODEL_NOT_FOUND,
        msg: str = "Model Not Found",
        **kwargs,
    ):
        super().__init__(http_code, vmc_code=vmc_code, msg=msg, **kwargs)


class GroupNotFoundError(VMCException):
    """GroupNotFoundError: Exception for group not found"""

    def __init__(
        self,
        http_code: int = HTTP_CODE.GROUP_NOT_FOUND,
        vmc_code: int = VMC_CODE.GROUP_NOT_FOUND,
        msg: str = "Group Not Found",
        **kwargs,
    ):
        super().__init__(http_code, vmc_code=vmc_code, msg=msg, **kwargs)


class GroupExistsError(VMCException):
    """GroupExistsError: Exception for group already exists"""

    def __init__(
        self,
        http_code: int = HTTP_CODE.GROUP_ALREADY_EXISTS,
        vmc_code: int = VMC_CODE.GROUP_ALREADY_EXISTS,
        msg: str = "Group Already Exists",
        **kwargs,
    ):
        super().__init__(http_code, vmc_code=vmc_code, msg=msg, **kwargs)


class ModelLoadError(VMCException):
    """ModelLoadError: Exception for model load error"""

    def __init__(
        self,
        http_code: int = HTTP_CODE.INTERNAL_ERROR,
        vmc_code: int = VMC_CODE.INTERNAL_ERROR,
        msg: str = "Model Load Error",
        **kwargs,
    ):
        super().__init__(http_code, vmc_code=vmc_code, msg=msg, **kwargs)


class IncorrectAPIKeyError(VMCException):
    """IncorrectAPIKeyError: Exception for incorrect API key error"""

    def __init__(
        self,
        http_code: int = HTTP_CODE.UNAUTHORIZED,
        vmc_code: int = VMC_CODE.UNAUTHORIZED,
        msg: str = "Incorrect API Key",
        **kwargs,
    ):
        super().__init__(http_code, vmc_code=vmc_code, msg=msg, **kwargs)


class InternalServerError(VMCException):
    """InternalServerError: Exception for internal server error"""

    def __init__(
        self,
        http_code: int = HTTP_CODE.INTERNAL_ERROR,
        vmc_code: int = VMC_CODE.INTERNAL_ERROR,
        msg: str = "Internal Server Error",
        **kwargs,
    ):
        super().__init__(http_code, vmc_code=vmc_code, msg=msg, **kwargs)


class RateLimitError(VMCException):
    """APIRateLimitError: Exception for API rate limit error"""

    def __init__(
        self,
        http_code: int = HTTP_CODE.API_RATE_LIMIT,
        vmc_code: int = VMC_CODE.API_RATE_LIMIT,
        msg: str = "API Rate Limit Error",
        **kwargs,
    ):
        super().__init__(http_code, vmc_code=vmc_code, msg=msg, **kwargs)


class BillLimitError(VMCException):
    """BillLimitError: Exception for bill limit error"""

    def __init__(
        self,
        http_code: int = HTTP_CODE.BILL_LIMIT,
        vmc_code: int = VMC_CODE.BILL_LIMIT,
        msg: str = "Bill Limit Error",
        **kwargs,
    ):
        super().__init__(http_code, vmc_code=vmc_code, msg=msg, **kwargs)


class BadParamsError(VMCException):
    """BadParamsError: Exception for bad parameters error"""

    def __init__(
        self,
        http_code: int = HTTP_CODE.BAD_PARAMS,
        vmc_code: int = VMC_CODE.BAD_PARAMS,
        msg: str = "Bad Parameters Error",
        **kwargs,
    ):
        super().__init__(http_code, vmc_code=vmc_code, msg=msg, **kwargs)


class ModelGenerateError(VMCException):
    """LocalModelGenerateError: Exception for local model generation error"""

    def __init__(
        self,
        http_code: int = HTTP_CODE.INTERNAL_ERROR,
        vmc_code: int = VMC_CODE.INTERNAL_ERROR,
        msg: str = "Model Generate Error",
        **kwargs,
    ):
        super().__init__(http_code, vmc_code=vmc_code, msg=msg, **kwargs)


class APITimeoutError(VMCException):
    def __init__(
        self,
        http_code: int = HTTP_CODE.API_TIMEOUT,
        vmc_code: int = VMC_CODE.API_TIMEOUT,
        msg: str = "API Timeout",
        **kwargs,
    ):
        super().__init__(http_code, vmc_code=vmc_code, msg=msg, **kwargs)


class BadResponseError(VMCException):
    def __init__(
        self,
        http_code: int = HTTP_CODE.BAD_RESPONSE,
        vmc_code: int = VMC_CODE.BAD_RESPONSE,
        msg: str = "Bad Response",
        **kwargs,
    ):
        super().__init__(http_code, vmc_code=vmc_code, msg=msg, **kwargs)


class APIConnectionError(VMCException):
    def __init__(
        self,
        http_code: int = HTTP_CODE.API_CONNECTION_ERROR,
        vmc_code: int = VMC_CODE.API_CONNECTION_ERROR,
        msg: str = "API Connnection Error",
        **kwargs,
    ):
        super().__init__(http_code, vmc_code=vmc_code, msg=msg, **kwargs)


class ModelNotStartedError(VMCException):
    def __init__(
        self,
        http_code: int = HTTP_CODE.MODEL_NOT_STARTED,
        vmc_code: int = VMC_CODE.MODEL_NOT_STARTED,
        msg: str = "Model Not Started",
        **kwargs,
    ):
        super().__init__(http_code, vmc_code=vmc_code, msg=msg, **kwargs)


class ManagerNotLoadedError(VMCException):
    def __init__(
        self,
        http_code: int = HTTP_CODE.MANAGER_NOT_LOADED,
        vmc_code: int = VMC_CODE.MANAGER_NOT_LOADED,
        msg: str = "Manager Not Loaded",
        **kwargs,
    ):
        super().__init__(http_code, vmc_code=vmc_code, msg=msg, **kwargs)

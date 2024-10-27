from pydantic import BaseModel


class AuthParams(BaseModel):
    """AuthParams: Parameters for authentication"""

    user_name: str
    user_password: str
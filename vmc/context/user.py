from contextvars import ContextVar
from dataclasses import dataclass


# The context variable for the current user.
@dataclass
class User:
    id: str
    name: str
    email: str
    role: str


current_user: ContextVar[User] = ContextVar("current_user", default=User("", "", "", ""))

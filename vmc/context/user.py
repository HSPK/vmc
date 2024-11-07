from contextvars import ContextVar

# Import LocalProxy from werkzeug.local to create a proxy object
from werkzeug.local import LocalProxy

from vmc.db.schema import User

current_user: User = LocalProxy(lambda: _get_user())
_current_user: ContextVar[User] = ContextVar("current_user", default=None)


def _get_user():
    return _current_user.get()


def set_user(user: User):
    _current_user.set(user)

import sys

from nicegui import app


class _M(object):
    def __init__(self):
        pass

    @property
    def user(self):
        return app.storage.user

    @property
    def authenticated(self):
        return app.storage.user.get("authenticated", False)

    @property
    def username(self):
        return app.storage.user.get("username", "")

    @property
    def user_id(self):
        return app.storage.user.get("user_id", "")


sys.modules[__name__] = _M()

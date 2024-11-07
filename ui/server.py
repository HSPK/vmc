from typing import Optional

from dotenv import find_dotenv, load_dotenv
from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import app, ui
from starlette.middleware.base import BaseHTTPMiddleware

from ui.frontend.routes.conv import router

load_dotenv(find_dotenv())


class Passwords:
    def __init__(self):
        self.passwords = {
            "puyuan": {"password": "puyuan.tech", "id": "puyuan"},
            "admin": {"password": "admin.abc", "id": "admin"},
        }

    def get(self, username: str) -> dict[str, str]:
        if username in self.passwords:
            return self.passwords[username]["password"]
        return None

    def get_id(self, username: str) -> str:
        if username in self.passwords:
            return self.passwords[username]["id"]
        return None


passwords = Passwords()
unrestricted_page_routes = {"/login"}


class AuthMiddleware(BaseHTTPMiddleware):
    """This middleware restricts access to all NiceGUI pages.

    It redirects the user to the login page if they are not authenticated.
    """

    async def dispatch(self, request: Request, call_next):
        if not app.storage.user.get("authenticated", False):
            if (
                not request.url.path.startswith("/_nicegui")
                and request.url.path not in unrestricted_page_routes
            ):
                app.storage.user["referrer_path"] = (
                    request.url.path
                )  # remember where the user wanted to go
                return RedirectResponse("/login")
        return await call_next(request)


app.add_middleware(AuthMiddleware)


@ui.page("/login")
async def login() -> Optional[RedirectResponse]:
    def try_login() -> None:  # local function to avoid passing username and password as arguments
        if passwords.get(username.value) == password.value:
            app.storage.user.update(
                {
                    "username": username.value,
                    "authenticated": True,
                    "user_id": passwords.get_id(username.value),
                }
            )
            ui.navigate.to(app.storage.user.get("referrer_path", "/"))
        else:
            ui.notify("Wrong username or password", color="negative")

    if app.storage.user.get("authenticated", False):
        return RedirectResponse("/")
    with ui.card().classes("absolute-center max-w-sm"):
        username = ui.input("Username").on("keydown.enter", try_login)
        password = ui.input("Password", password=True, password_toggle_button=True).on(
            "keydown.enter", try_login
        )
        ui.button("Log in", on_click=try_login).classes("self-end")
    return None


@ui.page("/")
async def index():
    ui.navigate.to("/conv")


@ui.page("/logout")
async def logout():
    app.storage.user.clear()
    return RedirectResponse("/login")


app.include_router(router)

ui.run(title="NewBI", dark=False, port=12101, storage_secret="sc-2023-10-11")

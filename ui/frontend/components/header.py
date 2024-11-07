from typing import TYPE_CHECKING

from nicegui import ui

if TYPE_CHECKING:
    from ui.frontend.components.history_drawer import HistoryDrawer


class ChatHeader(ui.header):
    def __init__(
        self,
        *,
        history_drawer: "HistoryDrawer" = None,
        value=True,
        fixed=True,
        bordered=False,
        elevated=False,
        wrap=True,
        add_scroll_padding=True,
    ):
        super().__init__(
            value=value,
            fixed=fixed,
            bordered=bordered,
            elevated=elevated,
            wrap=wrap,
            add_scroll_padding=add_scroll_padding,
        )
        self.classes("bg-white h-15 items-center px-5 py-2.5 -space-x-2")
        self.history_drawer = history_drawer
        with self:
            self.build()

    def build(self):
        icon_classes = "text-gray-600 rounded-lg p-2 hover:bg-slate-200 cursor-pointer"
        with ui.row().classes("items-center -space-x-3").bind_visibility_from(
            self.history_drawer, "opened", value=False
        ):
            with ui.icon("view_list", size="sm").classes(icon_classes).on(
                "click", self.history_drawer.toggle
            ):
                ui.tooltip("Open").classes("text-white text-sm bg-black no-wrap")
            with ui.icon("edit", size="sm").classes(icon_classes).on(
                "click", lambda: ui.navigate.to("/conv")
            ):
                ui.tooltip("New Chat").classes("text-white text-sm bg-black no-wrap")
        ui.space().classes("md:hidden")
        ui.label("NewBI").classes(
            "font-bold text-xl font-serif text-gray-600 "
            "rounded-lg hover:bg-gray-100 "
            "px-3 py-2 cursor-pointer"
        )
        ui.space()
        with ui.row().classes("items-center -space-x-1"):
            ui.avatar("person", size="md").classes(
                "hover:ring-2 ring-primary ring-opacity-50 cursor-pointer"
            )
            ui.icon("logout", size="sm").classes(
                "text-gray-600 rounded-lg p-2 hover:bg-slate-200 cursor-pointer"
            ).on("click", lambda e: ui.navigate.to("/logout"))

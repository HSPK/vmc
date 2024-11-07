from typing import Callable

from nicegui import ui

from ui.db.schema import ConvSummary


class ConversationItem(ui.item):
    def __init__(
        self,
        *,
        on_conv_click: Callable[[str], None],
        on_conv_rename: Callable[[str, str], None],
        on_conv_delete: Callable[["ConversationItem"], None],
        conv: ConvSummary,
    ):
        super().__init__()
        self.classes(
            "w-full items-center group cursor-pointer rounded-lg hover:bg-gray-200 px-3 py-0 z-0"
        )
        self.props("clickable")
        self.conv = conv
        self.conv_id = conv.id
        self._on_conv_click = on_conv_click
        self._on_conv_rename = on_conv_rename
        self._on_conv_delete = on_conv_delete
        with self:
            self.build()
            self.on("click", self.on_conv_click)

    async def on_conv_click(self):
        return await self._on_conv_click(self.conv_id)

    async def on_conv_rename(self, title: str):
        if not title:
            return False
        await self._on_conv_rename(self.conv_id, title)
        self.conv.title = title
        return True

    def build(self):
        summary = ui.label(self.conv.title).classes("text-sm line-clamp-2")
        self.name = summary
        with ui.icon("more_horiz", size="sm").classes(
            "absolute right-2 top-1"
            "text-gray-600 bg-gray-200 bg-opacity-90 p-2 rounded-3xl hover:bg-gray-300 cursor-pointer"
        ).on("click.stop", lambda: menu.open()) as more:
            self.more = more

            async def rename():
                summary.set_visibility(False)
                more.set_visibility(False)

                async def set_title():
                    if await self.on_conv_rename(new_name_input.value):
                        summary.set_text(new_name_input.value)
                        summary.set_visibility(True)
                        more.set_visibility(True)
                        self.remove(new_name_input)
                    else:
                        ui.notify("Invalid title")
                        summary.set_visibility(True)
                        more.set_visibility(True)
                        self.remove(new_name_input)

                with self:
                    new_name_input = (
                        ui.input(value=summary.text)
                        .classes("text-sm line-clamp-2 -my-3")
                        .props("borderless autofocus")
                        .classes("text-sm")
                        .on("keydown.enter", lambda e: set_title())
                        .on("blur", lambda e: set_title())
                    )

            async def delete():
                await self._on_conv_delete(self)
                ui.notify("Deleted")
                dialog.close()

            with ui.dialog().classes() as dialog, ui.card().classes("p-4"):
                ui.label("Are you sure you want to delete this item?")
                with ui.row().classes("w-full"):
                    ui.button("Cancel").on("click", dialog.close)
                    ui.space()
                    ui.button("Delete").on("click", delete)

            with ui.menu().classes("rounded-lg shadow-lg") as menu:
                ui.menu_item("Rename").on("click", rename)
                ui.menu_item("Delete").classes("text-red-500").on("click", dialog.open)

            more.visible = False
            self.on(
                "mouseenter",
                lambda e: more.set_visibility(True) if summary.visible else None,
            )
            self.on(
                "mouseleave",
                lambda e: more.set_visibility(False)
                if summary.visible and not menu.value
                else None,
            )


class HistoryDrawer(ui.left_drawer):
    def __init__(
        self,
        *,
        on_conv_click: Callable[[str], None],
        on_conv_delete: Callable[[str], None],
        on_conv_rename: Callable[[str, str], None],
        value=False,
    ):
        super().__init__(value=value, top_corner=True, bottom_corner=True)
        self.opened = value
        self._on_conv_click = on_conv_click
        self._on_conv_delete = on_conv_delete
        self._on_conv_rename = on_conv_rename

        self.classes("bg-gray-100 px-3").props("bordered width=270 sm:overlay")
        icon_classes = "text-gray-600 rounded-lg p-2 hover:bg-slate-200 cursor-pointer"
        with self:
            with ui.row().classes("flex items-center w-full -my-1 mx-2"):
                with ui.icon("view_list", size="sm").classes(icon_classes).on("click", self.toggle):
                    ui.tooltip("Close Sidebar").classes("text-white text-sm bg-black")
                with ui.icon("edit", size="sm").classes(icon_classes + " ml-auto mr-4").on(
                    "click", lambda: ui.navigate.to("/conv")
                ):
                    ui.tooltip("New Chat").classes("text-white text-sm bg-black")
            ui.label("History\n").classes("text-black font-semibold text-md px-2.5 -mb-2 mt-1")
            self.conv_list = ui.list().classes("w-full space-y-1")

    def hide(self):
        self.opened = False
        return super().hide()

    def show(self):
        self.opened = True
        return super().show()

    def toggle(self):
        if self.opened:
            self.hide()
        else:
            self.show()

    def create_conv(self, conv: ConvSummary):
        async def on_delete(conv: ConversationItem):
            if self._on_conv_delete:
                await self._on_conv_delete(conv.conv_id)
            self.conv_list.remove(conv)

        with self.conv_list:
            ConversationItem(
                on_conv_click=self._on_conv_click,
                on_conv_delete=on_delete,
                on_conv_rename=self._on_conv_rename,
                conv=conv,
            )

    def set_convs(self, convs: list[ConvSummary]):
        for conv in convs:
            self.create_conv(conv)

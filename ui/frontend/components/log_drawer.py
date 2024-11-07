from nicegui import ui


class LogDrawer(ui.right_drawer):
    def __init__(
        self,
        *,
        value=False,
        fixed=True,
        bordered=False,
        elevated=False,
        top_corner=True,
        bottom_corner=True,
    ):
        super().__init__(
            value=value,
            fixed=fixed,
            bordered=bordered,
            elevated=elevated,
            top_corner=top_corner,
            bottom_corner=bottom_corner,
        )
        self.classes("bg-teal-50 w-full shadow-lg px-")
        self.props("overlay width=350")
        with self:
            self.build()

    def build(self):
        ui.label("Details").classes("font-semibold self-center text-gray-700 text-2xl mt-3")
        with ui.log().classes("w-full h-full") as log:
            self.log = log

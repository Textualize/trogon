from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll, Vertical
from textual.screen import ModalScreen
from textual.widgets import Static, Tabs, Tab

from textual_click.introspect import CommandSchema
from textual_click.widgets.multiple_choice import NonFocusableVerticalScroll


class CommandInfo(ModalScreen):
    COMPONENT_CLASSES = {"title", "subtitle"}

    BINDINGS = [
        Binding("q,escape", "close_modal", "Close Modal")
    ]

    def __init__(
        self,
        command_schema: CommandSchema,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(
            name=name,
            id=id,
            classes=classes,
        )
        self.command_schema = command_schema

    def compose(self) -> ComposeResult:
        schema = self.command_schema
        path = schema.path_from_root
        path_string = " ➜ ".join(command.name for command in path)

        title_style = self.get_component_rich_style("title")
        subtitle_style = self.get_component_rich_style("subtitle")
        modal_header = Text.assemble(
            (path_string, title_style), "\n", ("command info", subtitle_style)
        )
        with NonFocusableVerticalScroll(classes="command-info-container"):
            with Vertical(classes="command-info-header"):
                yield Static(modal_header, classes="command-info-header-text")
                tabs = Tabs(Tab("Description"), Tab("Metadata"),
                           classes="command-info-tabs")
                tabs.focus()
                yield tabs

            command_info = self.command_schema.docstring
            if command_info:
                command_info = command_info.strip()
            yield Static(command_info, classes="command-info-text")

    def action_close_modal(self):
        self.app.pop_screen()

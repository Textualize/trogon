from __future__ import annotations

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static, Tabs, Tab, ContentSwitcher, DataTable

from trogon.introspect import CommandSchema
from trogon.widgets.multiple_choice import NonFocusableVerticalScroll


class CommandMetadata(DataTable):
    def __init__(
        self,
        command_schema: CommandSchema,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self.show_header = False
        self.zebra_stripes = True
        self.cursor_type = "none"
        self.command_schema = command_schema

    def on_mount(self) -> None:
        self.add_columns("Key", "Value")
        schema = self.command_schema
        self.add_rows(
            [
                (Text("Name", style="b"), schema.name),
                (
                    Text("Parent", style="b"),
                    getattr(schema.parent, "name", "No parent"),
                ),
                (Text("Subcommands", style="b"), list(schema.subcommands.keys())),
                (Text("Group", style="b"), schema.is_group),
                (Text("Arguments", style="b"), len(schema.arguments)),
                (Text("Options", style="b"), len(schema.options)),
            ]
        )


class CommandInfo(ModalScreen):
    COMPONENT_CLASSES = {"title", "subtitle"}

    BINDINGS = [Binding("q,escape", "close_modal", "Close Modal")]

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
                tabs = Tabs(
                    Tab("Description", id="command-info-text"),
                    Tab("Metadata", id="command-info-metadata"),
                    classes="command-info-tabs",
                )
                tabs.focus()
                yield tabs

            command_info = (
                self.command_schema.docstring.strip()
                if self.command_schema.docstring
                else "No description available"
            )

            with ContentSwitcher(
                initial="command-info-text", id="command-info-switcher"
            ):
                yield Static(
                    command_info, id="command-info-text", classes="command-info-text"
                )
                yield CommandMetadata(
                    command_schema=self.command_schema,
                    id="command-info-metadata",
                    classes="command-info-metadata",
                )

    @on(Tabs.TabActivated)
    def switch_content(self, event: Tabs.TabActivated) -> None:
        self.query_one(ContentSwitcher).current = event.tab.id

    def action_close_modal(self):
        self.app.pop_screen()

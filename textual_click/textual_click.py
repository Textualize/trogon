from __future__ import annotations

import os
import shlex
from pathlib import Path

import click
from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.text import Text
from textual import log, events
from textual.app import ComposeResult, App, AutopilotCallbackType
from textual.binding import Binding
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.css.query import NoMatches
from textual.screen import Screen
from textual.widgets import (
    Pretty,
    Tree,
    Label,
    Static,
    Button,
    Footer,
)
from textual.widgets.tree import TreeNode

from textual_click.widgets.form import CommandForm
from textual_click.introspect import (
    introspect_click_app,
    CommandSchema,
)
from textual_click.run_command import UserCommandData
from textual_click.widgets.command_tree import CommandTree


class CommandBuilder(Screen):
    BINDINGS = [
        Binding(key="ctrl+r", action="close_and_run", description="Close & Run")
    ]

    def __init__(
        self,
        cli: click.BaseCommand,
        click_app_name: str,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ):
        super().__init__(name, id, classes)
        self.command_data = None
        self.cli = cli
        self.is_grouped_cli = isinstance(cli, click.Group)
        self.command_schemas = introspect_click_app(cli)
        self.click_app_name = click_app_name
        self.highlighter = ReprHighlighter()

    def compose(self) -> ComposeResult:
        tree = CommandTree("", self.command_schemas)

        sidebar = Vertical(
            Label(self.click_app_name, id="home-commands-label"),
            tree,
            id="home-sidebar",
        )
        if self.is_grouped_cli:
            # If the root of the click app is a Group instance, then
            #  we display the command tree to users and focus it.
            tree.focus()
        else:
            # If the click app is structured using a single command,
            #  there's no need for us to display the command tree.
            sidebar.display = False
        yield sidebar

        scrollable_body = Vertical(
            Pretty(self.command_schemas),
            id="home-body-scroll",
        )
        scrollable_body.can_focus = False

        body = Vertical(
            VerticalScroll(
                Static(self.click_app_name or "", id="home-command-description"),
                id="home-command-description-container",
            ),
            scrollable_body,
            Horizontal(
                Static("", id="home-exec-preview-static"),
                Vertical(
                    Button.success("Close & Run", id="home-exec-button"),
                    id="home-exec-preview-buttons",
                ),
                id="home-exec-preview",
            ),
            id="home-body",
        )
        yield body
        yield Footer()

    def action_close_and_run(self) -> None:
        self.app.execute_on_exit = True
        self.app.exit()

    async def on_mount(self, event: events.Mount) -> None:
        await self._refresh_command_form()

    async def _refresh_command_form(self, node: TreeNode[CommandSchema] | None = None):
        if node is None:
            try:
                command_tree = self.query_one(CommandTree)
                node = command_tree.cursor_node
            except NoMatches:
                print("Failed to refresh command form.")
                return

        self.selected_command_schema = node.data
        self._update_command_description(node)
        self._update_execution_string_preview(
            self.selected_command_schema, self.command_data
        )
        await self._update_form_body(node)

    async def on_tree_node_highlighted(
        self, event: Tree.NodeHighlighted[CommandSchema]
    ) -> None:
        """When we highlight a node in the CommandTree, the main body of the home page updates
        to display a form specific to the highlighted command."""
        # TODO: Add an ID check
        await self._refresh_command_form(event.node)
        self._update_execution_string_preview(
            self.selected_command_schema, self.command_data
        )

    def on_command_form_changed(self, event: CommandForm.Changed) -> None:
        self.command_data = event.command_data
        self._update_execution_string_preview(
            self.selected_command_schema, self.command_data
        )
        log(event.command_data.to_cli_string())

    def _update_command_description(self, node: TreeNode[CommandSchema]) -> None:
        """Update the description of the command at the bottom of the sidebar
        based on the currently selected node in the command tree."""
        description_box = self.query_one("#home-command-description", Static)
        description_text = node.data.docstring or ""
        description_text = f"[b]{node.label if self.is_grouped_cli else self.click_app_name}[/]\n{description_text}"
        description_box.update(description_text)

    def _update_execution_string_preview(
        self, command_schema: CommandSchema, command_data: UserCommandData
    ) -> None:
        """Update the preview box showing the command string to be executed"""
        if self.command_data is not None:
            prefix = Text(f"{self.click_app_name} ")
            include_root = self.is_grouped_cli
            new_value = command_data.to_cli_string(include_root_command=include_root)
            highlighted_new_value = prefix.append(self.highlighter(new_value))
            self.query_one("#home-exec-preview-static", Static).update(
                highlighted_new_value
            )

    async def _update_form_body(self, node: TreeNode[CommandSchema]) -> None:
        # self.query_one(Pretty).update(node.data)
        parent = self.query_one("#home-body-scroll", Vertical)
        for child in parent.children:
            await child.remove()

        # Process the metadata for this command and mount corresponding widgets
        command_schema = node.data
        command_form = CommandForm(
            command_schema=command_schema, command_schemas=self.command_schemas
        )
        await parent.mount(command_form)
        if not self.is_grouped_cli:
            command_form.focus()


class TextualClick(App):
    CSS_PATH = Path(__file__).parent / "textual_click.scss"

    def __init__(
        self,
        cli: click.Group,
        app_name: str = None,
        click_context: click.Context = None,
    ) -> None:
        super().__init__()
        self.cli = cli
        self.post_run_command: list[str] = []
        self.execute_on_exit = False
        self.click_context = click_context
        self.app_name = click_context.find_root().info_name

    def on_mount(self):
        self.push_screen(CommandBuilder(self.cli, self.app_name))

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "home-exec-button":
            self.execute_on_exit = True
            self.exit()

    def run(
        self,
        *,
        headless: bool = False,
        size: tuple[int, int] | None = None,
        auto_pilot: AutopilotCallbackType | None = None,
    ) -> None:
        try:
            super().run(headless=headless, size=size, auto_pilot=auto_pilot)
        finally:
            if self.post_run_command:
                console = Console()
                if self.post_run_command and self.execute_on_exit:
                    console.print(
                        f"Running [b cyan]{self.app_name} {shlex.join(self.post_run_command)}[/]"
                    )
                    os.execvp(self.app_name, [self.app_name, *self.post_run_command])

    def on_command_form_changed(self, event: CommandForm.Changed):
        self.post_run_command = event.command_data.to_cli_args()


def tui(name: str = "TUI Mode"):
    def decorator(app: click.Group | click.Command):
        @click.pass_context
        def wrapped_tui(ctx, *args, **kwargs):
            TextualClick(app, app_name=name, click_context=ctx).run()

        if isinstance(app, click.Group):
            app.command(name="tui")(wrapped_tui)
        else:
            new_group = click.Group()
            new_group.add_command(app)
            new_group.command(name="tui")(wrapped_tui)
            return new_group

        return app

    return decorator

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path
from typing import Sequence

import click
from rich.console import Console
from rich.style import Style
from rich.text import TextType, Text
from textual import log
from textual.app import ComposeResult, App, AutopilotCallbackType, ReturnType
from textual.containers import VerticalScroll, Vertical, Horizontal
from textual.message import Message
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import (
    Pretty,
    Tree,
    Label,
    Static,
    Button,
    Input,
    Checkbox,
    RadioSet,
    RadioButton,
)
from textual.widgets._tree import TreeDataType
from textual.widgets.tree import TreeNode

from textual_click.introspect import (
    introspect_click_app,
    CommandName,
    CommandSchema,
    ArgumentSchema,
    OptionSchema,
)
from textual_click.run_command import UserCommandData


class CommandTree(Tree[CommandSchema]):
    def __init__(self, label: TextType, cli_metadata: dict[CommandName, CommandSchema]):
        super().__init__(label)
        self.show_root = False
        self.guide_depth = 3
        self.cli_metadata = cli_metadata

    def render_label(
        self, node: TreeNode[TreeDataType], base_style: Style, style: Style
    ) -> Text:
        label = node._label.copy()
        label.stylize(style)
        return label

    def on_mount(self):
        def build_tree(
            data: dict[CommandName, CommandSchema], node: TreeNode
        ) -> TreeNode:
            for cmd_name, cmd_data in data.items():
                if cmd_data.subcommands:
                    child = node.add(cmd_name, allow_expand=False, data=cmd_data)
                    build_tree(cmd_data.subcommands, child)
                else:
                    node.add_leaf(cmd_name, data=cmd_data)
            return node

        build_tree(self.cli_metadata, self.root)
        self.root.expand_all()
        self.select_node(self.root)


class CommandForm(Widget):
    DEFAULT_CSS = """
    .command-form-heading {
        padding: 1 0 0 2;
        text-style: bold;
    }
    .command-form-label {
        padding: 1 0 0 2;
    }
    .command-form-radioset {
        margin: 0 2;
    }
    .command-form-checkbox {
        padding: 1 2;
    }
    """

    class FormUpdated(Message):
        def __init__(self, command_data: UserCommandData):
            super().__init__()
            self.command_data = command_data
            """The new data taken from the form to be converted into a CLI invocation."""

    def __init__(
        self,
        command_schema: CommandSchema | None = None,
        command_schemas: dict[CommandName, CommandSchema] | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.command_schema = command_schema
        self.command_schemas = command_schemas

    def compose(self) -> ComposeResult:
        options = self.command_schema.options
        arguments = self.command_schema.arguments

        if options:
            yield Label("Options", classes="command-form-heading")
            yield from self._make_command_form(options)

        if arguments:
            yield Label("Arguments", classes="command-form-heading")
            yield from self._make_command_form(arguments)

        if not options and not arguments:
            # TODO - improve this...
            yield Label(
                "Choose a command from the sidebar", classes="command-form-label"
            )

    def _make_command_form(self, arguments: Sequence[ArgumentSchema | OptionSchema]):
        for argument in arguments:
            name = argument.name
            argument_type = argument.type
            default = argument.default
            help = argument.help if isinstance(argument, OptionSchema) else ""
            label = self._make_command_form_control_label(name, argument_type)
            if argument_type in {"text", "float", "integer", "Path"}:
                yield Label(label, classes="command-form-label")
                yield Input(
                    value=str(default) if default is not None else "",
                    placeholder=help if help else label.plain,
                )
            elif argument_type in {"boolean"}:
                yield Checkbox(
                    f"{name} ({argument_type})",
                    button_first=False,
                    value=default,
                    classes="command-form-checkbox",
                )
            elif argument_type in {"choice"}:
                choices = argument.choices
                with RadioSet(classes="command-form-radioset"):
                    for choice in choices:
                        yield RadioButton(choice)


    # def _build_command_data(self) -> UserCommandData:
    #     """Takes the current state of this form and converts it into a UserCommandData,
    #     ready to be executed."""

    # def _validate_command_data(self) -> None:
    #     validate_user_command_data(self.command_schemas, self.)

    @staticmethod
    def _make_command_form_control_label(name: str, type: str) -> Text:
        return Text.from_markup(f"{name} [dim]{type}[/]")


class CommandBuilder(Screen):
    def __init__(
        self,
        cli: click.Group,
        click_app_name: str,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ):
        super().__init__(name, id, classes)
        self.command_schemas = introspect_click_app(cli)
        self.click_app_name = click_app_name

    def compose(self) -> ComposeResult:
        tree = CommandTree("", self.command_schemas)
        tree.focus()
        yield Vertical(
            Label("Command Builder", id="home-commands-label"), tree, id="home-sidebar"
        )

        scrollable_body = VerticalScroll(
            Pretty(self.command_schemas),
            id="home-body-scroll",
        )
        body = Vertical(
            Static("", id="home-command-description"),
            scrollable_body,
            Horizontal(
                Static("", id="home-exec-preview-static"),
                Vertical(
                    Button.success("Execute"),
                    id="home-exec-preview-buttons",
                ),
                id="home-exec-preview",
            ),
            id="home-body",
        )
        scrollable_body.can_focus = True
        yield body

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted):
        """When we highlight a node in the CommandTree, the main body of the home page updates
        to display a form specific to the highlighted command."""

        # TODO: Add an ID check

        command_string = self._build_command_from_node(event.node)
        self._update_command_description(event.node)
        self._update_execution_string_preview(command_string.plain)
        self._update_form_body(event.node)

    def _build_command_from_node(self, node: TreeNode) -> Text:
        """Given a TreeNode, look up the ancestors and build the Text required
        to call that command."""
        command_parts = [node.label]
        while node:
            node = node.parent
            if node.parent is None:
                break
            else:
                command_parts.append(node.label)
        return Text(" ").join(reversed(command_parts))

    def _update_command_description(self, node: TreeNode[CommandSchema]) -> None:
        """Update the description of the command at the bottom of the sidebar
        based on the currently selected node in the command tree."""
        description_box = self.query_one("#home-command-description", Static)
        description_text = node.data.docstring or ""
        description_text = f"[b]{node.label}[/]\n{description_text}"
        description_box.update(description_text)

    def _update_execution_string_preview(self, command_string: str) -> None:
        """Update the preview box showing the command string to be executed"""
        self.query_one("#home-exec-preview-static", Static).update(command_string)

    def _update_form_body(self, node: TreeNode[CommandSchema]) -> None:
        # self.query_one(Pretty).update(node.data)
        parent = self.query_one("#home-body-scroll", VerticalScroll)
        for child in parent.children:
            child.remove()

        # Process the metadata for this command and mount corresponding widgets
        command_schema = node.data
        log(command_schema)
        parent.mount(
            CommandForm(
                command_schema=command_schema, command_schemas=self.command_schemas
            )
        )


class TextualClick(App):
    CSS_PATH = Path(__file__).parent / "textual_click.scss"

    def __init__(self, cli: click.Group, app_name: str = None) -> None:
        super().__init__()
        self.cli = cli
        self.app_name = app_name
        # TODO: Don't hardcode ls
        self.post_run_command: list[str] = ["ls"]

    def on_mount(self):
        self.push_screen(CommandBuilder(self.cli, self.app_name))

    def run(
        self,
        *,
        headless: bool = False,
        size: tuple[int, int] | None = None,
        auto_pilot: AutopilotCallbackType | None = None,
    ) -> ReturnType | None:
        try:
            super().run(headless=headless, size=size, auto_pilot=auto_pilot)
        finally:
            # TODO: Make this happen only when you Execute/Save+Execute
            if self.post_run_command:
                console = Console()
                console.print(f"Running [b cyan]{shlex.join(self.post_run_command)}[/]")
                subprocess.run(self.post_run_command)
        return

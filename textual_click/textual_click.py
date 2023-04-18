from __future__ import annotations

from pathlib import Path
from typing import Any

import click
from rich.style import Style
from rich.text import TextType, Text
from textual.app import ComposeResult, App
from textual.containers import VerticalScroll, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Pretty, Tree, Label, Static, Button
from textual.widgets._tree import TreeDataType
from textual.widgets.tree import TreeNode

from textual_click.introspect import introspect_click_app


class CommandTree(Tree):

    def __init__(self, label: TextType, cli_metadata: dict[str, Any]):
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
        def build_tree(data: dict[str, Any], node: TreeNode) -> TreeNode:
            for cmd_name, cmd_data in data.items():
                if cmd_data["subcommands"]:
                    child = node.add(cmd_name, allow_expand=False, data=cmd_data)
                    build_tree(cmd_data["subcommands"], child)
                else:
                    node.add_leaf(cmd_name, data=cmd_data)
            return node

        build_tree(self.cli_metadata, self.root)
        self.root.expand_all()
        self.select_node(self.root)


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
        self.cli_metadata = introspect_click_app(cli)
        self.click_app_name = click_app_name

    def compose(self) -> ComposeResult:
        tree = CommandTree("", self.cli_metadata)
        tree.focus()
        yield Vertical(
            Label("Command Builder", id="home-commands-label"),
            tree,
            Static("", id="home-sidebar-description"),
            id="home-sidebar"
        )

        scrollable_body = VerticalScroll(
            Pretty(self.cli_metadata),
            id="home-body-scroll",
        )
        body = Vertical(
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

        # Look from the highlighted node up to the root node to build up the string
        # containing the commands and subcommands...

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

    def _update_command_description(self, node: TreeNode) -> None:
        """Update the description of the command at the bottom of the sidebar
        based on the currently selected node in the command tree."""
        description_box = self.query_one("#home-sidebar-description", Static)
        description_text = node.data.get("docstring") or ""
        description_text = f"[b]{node.label}[/]\n{description_text}"
        description_box.update(description_text)

    def _update_execution_string_preview(self, command_string: str) -> None:
        """Update the preview box showing the command string to be executed"""
        self.query_one("#home-exec-preview-static", Static).update(command_string)

    def _update_form_body(self, node: TreeNode) -> None:
        # TODO - this is temporary
        self.query_one(Pretty).update(node.data)


class TextualClick(App):
    CSS_PATH = Path(__file__).parent / "textual_click.scss"

    def __init__(self, cli: click.Group, app_name: str = None) -> None:
        super().__init__()
        self.cli = cli
        self.app_name = app_name

    def on_mount(self):
        self.push_screen(CommandBuilder(self.cli, self.app_name))

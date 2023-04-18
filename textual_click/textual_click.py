from __future__ import annotations

from pathlib import Path
from typing import Any

import click
from rich.style import Style
from rich.text import TextType, Text
from textual.app import ComposeResult, App
from textual.containers import VerticalScroll, Vertical
from textual.widgets import Pretty, Tree, Label
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
                    child = node.add(cmd_name)
                    build_tree(cmd_data["subcommands"], child)
                else:
                    node.add_leaf(cmd_name)
            return node

        build_tree(self.cli_metadata, self.root)
        self.root.expand_all()
        self.select_node(self.root)


class TextualClick(App):
    CSS_PATH = Path(__file__).parent / "textual_click.scss"

    def __init__(self, cli: click.Group, app_name: str = None) -> None:
        super().__init__()
        self.cli = cli
        self.app_name = app_name
        self.cli_metadata = introspect_click_app(cli)

    def compose(self) -> ComposeResult:
        tree = CommandTree("", self.cli_metadata)
        tree.focus()
        yield Vertical(
            Label("Commands", id="home-commands-label"),
            tree,
            id="home-sidebar"
        )

        body = VerticalScroll(
            Pretty(self.cli_metadata),
            id="home-body",
        )
        body.can_focus = True
        yield body

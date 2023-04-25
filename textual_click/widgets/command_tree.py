from __future__ import annotations

from rich.style import Style
from rich.text import TextType, Text
from textual.widgets import Tree
from textual.widgets._tree import TreeNode, TreeDataType

from textual_click.introspect import CommandSchema, CommandName


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
                if not cmd_data.subcommands and not cmd_data.options and not cmd_data.arguments:
                    continue
                if cmd_data.subcommands:
                    child = node.add(cmd_name, allow_expand=False, data=cmd_data)
                    build_tree(cmd_data.subcommands, child)
                else:
                    node.add_leaf(cmd_name, data=cmd_data)
            return node

        build_tree(self.cli_metadata, self.root)
        self.root.expand_all()
        self.select_node(self.root)

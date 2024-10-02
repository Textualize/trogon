from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence, NewType

import click
from click import BaseCommand, ParamType


def generate_unique_id():
    return f"id_{str(uuid.uuid4())[:8]}"


@dataclass
class MultiValueParamData:
    values: list[tuple[int | float | str]]

    @staticmethod
    def process_cli_option(value) -> "MultiValueParamData":
        if value is None:
            value = MultiValueParamData([])
        elif isinstance(value, tuple):
            value = MultiValueParamData([value])
        elif isinstance(value, list):
            processed_list = [
                (item,) if not isinstance(item, tuple) else item for item in value
            ]
            value = MultiValueParamData(processed_list)
        else:
            value = MultiValueParamData([(value,)])

        return value


@dataclass
class OptionSchema:
    name: list[str]
    type: ParamType
    default: MultiValueParamData | None = None
    required: bool = False
    is_flag: bool = False
    is_boolean_flag: bool = False
    flag_value: Any = ""
    opts: list[str] = field(default_factory=list)
    counting: bool = False
    secondary_opts: list[str] = field(default_factory=list)
    key: str | tuple[str] = field(default_factory=generate_unique_id)
    help: str | None = None
    choices: Sequence[str] | None = None
    multiple: bool = False
    multi_value: bool = False
    nargs: int = 1

    def __post_init__(self):
        self.multi_value = isinstance(self.type, click.Tuple)


@dataclass
class ArgumentSchema:
    name: str
    type: str
    required: bool = False
    key: str = field(default_factory=generate_unique_id)
    default: MultiValueParamData | None = None
    choices: Sequence[str] | None = None
    multiple: bool = False
    nargs: int = 1


@dataclass
class CommandSchema:
    name: CommandName
    function: Callable[..., Any | None]
    key: str = field(default_factory=generate_unique_id)
    docstring: str | None = None
    options: list[OptionSchema] = field(default_factory=list)
    arguments: list[ArgumentSchema] = field(default_factory=list)
    subcommands: dict["CommandName", "CommandSchema"] = field(default_factory=dict)
    parent: "CommandSchema | None" = None
    is_group: bool = False

    @property
    def path_from_root(self) -> list["CommandSchema"]:
        node = self
        path: list[CommandSchema] = [self]
        while True:
            node = node.parent
            if node is None:
                break
            path.append(node)
        return list(reversed(path))


def introspect_click_app(app: BaseCommand) -> dict[CommandName, CommandSchema]:
    """
    Introspect a Click application and build a data structure containing
    information about all commands, options, arguments, and subcommands,
    including the docstrings and command function references.

    This function recursively processes each command and its subcommands
    (if any), creating a nested dictionary that includes details about
    options, arguments, and subcommands, as well as the docstrings and
    command function references.

    Args:
        app (click.BaseCommand): The Click application's top-level group or command instance.

    Returns:
        Dict[str, CommandData]: A nested dictionary containing the Click application's
        structure. The structure is defined by the CommandData TypedDict and its related
        TypedDicts (OptionData and ArgumentData).
    """

    def process_command(
        cmd_name: CommandName, cmd_obj: click.Command, parent=None
    ) -> CommandSchema:
        cmd_data = CommandSchema(
            name=cmd_name,
            docstring=cmd_obj.help,
            function=cmd_obj.callback,
            options=[],
            arguments=[],
            subcommands={},
            parent=parent,
            is_group=isinstance(cmd_obj, click.Group),
        )

        for param in cmd_obj.params:
            default = MultiValueParamData.process_cli_option(param.default)
            if isinstance(param, (click.Option, click.core.Group)):
                option_data = OptionSchema(
                    name=param.opts,
                    type=param.type,
                    is_flag=param.is_flag,
                    is_boolean_flag=param.is_bool_flag,
                    flag_value=param.flag_value,
                    counting=param.count,
                    opts=param.opts,
                    secondary_opts=param.secondary_opts,
                    required=param.required,
                    default=default,
                    help=param.help,
                    multiple=param.multiple,
                    nargs=param.nargs,
                )
                if isinstance(param.type, click.Choice):
                    option_data.choices = param.type.choices
                cmd_data.options.append(option_data)
            elif isinstance(param, click.Argument):
                argument_data = ArgumentSchema(
                    name=param.name,
                    type=param.type,
                    required=param.required,
                    multiple=param.multiple,
                    default=default,
                    nargs=param.nargs,
                )
                if isinstance(param.type, click.Choice):
                    argument_data.choices = param.type.choices
                cmd_data.arguments.append(argument_data)

        if isinstance(cmd_obj, click.core.Group):
            for subcmd_name, subcmd_obj in cmd_obj.commands.items():
                cmd_data.subcommands[CommandName(subcmd_name)] = process_command(
                    CommandName(subcmd_name), subcmd_obj, parent=cmd_data
                )

        return cmd_data

    data: dict[CommandName, CommandSchema] = {}

    # Special case for the root group
    if isinstance(app, click.Group):
        root_cmd_name = CommandName("root")
        data[root_cmd_name] = process_command(root_cmd_name, app)
        app = data[root_cmd_name]

    if isinstance(app, click.Group):
        for cmd_name, cmd_obj in app.commands.items():
            data[CommandName(cmd_name)] = process_command(
                CommandName(cmd_name), cmd_obj
            )
    elif isinstance(app, click.Command):
        cmd_name = CommandName(app.name)
        data[cmd_name] = process_command(cmd_name, app)

    return data


CommandName = NewType("CommandName", str)

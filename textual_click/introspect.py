from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Sequence, NewType

import click


@dataclass
class OptionSchema:
    name: str
    type: str
    default: Any
    help: str | None
    choices: Sequence[str] | None = None


@dataclass
class ArgumentSchema:
    name: str
    type: str
    required: bool
    default: Any | None = None
    choices: Sequence[str] | None = None


@dataclass
class CommandSchema:
    name: CommandName
    docstring: str
    function: Callable[..., Any | None]
    options: list[OptionSchema] = field(default_factory=list)
    arguments: list[ArgumentSchema] = field(default_factory=list)
    subcommands: dict["CommandName", "CommandSchema"] = field(default_factory=dict)


def introspect_click_app(app: click.Group) -> dict[CommandName, CommandSchema]:
    """
    Introspect a Click application and build a data structure containing
    information about all commands, options, arguments, and subcommands,
    including the docstrings and command function references.

    This function recursively processes each command and its subcommands
    (if any), creating a nested dictionary that includes details about
    options, arguments, and subcommands, as well as the docstrings and
    command function references.

    Args:
        app (click.Group): The Click application's top-level group instance.

    Returns:
        Dict[str, CommandData]: A nested dictionary containing the Click application's
        structure. The structure is defined by the CommandData TypedDict and its related
        TypedDicts (OptionData and ArgumentData).
    """

    def process_command(cmd_name: CommandName, cmd_obj: click.Command) -> CommandSchema:
        cmd_data = CommandSchema(
            name=cmd_name,
            docstring=cmd_obj.help,
            function=cmd_obj.callback,
            options=[],
            arguments=[],
            subcommands={},
        )

        for param in cmd_obj.params:
            if isinstance(param, click.Option):
                option_data = OptionSchema(
                    name=param.name,
                    type=param.type.name,
                    default=param.default,
                    help=param.help,
                )
                cmd_data.options.append(option_data)
            elif isinstance(param, click.Argument):
                argument_data = ArgumentSchema(
                    name=param.name, type=param.type.name, required=param.required
                )
                if isinstance(param.type, click.Choice):
                    argument_data.choices = param.type.choices
                cmd_data.arguments.append(argument_data)

        if isinstance(cmd_obj, click.core.Group):
            for subcmd_name, subcmd_obj in cmd_obj.commands.items():
                cmd_data.subcommands[CommandName(subcmd_name)] = process_command(
                    CommandName(subcmd_name), subcmd_obj
                )

        return cmd_data

    data: dict[CommandName, CommandSchema] = {}
    for cmd_name, cmd_obj in app.commands.items():
        data[CommandName(cmd_name)] = process_command(CommandName(cmd_name), cmd_obj)

    return data


CommandName = NewType("CommandName", str)

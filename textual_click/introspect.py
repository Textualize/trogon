from __future__ import annotations

from typing import Any, TypedDict, Callable, Sequence

import click


class OptionData(TypedDict):
    name: str
    type: str
    default: Any
    help: str | None


class ArgumentData(TypedDict):
    name: str
    type: str
    required: bool
    choices: Sequence[str]


class CommandData(TypedDict):
    docstring: str | None
    function: Callable[..., Any | None]
    options: list[OptionData]
    arguments: list[ArgumentData]
    subcommands: dict[str, 'CommandData']


def introspect_click_app(app: click.Group) -> dict[str, CommandData]:
    """
        Introspect a Click application and build a data structure containing
        information about all commands, options, arguments, and subcommands.

        This function recursively processes each command and its subcommands
        (if any), creating a nested dictionary that includes details about
        options, arguments, and subcommands.

        Args:
            app (click.Group): The Click application's top-level group instance.

        Returns:
            dict[str, Any]: A nested dictionary containing the Click application's
            structure, including information about commands, options, arguments,
            and subcommands. The dictionary has the following structure:

            {
                'command_name': {
                    'options': [
                        {
                            'name': str,
                            'type': str,
                            'default': Any,
                            'help': Optional[str]
                        },
                        ...
                    ],
                    'arguments': [
                        {
                            'name': str,
                            'type': str,
                            'required': bool
                        },
                        ...
                    ],
                    'subcommands': {
                        'subcommand_name': { ... },
                        ...
                    }
                },
                ...
            }
        """

    def process_command(cmd_name: str, cmd_obj: click.Command) -> CommandData:
        cmd_data: CommandData = {
            'docstring': cmd_obj.help,
            'function': cmd_obj.callback,
            'options': [],
            'arguments': [],
            'subcommands': {}
        }

        for param in cmd_obj.params:
            if isinstance(param, click.Option):
                option_data: OptionData = {
                    'name': param.name,
                    'type': param.type.name,
                    'default': param.default,
                    'help': param.help
                }
                cmd_data['options'].append(option_data)
            elif isinstance(param, click.Argument):
                argument_data: ArgumentData = {
                    'name': param.name,
                    'type': param.type.name,
                    'required': param.required,
                    'choices': None
                }
                if isinstance(param.type, click.Choice):
                    argument_data['choices'] = param.type.choices
                cmd_data['arguments'].append(argument_data)

        if isinstance(cmd_obj, click.core.Group):
            for subcmd_name, subcmd_obj in cmd_obj.commands.items():
                cmd_data['subcommands'][subcmd_name] = process_command(subcmd_name, subcmd_obj)

        return cmd_data

    data: dict[str, CommandData] = {}
    for cmd_name, cmd_obj in app.commands.items():
        data[cmd_name] = process_command(cmd_name, cmd_obj)

    return data

from __future__ import annotations

import sys
from typing import Type
from collections import defaultdict


from trogon import Trogon

from trogon.constants import DEFAULT_COMMAND_NAME
from trogon.trogon import Trogon
from trogon.schemas import (
    ArgumentSchema,
    CommandName,
    CommandSchema,
    OptionSchema,
    ChoiceSchema,
)
from typing import Type, Any
from uuid import UUID
from datetime import datetime
import argparse


def introspect_argparse_parser(
    parser: argparse.ArgumentParser, cmd_ignorelist: list[str] | None = None
) -> dict[CommandName, CommandSchema]:
    """
    Introspect a argparse parser and build a data structure containing
    information about all commands, options, arguments, and subcommands,
    including the docstrings and command function references.

    This function recursively processes each command and its subcommands
    (if any), creating a nested dictionary that includes details about
    options, arguments, and subcommands, as well as the docstrings and
    command function references.

    Args:
        parser (argparse.ArgumentParser): The argparse parser instance.

    Returns:
        Dict[str, CommandData]: A nested dictionary containing the Click application's
        structure. The structure is defined by the CommandData TypedDict and its related
        TypedDicts (OptionData and ArgumentData).
    """

    def process_command(
        cmd_name: CommandName,
        parser: argparse.ArgumentParser,
        parent=None,
    ) -> CommandSchema:
        cmd_data = CommandSchema(
            name=cmd_name,
            docstring=parser.description,
            options=[],
            arguments=[],
            subcommands={},
            parent=parent,
        )

        # this is specific to yapx.
        param_types: dict[str, Type[Any]] | None = getattr(parser, "_dest_type", None)


        for param in parser._actions:
            if (
                isinstance(param, TuiAction)
                or argparse.SUPPRESS in [param.help, param.default]
            ):
                continue

            if isinstance(param, argparse._SubParsersAction):
                for subparser_name, subparser in param.choices.items():
                    if subparser.description != argparse.SUPPRESS and (
                        not cmd_ignorelist or subparser not in cmd_ignorelist
                    ):
                        cmd_data.subcommands[
                            CommandName(subparser_name)
                        ] = process_command(
                            CommandName(subparser_name),
                            subparser,
                            parent=cmd_data,
                        )
                continue

            param_type: Type[Any] | None = None
            if param_types:
                param_type = param_types.get(param.dest, param.type)

            if param_type is None and param.default is not None:
                param_type = type(param.default)

            is_counting: bool = False
            is_multiple: bool = False
            is_flag: bool = False

            opts: list[str] = param.option_strings
            secondary_opts: list[str] = []

            if isinstance(param, argparse._CountAction):
                is_counting = True
            elif isinstance(param, argparse._AppendAction):
                is_multiple = True
            elif isinstance(param, argparse._StoreConstAction):
                is_flag = True
            elif (sys.version_info >= (3, 9) and isinstance(
                param, argparse.BooleanOptionalAction
            )) or type(param).__name__ == 'BooleanOptionalAction':
                # check the type by name, because 'BooleanOptionalAction'
                # is often manually backported to Python versions < 3.9.
                if param_type is None:
                    param_type = bool
                is_flag = True
                secondary_prefix: str = "--no-"
                opts = [
                    x
                    for x in param.option_strings
                    if not x.startswith(secondary_prefix)
                ]
                secondary_opts = [
                    x
                    for x in param.option_strings
                    if x.startswith(secondary_prefix)
                ]

            # look for these "tags" in the help text: "secret", "prompt"
            # if present, set variables and remove from the help text.
            is_secret: bool = False
            is_prompt: bool = False
            param_help: str = param.help
            if param_help:
                param_help = param_help.replace('%(default)s', str(param.default))

                tag_prefix: str = "<"
                tag_suffix: str = ">"
                tag_start: int = param_help.find(tag_prefix)
                if tag_start >= 0:
                    tag_end: int = param_help.find(tag_suffix)
                    if tag_end > tag_start:
                        tag_txt: str = param_help[tag_start : tag_end + 1]
                        tags: list[str] = [
                            x.strip() for x in tag_txt[1:-1].split(",")
                        ]
                        is_secret = "secret" in tags
                        is_prompt = "prompt" in tags
                        if any([is_secret, is_prompt]):
                            param_help = param_help.replace(tag_txt, "")

            nargs: int = (
                1
                if param.nargs in [None, "?"]
                else -1
                if param.nargs in ["+", "*"]
                else int(param.nargs)
            )
            multi_value: bool = nargs < 0 or nargs > 1

            if param.option_strings:
                option_data = OptionSchema(
                    name=opts,
                    type=param_type,
                    is_flag=is_flag,
                    counting=is_counting,
                    secondary_opts=secondary_opts,
                    required=param.required,
                    default=param.default,
                    help=param_help,
                    choices=param.choices,
                    multiple=is_multiple,
                    multi_value=multi_value,
                    nargs=nargs,
                    secret=is_secret,
                    read_only=is_prompt,
                    placeholder="< You will be prompted. >"
                    if is_prompt
                    else "",
                )
                cmd_data.options.append(option_data)

            else:
                argument_data = ArgumentSchema(
                    name=param.dest,
                    type=param_type,
                    required=param.required,
                    default=param.default,
                    help=param_help,
                    choices=param.choices,
                    multiple=is_multiple,
                    multi_value=multi_value,
                    nargs=nargs,
                    secret=is_secret,
                    read_only=is_prompt,
                    placeholder="< You will be prompted. >"
                    if is_prompt
                    else "",
                )
                cmd_data.arguments.append(argument_data)

        return cmd_data

    data: dict[CommandName, CommandSchema] = {}

    root_cmd_name = CommandName("root")
    data[root_cmd_name] = process_command(root_cmd_name, parser)

    return data


class TuiAction(argparse.Action):
    def __init__(
        self,
        option_strings,
        dest=argparse.SUPPRESS,
        default=argparse.SUPPRESS,
        help="Open Textual TUI.",
        const: str = None,
        metavar: str = None,
        nargs: int | str | None = None,
        **_kwargs: Any,
    ):
        super(TuiAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs="?" if nargs is None else nargs,
            help=help,
            const=const,
            metavar=metavar
        )

    def __call__(self, parser, namespace, values, option_string=None):
        root_parser: argparse.ArgumentParser = getattr(namespace, '_parent_parser', parser)

        Trogon(
            introspect_argparse_parser(root_parser, cmd_ignorelist=[parser]),
            app_name=root_parser.prog,
            command_filter = values,
        ).run()

        parser.exit()


def add_tui_argument(
    parser: argparse.ArgumentParser,
    option_strings: str | list[str] = None,
    help: str = "Open Textual TUI.",
    default=argparse.SUPPRESS,
    **kwargs,
) -> None:
    if not option_strings:
        option_strings = [f"--{DEFAULT_COMMAND_NAME.replace('_', '-').lstrip('-')}"]
    elif isinstance(option_strings, str):
        option_strings = [option_strings]

    parser.add_argument(*option_strings, metavar='CMD', action=TuiAction, default=default, help=help, **kwargs)


def add_tui_command(
    parser: argparse.ArgumentParser,
    command: str = DEFAULT_COMMAND_NAME,
    help: str = "Open Textual TUI.",
) -> None:
    subparsers: argparse._SubParsersAction
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            subparsers = action
            break
    else:
        subparsers = parser.add_subparsers()

    tui_parser = subparsers.add_parser(command, description=argparse.SUPPRESS, help=help)
    tui_parser.set_defaults(_parent_parser=parser)

    add_tui_argument(tui_parser, option_strings=['cmd_filter'], default=None, help="Command filter")


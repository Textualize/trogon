from __future__ import annotations

import shlex
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, List, Optional

from textual_click.introspect import (
    CommandSchema,
    CommandName,
    OptionSchema,
    ArgumentSchema,
)


@dataclass
class UserOptionData:
    """
    A dataclass to store user input for a specific option.

    Attributes:
        name: The name of the option.
        value: The user-provided value for the option.
        option_schema: The schema corresponding to this option.
    """

    name: str | list[str]
    value: Any
    option_schema: OptionSchema

    @property
    def string_name(self) -> str:
        if isinstance(self.name, str):
            return self.name
        else:
            return self.name[0]


@dataclass
class UserArgumentData:
    """
    A dataclass to store user input for a specific argument.

    Attributes:
        name: The name of the argument.
        value: The user-provided value for the argument.
        argument_schema: The schema corresponding to this argument.
    """

    name: str
    value: Any
    argument_schema: ArgumentSchema


@dataclass
class UserCommandData:
    """
    A dataclass to store user input for a command, its options, and arguments.

    Attributes:
        name: The name of the command.
        options: A list of UserOptionData instances representing the user input for the command's options.
        arguments: A list of UserArgumentData instances representing the user input for the command's arguments.
        subcommand: An optional UserCommandData instance representing a subcommand of the current command.
            Since commands can be nested (i.e. subcommands), this may be processed recursively.
    """

    name: CommandName
    options: List[UserOptionData]
    arguments: List[UserArgumentData]
    subcommand: Optional["UserCommandData"] = None
    parent: Optional["UserCommandData"] = None
    command_schema: Optional["CommandSchema"] = None

    def to_cli_args(self) -> List[str]:
        """
        Generates a list of strings representing the CLI invocation based on the user input data.

        Returns:
            A list of strings that can be passed to subprocess.run to execute the command.
        """
        args = [self.name]

        multiples = defaultdict(list)
        multiples_schemas = {}
        for option in self.options:
            if option.option_schema.multiple:
                # We need to gather the items for the same option,
                #  compare them to the default, then display them all
                #  if they aren't equivalent to the default.
                multiples[option.string_name].append(option.value)
                multiples_schemas[option.string_name] = option.option_schema
            else:
                value = option.value
                default = option.option_schema.default
                is_default = value == str(default)

                if (
                    value is not None
                    and value is not False
                    and not is_default
                    and value != ""  # TODO: We need to support empty strings
                ):
                    if isinstance(option.name, str):
                        args.append(option.name)
                    else:
                        # Use the option with the longest name, since
                        # it's probably the most descriptive.
                        longest_name = max(option.name, key=len)
                        args.append(longest_name)

                    # Only add a value for non-boolean options
                    if value is not True:
                        args.append(str(value))

        for option_name, values in multiples.items():
            # Check if the values given for this option differ from the default
            defaults = multiples_schemas[option_name].default or []
            if list(sorted(map(str, values))) != list(sorted(map(str, defaults))):
                for value in values:
                    args.append(option_name)
                    args.append(str(value))

        for argument in self.arguments:
            if argument.value != "":
                args.append(str(argument.value))

        if self.subcommand:
            args.extend(self.subcommand.to_cli_args())

        return args

    def to_cli_string(self, include_root_command: bool = False) -> str:
        """
        Generates a string representing the CLI invocation as if typed directly into the command line.

        Returns:
            A string representing the command invocation.
        """
        args = self.to_cli_args()
        if not include_root_command:
            args = args[1:]
        return " ".join(shlex.quote(arg) for arg in args)

    def fill_defaults(self, command_schema: CommandSchema) -> None:
        """
        Prefills the UserCommandData instance with default values for options and arguments based on the provided
        CommandSchema.

        Args:
            command_schema: A CommandSchema instance representing the schema for the command to prefill defaults.
        """
        # Prefill default option values
        for option_schema in command_schema.options:
            if option_schema.default is not None and not any(
                opt.name == option_schema.name for opt in self.options
            ):
                if option_schema.multiple:
                    for default in option_schema.default:
                        self.options.append(
                            UserOptionData(
                                name=option_schema.name,
                                value=default,
                                option_schema=option_schema,
                            )
                        )
                else:
                    self.options.append(
                        UserOptionData(
                            name=option_schema.name,
                            value=option_schema.default,
                            option_schema=option_schema,
                        )
                    )

        # Prefill default argument values
        for arg_schema in command_schema.arguments:
            if arg_schema.default is not None and not any(
                arg.name == arg_schema.name for arg in self.arguments
            ):
                self.arguments.append(
                    UserArgumentData(
                        name=arg_schema.name,
                        value=arg_schema.default,
                        argument_schema=arg_schema,
                    )
                )

        # Prefill defaults for subcommand if present
        if self.subcommand:
            subcommand_schema = next(
                (
                    cmd
                    for cmd in command_schema.subcommands.values()
                    if cmd.name == self.subcommand.name
                ),
                None,
            )
            if subcommand_schema:
                self.subcommand.fill_defaults(subcommand_schema)

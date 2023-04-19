from __future__ import annotations

import shlex
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from textual_click.introspect import CommandSchema, CommandName


@dataclass
class UserOptionData:
    """
    A dataclass to store user input for a specific option.

    Attributes:
        name: The name of the option.
        value: The user-provided value for the option.
    """

    name: str
    value: Any


@dataclass
class UserArgumentData:
    """
    A dataclass to store user input for a specific argument.

    Attributes:
        name: The name of the argument.
        value: The user-provided value for the argument.
    """

    name: str
    value: Any


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

    name: str
    options: List[UserOptionData]
    arguments: List[UserArgumentData]
    subcommand: Optional["UserCommandData"] = None

    def to_cli_args(self) -> List[str]:
        """
        Generates a list of strings representing the CLI invocation based on the user input data.

        Returns:
            A list of strings that can be passed to subprocess.run to execute the command.
        """
        args = [self.name]

        for option in self.options:
            args.append(f"--{option.name}")
            args.append(str(option.value))

        for argument in self.arguments:
            args.append(str(argument.value))

        if self.subcommand:
            args.extend(self.subcommand.to_cli_args())

        return args

    def to_cli_string(self) -> str:
        """
        Generates a string representing the CLI invocation as if typed directly into the command line.

        Returns:
            A string representing the command invocation.
        """
        args = self.to_cli_args()
        return shlex.join(args)


def validate_user_command_data(
    introspection_data: Dict[CommandName, CommandSchema],
    user_command_data: UserCommandData,
) -> None:
    """
    Validates the user input against the provided command schema.

    Args:
        introspection_data: A dictionary mapping command names to CommandSchema instances representing the schema
            for the introspected CLI commands, options, and arguments.
        user_command_data: A UserCommandData instance representing the user input for the command to validate,
            its options, arguments, and any subcommands.

    Raises:
        ValueError: If the user input does not conform to the command schema, such as an unknown command, missing
            required argument, or invalid option value.
    """
    command_schema = introspection_data.get(CommandName(user_command_data.name))
    if not command_schema:
        raise ValueError(f"Unknown command: {user_command_data.name}")

    # Validate options
    for user_option_data in user_command_data.options:
        option_schema = next(
            (
                opt
                for opt in command_schema.options
                if opt.name == user_option_data.name
            ),
            None,
        )
        if not option_schema:
            raise ValueError(f"Unknown option: --{user_option_data.name}")
        if (
            option_schema.choices
            and user_option_data.value not in option_schema.choices
        ):
            raise ValueError(
                f"Invalid value for option --{user_option_data.name}. "
                f"Allowed values: {', '.join(map(str, option_schema.choices))}."
            )

    # Validate arguments
    if len(user_command_data.arguments) != len(command_schema.arguments):
        raise ValueError(
            f"Invalid number of arguments for command {user_command_data.name}"
        )
    for user_arg_data, arg_schema in zip(
        user_command_data.arguments, command_schema.arguments
    ):
        if not isinstance(user_arg_data.value, arg_schema.type):
            raise ValueError(
                f"Invalid type for argument {user_arg_data.name}. "
                f"Expected {arg_schema.type.__name__}, but got {type(user_arg_data.value).__name__}."
            )

    # Validate subcommand
    if user_command_data.subcommand:
        validate_user_command_data(introspection_data, user_command_data.subcommand)

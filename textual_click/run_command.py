from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from textual_click.introspect import CommandSchema, CommandName

CLICK_TYPE_TO_PYTHON_TYPE = {
    "text": str,
    "int": int,
    "float": float,
    "boolean": bool,
    "uuid": (str, UUID),  # UUID type can be a string or uuid.UUID instance
    "Path": Path,
}


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
        return ' '.join(shlex.quote(arg) for arg in args)

    def prefill_defaults(self, command_schema: CommandSchema) -> None:
        """
        Prefills the UserCommandData instance with default values for options and arguments based on the provided
        CommandSchema.

        Args:
            command_schema: A CommandSchema instance representing the schema for the command to prefill defaults.
        """
        # Prefill default option values
        for option_schema in command_schema.options:
            if (
                option_schema.default is not None
                and not any(opt.name == option_schema.name for opt in self.options)
            ):
                self.options.append(UserOptionData(name=option_schema.name, value=option_schema.default))

        # Prefill default argument values
        for arg_schema in command_schema.arguments:
            if (
                arg_schema.default is not None
                and not any(arg.name == arg_schema.name for arg in self.arguments)
            ):
                self.arguments.append(UserArgumentData(name=arg_schema.name, value=arg_schema.default))

        # Prefill defaults for subcommand if present
        if self.subcommand:
            subcommand_schema = next(
                (cmd for cmd in command_schema.subcommands.values() if cmd.name == self.subcommand.name),
                None,
            )
            if subcommand_schema:
                self.subcommand.prefill_defaults(subcommand_schema)

    def copy_with(
        self,
        name: Optional[str] = None,
        options: Optional[List[UserOptionData]] = None,
        arguments: Optional[List[UserArgumentData]] = None,
        subcommand: Optional['UserCommandData'] = None,
    ) -> 'UserCommandData':
        """
        Creates a new instance of UserCommandData with the given values, falling back to the original values if
        not provided.

        Args:
            name: The name of the command.
            options: A list of UserOptionData instances representing the options for the command.
            arguments: A list of UserArgumentData instances representing the arguments for the command.
            subcommand: A UserCommandData instance representing the subcommand for the command, if any.

        Returns:
            A new UserCommandData instance with the updated values.
        """
        return UserCommandData(
            name=name or self.name,
            options=options or self.options,
            arguments=arguments or self.arguments,
            subcommand=subcommand or self.subcommand,
        )

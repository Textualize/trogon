from __future__ import annotations

import itertools
import shlex
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, List, Optional

from rich.text import Text

from trogon.introspect import (
    CommandSchema,
    CommandName,
    OptionSchema,
    ArgumentSchema,
    MultiValueParamData,
)
from trogon.widgets.parameter_controls import ValueNotSupplied


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
    value: tuple[Any]  # Multi-value options will be tuple length > 1
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
    value: tuple[Any]
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
    options: list[UserOptionData] = field(default_factory=list)
    arguments: list[UserArgumentData] = field(default_factory=list)
    subcommand: UserCommandData | None = None
    parent: UserCommandData | None = None
    command_schema: CommandSchema | None = None

    def to_cli_args(self, include_root_command: bool = False) -> list[str]:
        """
        Generates a list of strings representing the CLI invocation based on the user input data.

        Returns:
            A list of strings that can be passed to subprocess.run to execute the command.
        """
        cli_args = self._to_cli_args()
        if not include_root_command:
            cli_args = cli_args[1:]

        return cli_args

    def _to_cli_args(self) -> list[str]:
        args: list[str] = [self.name]

        multiples: dict[str, list[tuple[str]]] = defaultdict(list)
        multiples_schemas: dict[str, OptionSchema] = {}

        for option in self.options:
            if option.option_schema.multiple:
                # We need to gather the items for the same option,
                #  compare them to the default, then display them all
                #  if they aren't equivalent to the default.
                multiples[option.string_name].append(option.value)
                multiples_schemas[option.string_name] = option.option_schema
            else:
                value_data: list[tuple[Any]] = MultiValueParamData.process_cli_option(
                    option.value
                ).values

                if option.option_schema.default is not None:
                    default_data: list[tuple[Any]] = option.option_schema.default.values
                else:
                    default_data = [tuple()]

                flattened_values = sorted(itertools.chain.from_iterable(value_data))
                flattened_defaults = sorted(itertools.chain.from_iterable(default_data))

                # If the user has supplied values (any values are not None), then
                # we don't display the value.
                values_supplied = any(
                    value != ValueNotSupplied() for value in flattened_values
                )
                values_are_defaults = list(map(str, flattened_values)) == list(
                    map(str, flattened_defaults)
                )

                # If the user has supplied values, and they're not the default values,
                # then we want to display them in the command string...
                if values_supplied and not values_are_defaults:
                    if isinstance(option.name, str):
                        option_name = option.name
                    else:
                        if option.option_schema.counting:
                            # For count options, we use the shortest name, e.g. use
                            # -v instead of --verbose.
                            option_name = min(option.name, key=len)
                        else:
                            # Use the option with the longest name, since
                            # it's probably the most descriptive (use --verbose over -v)
                            option_name = max(option.name, key=len)

                    is_true_bool = value_data == [(True,)]

                    is_flag = option.option_schema.is_flag
                    secondary_opts = option.option_schema.secondary_opts

                    if is_flag:
                        # If the option is specified like `--thing/--not-thing`,
                        # then secondary_opts will contain `--not-thing`, and if the
                        # value is False, we should use that.
                        if is_true_bool:
                            args.append(option_name)
                        else:
                            if secondary_opts:
                                longest_secondary_name = max(secondary_opts, key=len)
                                args.append(longest_secondary_name)
                    else:
                        if not option.option_schema.counting:
                            # Although buried away a little, this branch here is
                            # actually the nominal case... single value options e.g.
                            # `--foo bar`.
                            args.append(option_name)
                            for subvalue_tuple in value_data:
                                args.extend(subvalue_tuple)
                        else:
                            # Get the value of the counting option
                            count = next(itertools.chain.from_iterable(value_data), 1)
                            try:
                                count = int(count)
                            except ValueError:
                                # TODO: Not sure if this is the right thing to do
                                count = 1
                            count = max(1, min(count, 5))
                            if option_name.startswith("--"):
                                args.extend([option_name] * count)
                            else:
                                clean_option_name = option_name.lstrip("-")
                                args.append(f"-{clean_option_name * count}")

        for option_name, values in multiples.items():
            # Check if the values given for this option differ from the default
            defaults = multiples_schemas[option_name].default or []
            default_values = list(itertools.chain.from_iterable(defaults.values))
            supplied_defaults = [
                value for value in default_values if value != ValueNotSupplied()
            ]
            supplied_defaults = list(map(str, supplied_defaults))
            supplied_defaults = sorted(supplied_defaults)

            supplied_values = list(itertools.chain.from_iterable(values))
            supplied_values = [
                value for value in supplied_values if value != ValueNotSupplied()
            ]
            supplied_values = list(map(str, supplied_values))
            supplied_values = sorted(supplied_values)

            values_are_defaults = supplied_values == supplied_defaults
            values_supplied = any(
                value != ValueNotSupplied() for value in supplied_values
            )

            # If the user has supplied any non-default values, include them...
            if values_supplied and not values_are_defaults:
                for value_data in values:
                    if not all(value == ValueNotSupplied() for value in value_data):
                        args.append(option_name)
                        args.extend(v for v in value_data)

        for argument in self.arguments:
            this_arg_values = argument.value
            for argument_value in this_arg_values:
                if argument_value != ValueNotSupplied():
                    args.append(argument_value)

        if self.subcommand:
            args.extend(self.subcommand._to_cli_args())

        return args

    def to_cli_string(self, include_root_command: bool = False) -> Text:
        """
        Generates a string representing the CLI invocation as if typed directly into the
        command line.

        Returns:
            A string representing the command invocation.
        """
        args = self.to_cli_args(include_root_command=include_root_command)

        text_renderables: list[Text] = []
        for arg in args:
            text_renderables.append(
                Text(shlex.quote(str(arg)))
                if arg != ValueNotSupplied()
                else Text("???", style="bold black on red")
            )
        return Text(" ").join(text_renderables)

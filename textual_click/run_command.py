from __future__ import annotations

from typing import Any, List, Dict, Optional

from textual_click.introspect import CommandSchema, CommandName


def validate_and_run_command(
    introspection_data: dict[CommandName, CommandSchema],
    command_path: list[str],
    options_and_arguments: dict[str, Any]
) -> None:
    """
    Validate and run a user command based on the provided introspection data.

    This function checks if the given command, options, and arguments are valid
    according to the introspection data, and if so, runs the corresponding command
    function with the validated options and arguments.

    The command_path parameter should be a list of command and subcommand names,
    representing the command hierarchy. The options_and_arguments parameter should
    be a dictionary where the keys are option or argument names, and the values are
    the provided user input for those options or arguments.

    If any validation errors are encountered, such as unknown commands, invalid option
    values, or missing required arguments, an error message is printed, and the command
    function is not executed.

    Args:
        introspection_data: A dictionary containing the introspection
            data for a Click application, as returned by the introspect_click_app function.
        command_path: A list of command and subcommand names, representing the
            command hierarchy to be executed.
        options_and_arguments: A dictionary containing the user-provided
            options and arguments for the command. Keys are the option or argument names,
            and values are the corresponding user input.
    """

    def find_command_data(cmd_path: List[str], cmd_data: Dict[str, CommandSchema]) -> Optional[CommandSchema]:
        if not cmd_path or not cmd_data:
            return None

        cmd_name = cmd_path[0]
        if cmd_name in cmd_data:
            if len(cmd_path) == 1:
                return cmd_data[cmd_name]
            else:
                return find_command_data(cmd_path[1:], cmd_data[cmd_name].subcommands)

        return None

    command_data = find_command_data(command_path, introspection_data)

    if not command_data:
        print(f"Command {' '.join(command_path)} not found.")
        return

    options = {option.name: option for option in command_data.options}
    arguments = {argument.name: argument for argument in command_data.arguments}

    for key, value in options_and_arguments.items():
        if key in options:
            option_data = options[key]
            try:
                value = option_data.type(value)
            except ValueError:
                print(f"Invalid value '{value}' for option '{key}'. Expected type '{option_data.type}'.")
                return
        elif key in arguments:
            argument_data = arguments[key]
            if argument_data.choices and value not in argument_data.choices:
                print(f"Invalid value '{value}' for argument '{key}'. Must be one of {argument_data.choices}.")
                return
            try:
                value = argument_data.type(value)
            except ValueError:
                print(f"Invalid value '{value}' for argument '{key}'. Expected type '{argument_data.type}'.")
                return
        else:
            print(f"Unknown option or argument: {key}")
            return

    # Run the command with the validated options and arguments
    command_data.function(**options_and_arguments)

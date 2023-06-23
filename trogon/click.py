from __future__ import annotations
from typing import Sequence


from trogon import Trogon

try:
    import click
    from click import BaseCommand
except ImportError as e:
    raise ImportError(
        "The extra `trogon[click]` is required to enable tui generation from Typer apps."
    ) from e

from trogon.constants import DEFAULT_COMMAND_NAME
from trogon.trogon import Trogon
from trogon.schemas import (
    ArgumentSchema,
    CommandName,
    CommandSchema,
    OptionSchema,
)
from typing import Type, Any
from uuid import UUID
from datetime import datetime
from pathlib import Path

CLICK_TO_PY_TYPES: dict[click.ParamType, Type[Any]] = {
    click.types.StringParamType: str,
    click.types.IntParamType: int,
    click.types.FloatParamType: float,
    click.types.BoolParamType: bool,
    click.types.UUIDParameterType: UUID,
    click.IntRange: int,
    click.FloatRange: float,
    click.DateTime: datetime,
    click.Path: Path,
}


def introspect_click_app(
    app: BaseCommand, cmd_ignorelist: list[str] | None = None
) -> dict[CommandName, CommandSchema]:
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
        cmd_name: CommandName,
        cmd_obj: click.Command,
        parent=None,
    ) -> CommandSchema:
        cmd_data = CommandSchema(
            name=cmd_name,
            docstring=cmd_obj.help,
            options=[],
            arguments=[],
            subcommands={},
            parent=parent,
        )
        for param in cmd_obj.params:
            param_type: Type[Any] = CLICK_TO_PY_TYPES.get(
                param.type, CLICK_TO_PY_TYPES.get(type(param.type), str)
            )
            param_choices: Sequence[str] | None = None
            if isinstance(param.type, click.Choice):
                param_choices = param.type.choices

            if isinstance(param, (click.Option, click.core.Group)):
                if param.hidden:
                    continue

                prompt_required: bool = param.prompt and param.prompt_required

                option_data = OptionSchema(
                    name=param.opts,
                    type=param_type,
                    is_flag=param.is_flag,
                    counting=param.count,
                    secondary_opts=param.secondary_opts,
                    required=param.required,
                    default=param.default,
                    help=param.help,
                    choices=param_choices,
                    multiple=param.multiple,
                    nargs=param.nargs,
                    sensitive=param.hide_input,
                    read_only=prompt_required,
                    placeholder="< You will be prompted. >" if prompt_required else "",
                )
                cmd_data.options.append(option_data)

            elif isinstance(param, click.Argument):
                argument_data = ArgumentSchema(
                    name=param.name,
                    type=param_type,
                    required=param.required,
                    choices=param_choices,
                    multiple=param.multiple,
                    default=param.default,
                    nargs=param.nargs,
                )
                cmd_data.arguments.append(argument_data)

        if isinstance(cmd_obj, click.core.Group):
            for subcmd_name, subcmd_obj in cmd_obj.commands.items():
                if not subcmd_obj.hidden and subcmd_name not in cmd_ignorelist:
                    cmd_data.subcommands[CommandName(subcmd_name)] = process_command(
                        CommandName(subcmd_name),
                        subcmd_obj,
                        parent=cmd_data,
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
                CommandName(cmd_name),
                cmd_obj,
            )
    elif isinstance(app, click.Command):
        cmd_name = CommandName(app.name)
        data[cmd_name] = process_command(cmd_name, app)

    return data


def tui(
    name: str | None = None,
    command: str = DEFAULT_COMMAND_NAME,
    help: str = "Open Textual TUI.",
):
    def decorator(app: click.Group | click.Command):
        @click.pass_context
        def wrapped_tui(ctx, *args, **kwargs):
            Trogon(
                introspect_click_app(app, cmd_ignorelist=[command]), app_name=name
            ).run()

        if isinstance(app, click.Group):
            app.command(name=command, help=help)(wrapped_tui)
        else:
            new_group = click.Group()
            new_group.add_command(app)
            new_group.command(name=command, help=help)(wrapped_tui)
            return new_group

        return app

    return decorator

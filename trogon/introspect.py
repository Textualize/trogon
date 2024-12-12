from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence, NewType

import click
from click import BaseCommand, ParamType


CommandName = NewType("CommandName", str)


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


class CommandSchema(ABC):

    def __init__(self, name: CommandName, parent: "CommandSchema | None" = None):
        self.name = name
        self.parent = parent
        self.key = generate_unique_id()

    @property
    @abstractmethod
    def options(self) -> list[OptionSchema]:
        pass

    @property
    @abstractmethod
    def arguments(self) -> list[ArgumentSchema]:
        pass
    
    @property
    @abstractmethod
    def subcommands(self) -> dict["CommandName", "CommandSchema"]:
        pass
    
    @property
    @abstractmethod
    def docstring(self) -> str | None:
        pass

    @property
    @abstractmethod
    def function(self) -> Callable[..., Any | None]:
        pass

    @property
    @abstractmethod
    def is_group(self) -> bool:
        pass

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


class ClickCommandSchema(CommandSchema):

    def __init__(
        self,
        cmd_obj: click.Command,
        cmd_ctx: click.Context,
        cmd_name: CommandName | None = None,
        parent: CommandSchema | None = None,
    ):
        super().__init__(cmd_name or cmd_obj.name, parent)
        self.cmd_obj = cmd_obj
        self.cmd_ctx = cmd_ctx
        self._options = None
        self._arguments = None
        self._subcommands = None
        self._docstring = None

    @property
    def options(self) -> list[OptionSchema]:
        if self._options is None:
            self._options = list[OptionSchema]()
            for param in self.cmd_obj.get_params(self.cmd_ctx):
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
                    self._options.append(option_data)
        return self._options

    @property
    def arguments(self) -> list[ArgumentSchema]:
        if self._arguments is None:
            self._arguments = list[ArgumentSchema]()
            for param in self.cmd_obj.get_params(self.cmd_ctx):
                default = MultiValueParamData.process_cli_option(param.default)
                if isinstance(param, click.Argument):
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
                    self._arguments.append(argument_data)
        return self._arguments
    
    @property
    def subcommands(self) -> dict["CommandName", "CommandSchema"]:
        if self._subcommands is None:
            self._subcommands = dict["CommandName", "CommandSchema"]()
            if isinstance(self.cmd_obj, click.core.Group):
                self.cmd_obj.to_info_dict(self.cmd_ctx)
                for subcmd_name, subcmd_obj in self.cmd_obj.commands.items():
                    self._subcommands[CommandName(subcmd_name)] = ClickCommandSchema(
                        cmd_obj=subcmd_obj,
                        cmd_ctx=self.cmd_ctx,
                        cmd_name=subcmd_name,
                        parent=self,
                    )
        return self._subcommands

    @property
    def docstring(self) -> str | None:
        if self._docstring is None:
            self._docstring = self.cmd_obj.get_help(self.cmd_ctx)
        return self._docstring

    @property
    def function(self) -> Callable[..., Any | None]:
        return self.cmd_obj.callback
    
    @property
    def is_group(self) -> bool:
        return isinstance(self.cmd_obj, click.Group)


def introspect_click_app(app: BaseCommand, click_context: click.Context) -> dict[CommandName, CommandSchema]:
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

    data: dict[CommandName, CommandSchema] = {}

    # Special case for the root group
    if isinstance(app, click.Group):
        root_cmd_name = CommandName("root")
        data[root_cmd_name] = ClickCommandSchema(app, click_context, cmd_name=root_cmd_name)
        app = data[root_cmd_name]

    if isinstance(app, click.Group):
        for cmd_name, cmd_obj in app.commands.items():
            data[CommandName(cmd_name)] = ClickCommandSchema(cmd_obj, click_context, cmd_name=CommandName(cmd_name))

    elif isinstance(app, click.Command):
        cmd_name = CommandName(app.name)
        data[cmd_name] = ClickCommandSchema(cmd_obj, click_context, cmd_name=cmd_name)

    return data

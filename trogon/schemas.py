from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence, NewType, Type



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
class ArgumentSchema:
    name: str | list[str]
    type: Type[Any] | None = None
    required: bool = False
    help: str | None = None
    key: str | tuple[str] = field(default_factory=generate_unique_id)
    default: MultiValueParamData | Any | None = None
    choices: Sequence[str] | None = None
    multiple: bool = False
    multi_value: bool = False
    nargs: int = 1

    def __post_init__(self):
        if not isinstance(self.default, MultiValueParamData):
            self.default = MultiValueParamData.process_cli_option(self.default)

        if not self.type:
            self.type = str

        if self.multi_value:
            self.multiple = True

        if self.choices:
            self.choices = [str(x) for x in self.choices]


@dataclass
class OptionSchema(ArgumentSchema):
    is_flag: bool = False
    counting: bool = False
    secondary_opts: list[str] | None = None


@dataclass
class CommandSchema:
    name: CommandName
    docstring: str | None = None
    key: str = field(default_factory=generate_unique_id)
    options: list[OptionSchema] = field(default_factory=list)
    arguments: list[ArgumentSchema] = field(default_factory=list)
    subcommands: dict["CommandName", "CommandSchema"] = field(default_factory=dict)
    parent: "CommandSchema | None" = None

    @property
    def path_from_root(self) -> list["CommandSchema"]:
        node = self
        path = [self]
        while True:
            node = node.parent
            if node is None:
                break
            path.append(node)
        return list(reversed(path))


CommandName = NewType("CommandName", str)

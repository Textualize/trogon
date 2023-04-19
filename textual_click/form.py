from __future__ import annotations

import dataclasses
import uuid
from typing import Sequence, NamedTuple

from rich.text import Text
from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label, Input, Checkbox, RadioSet, RadioButton

from textual_click.introspect import CommandSchema, CommandName, ArgumentSchema, OptionSchema
from textual_click.run_command import UserCommandData


def generate_unique_id():
    return str(uuid.uuid4())[:8]


@dataclasses.dataclass
class FormControlMeta:
    widget: Widget
    meta: OptionSchema | ArgumentSchema


class CommandForm(Widget):
    DEFAULT_CSS = """
    .command-form-heading {
        padding: 1 0 0 2;
        text-style: bold;
    }
    .command-form-label {
        padding: 1 0 0 2;
    }
    .command-form-radioset {
        margin: 0 2;
    }
    .command-form-checkbox {
        padding: 1 2;
    }
    """

    class FormChanged(Message):
        def __init__(self, command_data: UserCommandData):
            super().__init__()
            self.command_data = command_data
            """The new data taken from the form to be converted into a CLI invocation."""

    def __init__(
        self,
        command_schema: CommandSchema | None = None,
        command_schemas: dict[CommandName, CommandSchema] | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.command_schema = command_schema
        self.command_schemas = command_schemas
        self.id_widget_map: dict[str,] = {}

    def compose(self) -> ComposeResult:
        options = self.command_schema.options
        arguments = self.command_schema.arguments

        # TODO
        #  We should generate a unique ID for each form widget and store that in a mapping,
        #  alongside the corresponding schema. Then when an event arrives, we can lookup the
        #  ID in the mapping to retrieve the schema to go alongside the new value. Using this
        #  data, we can construct a UserCommandData and post it up the DOM.

        if options:
            yield Label("Options", classes="command-form-heading")
            yield from self._make_command_form(options)

        if arguments:
            yield Label("Arguments", classes="command-form-heading")
            yield from self._make_command_form(arguments)

        if not options and not arguments:
            # TODO - improve this...
            yield Label(
                "Choose a command from the sidebar", classes="command-form-label"
            )

    def on_input_changed(self, event: Input.Changed) -> None:
        pass

    def form_changed(self) -> UserCommandData:
        """Take the current state of the form and build a UserCommandData from it,
        then post a FormChanged message"""

    def _make_command_form(self, arguments: Sequence[ArgumentSchema | OptionSchema]):
        for argument in arguments:
            name = argument.name
            argument_type = argument.type
            default = argument.default
            help = argument.help if isinstance(argument, OptionSchema) else ""
            label = self._make_command_form_control_label(name, argument_type)
            if argument_type in {"text", "float", "integer", "Path"}:
                yield Label(label, classes="command-form-label")
                yield Input(
                    value=str(default) if default is not None else "",
                    placeholder=help if help else label.plain,
                )
            elif argument_type in {"boolean"}:
                yield Checkbox(
                    f"{name} ({argument_type})",
                    button_first=False,
                    value=default,
                    classes="command-form-checkbox",
                )
            elif argument_type in {"choice"}:
                yield Label(label, classes="command-form-label")
                with RadioSet(classes="command-form-radioset"):
                    for choice in argument.choices:
                        yield RadioButton(choice)

    # def _build_command_data(self) -> UserCommandData:
    #     """Takes the current state of this form and converts it into a UserCommandData,
    #     ready to be executed."""

    # def _validate_command_data(self) -> None:
    #     validate_user_command_data(self.command_schemas, self.)

    @staticmethod
    def _make_command_form_control_label(name: str, type: str) -> Text:
        return Text.from_markup(f"{name} [dim]{type}[/]")

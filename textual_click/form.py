from __future__ import annotations

import dataclasses
import uuid
from typing import Sequence, Any

from rich.text import Text
from textual import log
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label, Input, Checkbox, RadioSet, RadioButton

from textual_click.introspect import CommandSchema, CommandName, ArgumentSchema, OptionSchema
from textual_click.run_command import UserCommandData, UserOptionData, UserArgumentData


def generate_unique_id():
    return f"id_{str(uuid.uuid4())[:8]}"


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

    class Changed(Message):
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
        self.id_to_metadata: dict[str, ArgumentSchema | OptionSchema] = {}

    def compose(self) -> ComposeResult:
        path_from_root = iter(self.command_schema.path_from_root)
        command_node = next(path_from_root)
        with VerticalScroll():
            while command_node is not None:
                options = command_node.options
                arguments = command_node.arguments
                if options:
                    yield Label("Options", classes="command-form-heading")
                    yield from self._make_command_form(options)

                if arguments:
                    yield Label("Arguments", classes="command-form-heading")
                    yield from self._make_command_form(arguments)

                command_node = next(path_from_root, None)

        # if not options and not arguments:
        #     # TODO - improve this...
        #     yield Label(
        #         "Choose a command from the sidebar", classes="command-form-label"
        #     )

    def on_input_changed(self) -> None:
        self._form_changed()

    def on_radio_set_changed(self) -> None:
        self._form_changed()

    def on_checkbox_changed(self) -> None:
        self._form_changed()

    def _form_changed(self) -> UserCommandData:
        """Take the current state of the form and build a UserCommandData from it,
        then post a FormChanged message"""

        # For each control in the form, pull out the value, look up the metadata, and add
        #  it to the UserCommandData
        command_data = UserCommandData(
            name=self.command_schema.name,
            options=[],
            arguments=[],
        )

        for id, schema in self.id_to_metadata.items():
            widget = self.query_one(f"#{id}")
            value = self._get_form_control_value(widget)
            # If we're dealing with an option
            if isinstance(schema, OptionSchema):
                option_data = UserOptionData(schema.name, value)
                command_data.options.append(option_data)
            elif isinstance(schema, ArgumentSchema):
                argument_data = UserArgumentData(schema.name, value)
                command_data.arguments.append(argument_data)

        command_data.fill_defaults(self.command_schema)
        self.post_message(self.Changed(command_data))
        log(command_data)

    @staticmethod
    def _get_form_control_value(control: Input | RadioSet | Checkbox) -> Any:
        if isinstance(control, (Input, Checkbox)):
            return control.value
        elif isinstance(control, RadioSet):
            return control.pressed_button.label.plain

    def _make_command_form(self, schemas: Sequence[ArgumentSchema | OptionSchema]):
        for schema in schemas:
            control_id = generate_unique_id()
            self.id_to_metadata[control_id] = schema

            name = schema.name
            argument_type = schema.type
            default = schema.default
            help = schema.help if isinstance(schema, OptionSchema) else ""
            label = self._make_command_form_control_label(name, argument_type)
            if argument_type in {"text", "float", "integer", "Path"}:
                yield Label(label, classes="command-form-label")
                yield Input(
                    value=str(default) if default is not None else "",
                    placeholder=help if help else label.plain,
                    id=control_id,
                )
            elif argument_type in {"boolean"}:
                yield Checkbox(
                    f"{name} ({argument_type})",
                    button_first=False,
                    value=default,
                    classes="command-form-checkbox",
                    id=control_id,
                )
            elif argument_type in {"choice"}:
                yield Label(label, classes="command-form-label")
                with RadioSet(id=control_id, classes="command-form-radioset"):
                    for choice in schema.choices:
                        yield RadioButton(choice)

    # def _build_command_data(self) -> UserCommandData:
    #     """Takes the current state of this form and converts it into a UserCommandData,
    #     ready to be executed."""

    # def _validate_command_data(self) -> None:
    #     validate_user_command_data(self.command_schemas, self.)

    @staticmethod
    def _make_command_form_control_label(name: str, type: str) -> Text:
        return Text.from_markup(f"{name} [dim]{type}[/]")

from __future__ import annotations

import dataclasses
from typing import Sequence, Any

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label, Input, Checkbox, RadioSet, RadioButton, Static

from textual_click.introspect import (
    CommandSchema,
    CommandName,
    ArgumentSchema,
    OptionSchema,
)
from textual_click.run_command import UserCommandData, UserOptionData, UserArgumentData
from textual_click.widgets.multiple_choice import MultipleChoice
from textual_click.widgets.multiple_input import MultipleInput


@dataclasses.dataclass
class FormControlMeta:
    widget: Widget
    meta: OptionSchema | ArgumentSchema


class CommandForm(Widget):
    """Form which is constructed from an introspected Click app. Users
    make use of this form in order to construct CLI invocation strings."""

    DEFAULT_CSS = """
    .command-form-heading {
        padding: 1 0 0 2;
        text-style: u;
        color: $text 70%;
    }
    .command-form-input {
        margin: 0 1 0 1;
    }
    .command-form-label {
        padding: 1 0 0 2;
    }
    .command-form-radioset {
        margin: 0 0 0 2;
    }
    .command-form-multiple-choice {
        margin: 0 0 0 2;
    }
    .command-form-checkbox {
        padding: 1 0 0 2;
    }
    .command-form-command-group {
        margin: 1 2;
        height: auto;
        background: $boost;
        border: panel $primary 60%;
        border-title-color: $text 80%;
        border-title-style: bold;
        border-subtitle-color: $text 30%;
        padding-bottom: 1;
    }
    .command-form-control-help-text {
        margin: 0 0 0 2;
        height: auto;
        color: $text 40%;
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
        self.schema_key_to_metadata: dict[str, ArgumentSchema | OptionSchema] = {}
        self.first_control: Widget | None = None

    def compose(self) -> ComposeResult:
        path_from_root = iter(self.command_schema.path_from_root)
        command_node = next(path_from_root)
        with VerticalScroll() as vs:
            vs.can_focus = False
            while command_node is not None:
                options = command_node.options
                arguments = command_node.arguments
                if options or arguments:
                    with Vertical(classes="command-form-command-group") as v:
                        is_inherited = command_node is not self.command_schema
                        v.border_title = (
                            f"{'↪ ' if is_inherited else ''}{command_node.name}"
                        )
                        v.border_subtitle = f"{'(parameters inherited from parent)' if is_inherited else ''}"
                        if arguments:
                            yield Label(f"Arguments", classes="command-form-heading")
                            yield from self._make_command_form(arguments)

                        if options:
                            yield Label(f"Options", classes="command-form-heading")
                            yield from self._make_command_form(options, is_option=True)

                command_node = next(path_from_root, None)

    def on_mount(self) -> None:
        self._form_changed()

    def on_input_changed(self) -> None:
        self._form_changed()

    def on_radio_set_changed(self) -> None:
        self._form_changed()

    def on_checkbox_changed(self) -> None:
        self._form_changed()

    def on_multiple_choice_changed(self) -> None:
        self._form_changed()

    def _form_changed(self) -> UserCommandData:
        """Take the current state of the form and build a UserCommandData from it,
        then post a FormChanged message"""

        command_schema = self.command_schema
        path_from_root = command_schema.path_from_root

        # Sentinel root value to make constructing the tree a little easier.
        parent_command_data = UserCommandData(
            name=CommandName("_"), options=[], arguments=[]
        )
        root_command_data = parent_command_data
        try:
            for command in path_from_root:
                option_datas = []
                # For each of the options in the schema for this command,
                # lets grab the values the user has supplied for them in the form.

                for option in command.options:
                    form_control_widget = self.query_one(f"#{option.key}")
                    value = self._get_form_control_value(form_control_widget)
                    # Handle the case of multiple=True
                    if option.multiple:
                        for v in value:
                            option_data = UserOptionData(option.name, v, option)
                            option_datas.append(option_data)
                    else:
                        option_data = UserOptionData(option.name, value, option)
                        option_datas.append(option_data)

                # Now do the same for the arguments
                argument_datas = []
                for argument in command.arguments:
                    form_control_widget = self.query_one(f"#{argument.key}")
                    value = self._get_form_control_value(form_control_widget)
                    argument_data = UserArgumentData(argument.name, value, argument)
                    argument_datas.append(argument_data)

                command_data = UserCommandData(
                    name=command.name,
                    options=option_datas,
                    arguments=argument_datas,
                    parent=parent_command_data,
                    command_schema=command,
                )
                parent_command_data.subcommand = command_data
                parent_command_data = command_data
        except Exception as e:
            # TODO
            print(f"exception {e}")
            return

        # Trim the sentinel
        root_command_data = root_command_data.subcommand
        root_command_data.parent = None
        root_command_data.fill_defaults(self.command_schema)
        self.post_message(self.Changed(root_command_data))

    def focus(self, scroll_visible: bool = True):
        return self.first_control.focus()

    @staticmethod
    def _get_form_control_value(
        control: Input | RadioSet | Checkbox | MultipleChoice,
    ) -> Any:
        if isinstance(control, (Input, Checkbox)):
            return control.value
        elif isinstance(control, RadioSet):
            if control.pressed_button is not None:
                return control.pressed_button.label.plain
            return None
        elif isinstance(control, MultipleChoice):
            return control.selected
        elif isinstance(control, MultipleInput):
            return control.values

    def _make_command_form(
        self, schemas: Sequence[ArgumentSchema | OptionSchema], is_option: bool = False
    ):
        for schema in schemas:
            # TODO: This may not be required any more.
            self.schema_key_to_metadata[schema.key] = schema

            name = schema.name
            argument_type = schema.type
            default = schema.default
            help_text = getattr(schema, "help", "") or ""
            multiple = schema.multiple
            label = self._make_command_form_control_label(
                name, argument_type, is_option, schema.required, multiple=multiple
            )
            if argument_type in {
                "text",
                "float",
                "integer",
                "path",
                "integer range",
                "file",
                "filename",
            }:
                yield Label(label, classes="command-form-label")
                if multiple:
                    control = MultipleInput(defaults=schema.default, id=schema.key)
                    yield control
                else:
                    control = Input(
                        value=str(default) if default is not None else "",
                        placeholder=name,
                        id=schema.key,
                        classes="command-form-input",
                    )
                    yield control
            elif argument_type in {"boolean"}:
                control = Checkbox(
                    f"{name}",
                    button_first=False,
                    value=default,
                    classes="command-form-checkbox",
                    id=schema.key,
                )
                yield control
            elif argument_type in {"choice"}:
                yield Label(label, classes="command-form-label")
                if multiple:
                    multi_choice = MultipleChoice(
                        list(schema.choices),
                        classes="command-form-multiple-choice",
                        id=schema.key,
                        defaults=default,
                    )
                    control = multi_choice
                    yield multi_choice
                else:
                    with RadioSet(
                        id=schema.key, classes="command-form-radioset"
                    ) as radio_set:
                        control = radio_set
                        for index, choice in enumerate(schema.choices):
                            radio_button = RadioButton(choice)
                            if schema.default == choice or (
                                schema.default is None and index == 0
                            ):
                                radio_button.value = True
                            yield radio_button

            # Take note of the first form control, so we can easily render it
            if self.first_control is None:
                self.first_control = control

            # Render the dim help text below the form controls
            if help_text:
                yield Static(help_text, classes="command-form-control-help-text")

    # def _build_command_data(self) -> UserCommandData:
    #     """Takes the current state of this form and converts it into a UserCommandData,
    #     ready to be executed."""

    # def _validate_command_data(self) -> None:
    #     validate_user_command_data(self.command_schemas, self.)

    @staticmethod
    def _make_command_form_control_label(
        name: str, type: str, is_option: bool, is_required: bool, multiple: bool
    ) -> Text:
        return Text.from_markup(
            f"{'--' if is_option else ''}{name.replace('_', '-') if is_option else name}[dim]{' multiple' if multiple else ''} {type}[/] {' [b red]*[/]required' if is_required else ''}"
        )

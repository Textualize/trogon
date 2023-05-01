from __future__ import annotations

import dataclasses
from typing import Sequence, Any, Callable, Iterable

import click
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
        """Takes the schemas for each parameter of the current command, and converts it into a
        form consisting of Textual widgets."""
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
            control: Widget | None = None
            print(argument_type)
            if argument_type in {
                click.types.STRING,
                click.types.FLOAT,
                click.types.INT,
                click.types.UUID,
                "integer range",  # TODO - update these types
                "filename",
            } or isinstance(
                argument_type,
                (
                    click.types.Path,
                    click.types.File,
                    click.types.IntRange,
                    click.types.FloatRange,
                ),
            ):
                control = yield from self.make_text_control(
                    default, label, multiple, schema
                )
            elif argument_type == click.types.BOOL:
                control = yield from self.make_checkbox_control(default, label, multiple, schema)
            elif isinstance(argument_type, click.types.Choice):
                control = yield from self.make_choice_control(
                    default, label, multiple, schema
                )
            elif isinstance(argument_type, click.types.Tuple):
                # This is the case for multi-value options. e.g. --paths "." "../" "path"
                # We need to ensure we render the correct type for each of the values in the tuple
                print(argument_type.types)
            else:
                print("Couldn't decide what to render")
                print(schema.name, argument_type, type(schema.type))

            # Take note of the first form control, so we can easily render it
            if self.first_control is None:
                self.first_control = control

            # Render the dim help text below the form controls
            if help_text:
                yield Static(help_text, classes="command-form-control-help-text")

    def get_control_method(self, argument_type: Any) -> Callable[
        [Any, Text, bool, OptionSchema | ArgumentSchema], Widget]:
        text_click_types = {
            click.types.STRING,
            click.types.FLOAT,
            click.types.INT,
            click.types.UUID,
            "integer range",  # TODO - update these types
            "filename",
        }
        text_types = (
            click.types.Path,
            click.types.File,
            click.types.IntRange,
            click.types.FloatRange,
        )
        is_text_type = argument_type in text_click_types or isinstance(argument_type, text_types)
        if is_text_type:
            return self.make_text_control

    @staticmethod
    def make_text_control(default: Any, label: Text, multiple: bool, schema: OptionSchema | ArgumentSchema) -> Widget:
        yield Label(label, classes="command-form-label")
        if multiple:
            control = MultipleInput(defaults=schema.default, id=schema.key)
            yield control
        else:
            control = Input(
                value=str(default) if default is not None else "",
                placeholder=str(default) if default is not None else "",
                id=schema.key,
                classes="command-form-input",
            )
            yield control
        return control

    @staticmethod
    def make_checkbox_control(default: Any, label: Text, multiple: bool,
                              schema: OptionSchema | ArgumentSchema) -> Widget:
        control = Checkbox(
            label,
            button_first=False,
            value=default,
            classes="command-form-checkbox",
            id=schema.key,
        )
        yield control
        return control

    @staticmethod
    def make_choice_control(default: Any, label: Text, multiple: bool, schema: OptionSchema | ArgumentSchema) -> Widget:
        yield Label(label, classes="command-form-label")
        if multiple:
            multi_choice = MultipleChoice(
                list(schema.choices),
                classes="command-form-multiple-choice",
                id=schema.key,
                defaults=default,
            )
            yield multi_choice
            return multi_choice
        else:
            with RadioSet(id=schema.key, classes="command-form-radioset") as radio_set:
                for index, choice in enumerate(schema.choices):
                    radio_button = RadioButton(choice)
                    if schema.default == choice or (
                        schema.default is None and index == 0
                    ):
                        radio_button.value = True
                    yield radio_button
                return radio_set

    @staticmethod
    def _make_command_form_control_label(
        name: str | list[str],
        type: str,
        is_option: bool,
        is_required: bool,
        multiple: bool,
    ) -> Text:
        if isinstance(name, str):
            return Text.from_markup(
                f"{name}[dim]{' multiple' if multiple else ''} {type}[/] {' [b red]*[/]required' if is_required else ''}"
            )
        elif isinstance(name, list):
            names = Text(" / ", style="dim").join([Text(n) for n in name])
            return f"{names}[dim]{' multiple' if multiple else ''} {type}[/] {' [b red]*[/]required' if is_required else ''}"

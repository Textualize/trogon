from __future__ import annotations

from functools import partial
from typing import Any, Callable

import click
from rich.text import Text
from textual import log
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import RadioButton, RadioSet, Label, Checkbox, Input, Static, Button

from textual_click.introspect import ArgumentSchema, OptionSchema
from textual_click.widgets.multiple_choice import MultipleChoice


class ControlGroup(Vertical):
    pass


class ParameterControls(Widget):

    def __init__(
        self,
        schema: ArgumentSchema | OptionSchema,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.schema = schema
        self.first_control: Widget | None = None

    def compose(self) -> ComposeResult:
        """Takes the schemas for each parameter of the current command, and converts it into a
        form consisting of Textual widgets."""
        schema = self.schema
        name = schema.name
        argument_type = schema.type
        default = schema.default
        help_text = getattr(schema, "help", "") or ""
        multiple = schema.multiple
        is_option = isinstance(schema, OptionSchema)

        label = self._make_command_form_control_label(
            name, argument_type, is_option, schema.required, multiple=multiple
        )
        first_focus_control: Widget | None = None  # The widget that will be focused when the form is focused.
        print(argument_type)

        yield Label(label, classes="command-form-label")
        if not isinstance(argument_type, click.Tuple):
            # Single-value option, but they could still be multiple=True, and
            # there could be multiple defaults. We need to render one control
            # for each of the defaults.
            many_defaults = multiple and default
            if many_defaults:
                for default_value in default:
                    control_method = self.get_control_method(argument_type)
                    first_focus_control = yield from control_method(default_value, label, multiple, schema, schema.key)
            elif default:
                control_method = self.get_control_method(argument_type)
                first_focus_control = yield from control_method(default, label, multiple, schema, schema.key)
        else:
            # Multi-value option
            if default:
                for defaults in default:
                    with ControlGroup():
                        for _type, default in zip(argument_type.types, defaults):
                            print(_type, default)
                            control_method = self.get_control_method(_type)
                            control = yield from control_method(default, label, multiple, schema, schema.key)
                            if first_focus_control is None:
                                first_focus_control = control

            with ControlGroup():
                for _type in argument_type.types:
                    control_method = self.get_control_method(_type)
                    control = yield from control_method(default, label, multiple, schema, schema.key)
                    if first_focus_control is None:
                        first_focus_control = control

        # Take note of the first form control, so we can easily focus it
        if self.first_control is None:
            self.first_control = first_focus_control

        # TODO Add handler for this button and probably filter by id
        if multiple:
            yield Button("Add another")

        # Render the dim help text below the form controls
        if help_text:
            yield Static(help_text, classes="command-form-control-help-text")

    # def get_values(self) -> list[tuple]:

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

    def get_control_method(self, argument_type: Any) -> Callable[
        [Any, Text, bool, OptionSchema | ArgumentSchema, str], Widget]:
        text_click_types = {
            click.STRING,
            click.FLOAT,
            click.INT,
            click.UUID,
        }
        text_types = (
            click.Path,
            click.File,
            click.IntRange,
            click.FloatRange,
        )

        is_text_type = argument_type in text_click_types or isinstance(argument_type, text_types)
        if is_text_type:
            return self.make_text_control
        elif argument_type == click.BOOL:
            return self.make_checkbox_control
        elif isinstance(argument_type, click.types.Choice):
            return partial(self.make_choice_control, choices=argument_type.choices)
        else:
            log.error(f"Given type {argument_type}, we couldn't determine which form control to render.")

    @staticmethod
    def make_text_control(default: Any, label: Text, multiple: bool, schema: OptionSchema | ArgumentSchema,
                          control_id: str) -> Widget:
        control = Input(
            value=str(default) if default is not None else "",
            placeholder=str(default) if default is not None else "",
            classes=f"command-form-input {control_id}",
        )
        yield control
        return control

    @staticmethod
    def make_checkbox_control(default: Any, label: Text, multiple: bool,
                              schema: OptionSchema | ArgumentSchema, control_id: str) -> Widget:
        control = Checkbox(
            label,
            button_first=False,
            value=default,
            classes=f"command-form-checkbox {control_id}",
        )
        yield control
        return control

    @staticmethod
    def make_choice_control(default: Any, label: Text, multiple: bool, schema: OptionSchema | ArgumentSchema,
                            control_id: str, choices: list[str]) -> Widget:
        if multiple:
            multi_choice = MultipleChoice(
                choices,
                classes=f"command-form-multiple-choice {control_id}",
                defaults=default,
            )
            yield multi_choice
            return multi_choice
        else:
            with RadioSet(classes=f"{control_id} command-form-radioset") as radio_set:
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
        type: click.ParamType,
        is_option: bool,
        is_required: bool,
        multiple: bool,
    ) -> Text:
        if isinstance(name, str):
            return Text.from_markup(
                f"{name}[dim]{' multiple' if multiple else ''} {type.name}[/] {' [b red]*[/]required' if is_required else ''}"
            )
        elif isinstance(name, list):
            names = Text(" / ", style="dim").join([Text(n) for n in name])
            return f"{names}[dim]{' multiple' if multiple else ''} {type.name}[/] {' [b red]*[/]required' if is_required else ''}"

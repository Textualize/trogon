from __future__ import annotations

from functools import partial
from typing import Any, Callable, Iterable, TypeVar, Union

import click
from rich.text import Text
from textual import log
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import RadioButton, RadioSet, Label, Checkbox, Input, Static, Button

from textual_click.introspect import ArgumentSchema, OptionSchema
from textual_click.widgets.multiple_choice import MultipleChoice

ControlWidgetType: TypeVar = Union[Input, RadioSet, Checkbox, MultipleChoice]


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

        # If there are N defaults, we render the "group" N times.
        # Each group will contain `nargs` widgets.

        yield Label(label, classes="command-form-label")

        # Functionality needed for rendering the form:
        # Get the renderables for the widget set (if single value, the widget set is just of size 1)
        # Fill the widget set with a group of default values
        # Add a button which adds another widget set.

        if isinstance(argument_type, click.Choice) and multiple:
            # There's a special case where we have a Choice with multiple=True,
            # in this case, we can just render a single MultipleChoice widget
            # instead of multiple radio-sets.
            control_method = self.get_control_method(argument_type)
            multiple_choice_widget = control_method(default=default, label=label, multiple=multiple, schema=schema,
                                                    control_id=schema.key)
            yield from multiple_choice_widget
        else:
            # For other widgets, we'll render as normal...
            # If required, we'll generate widgets containing the defaults
            if default:
                defaults = default if multiple else [default]
                for default_value in defaults:
                    widget_group = self.make_widget_group()
                    print(f"Parameter {name}: defaults = {defaults!r}")
                    with ControlGroup():
                        # Parameter types can be of length 1, but there could still be multiple defaults.
                        # We need to render a widget for each of those defaults.
                        # Extend the widget group such that there's a slot available for each default...
                        for control_widget in widget_group:
                            self._apply_default_value(control_widget, default_value)
                            yield control_widget
                            # Keep track of the first control we render, for easy focus
                            if first_focus_control is None:
                                first_focus_control = control_widget

            # We always need to display the original group of controls, regardless of whether there are defaults
            if multiple or not default:
                widget_group = self.make_widget_group()
                with ControlGroup():
                    # No need to apply defaults to this group
                    for control_widget in widget_group:
                        yield control_widget
                        if first_focus_control is None:
                            first_focus_control = control_widget

        # Take note of the first form control, so we can easily focus it
        if self.first_control is None:
            self.first_control = first_focus_control

        # If it's a multiple and it's a Choice parameter, then we display
        # our special case MultiChoice widget, and so there's no need for this
        # button.
        if multiple and not isinstance(argument_type, click.Choice):
            # TODO Add handler for this button and probably filter by id
            yield Button("Add another", variant="primary")

        # Render the dim help text below the form controls
        if help_text:
            yield Static(help_text, classes="command-form-control-help-text")

    def make_widget_group(self) -> Iterable[Widget]:
        """For this option, yield a single set of widgets required to receive user input for it."""
        schema = self.schema
        default = schema.default
        parameter_type = schema.type
        name = schema.name
        multiple = schema.multiple
        required = schema.required
        is_option = isinstance(schema, OptionSchema)
        label = self._make_command_form_control_label(name, parameter_type, is_option, required, multiple)

        # Get the types of the parameter. We can map these types on to widgets that will be rendered.
        parameter_types = parameter_type.types if isinstance(parameter_type, click.Tuple) else [parameter_type]

        # For each of the these parameters, render the corresponding widget for it.
        # At this point we don't care about filling in the default values.
        for _type in parameter_types:
            control_method = self.get_control_method(_type)
            control_widgets = control_method(default, label, multiple, schema, schema.key)
            yield from control_widgets

    @staticmethod
    def _apply_default_value(control_widget: ControlWidgetType, default_value: Any) -> None:
        """Set the default value of a parameter-handling widget."""
        if isinstance(control_widget, Input):
            print(f"Setting Input widget value to: {default_value}")
            control_widget.value = str(default_value)
        elif isinstance(control_widget, RadioSet):
            for item in control_widget.walk_children():
                if isinstance(item, RadioButton):
                    label = item.label.plain
                    item.value = label == default_value

    @staticmethod
    def _get_form_control_value(control: ControlWidgetType) -> Any:
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
            classes=f"command-form-checkbox {control_id}",
        )
        yield control
        return control

    @staticmethod
    def make_choice_control(default: Any, label: Text, multiple: bool, schema: OptionSchema | ArgumentSchema,
                            control_id: str, choices: list[str]) -> Widget:

        # The MultipleChoice widget is only for single-valued parameters.
        if isinstance(schema.type, click.Tuple):
            multiple = False

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
                for index, choice in enumerate(choices):
                    radio_button = RadioButton(choice)
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

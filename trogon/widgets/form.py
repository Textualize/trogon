from __future__ import annotations

import dataclasses

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label, Input

from trogon.introspect import (
    CommandSchema,
    CommandName,
    ArgumentSchema,
    OptionSchema,
)
from trogon.run_command import UserCommandData, UserOptionData, UserArgumentData
from trogon.widgets.parameter_controls import ParameterControls


@dataclasses.dataclass
class FormControlMeta:
    widget: Widget
    meta: OptionSchema | ArgumentSchema


class CommandForm(Widget):
    """Form which is constructed from an introspected Click app. Users
    make use of this form in order to construct CLI invocation strings."""

    DEFAULT_CSS = """    
    .command-form-heading {
        padding: 1 0 0 1;
        text-style: u;
        color: $text;
    }
    .command-form-input {        
        border: tall transparent;
    }
    .command-form-label {
        padding: 1 0 0 1;
    }
    .command-form-checkbox {
        background: $boost;
        margin: 1 0 0 0;
        padding-left: 1;
        border: tall transparent;
    }
    .command-form-checkbox:focus {
      border: tall $accent;      
    }
    .command-form-checkbox:focus > .toggle--label {
        text-style: none;
    }
    .command-form-command-group {
        
        margin: 1 2;
        padding: 0 1;
        height: auto;
        background: $foreground 3%;
        border: panel $background;
        border-title-color: $text 80%;
        border-title-style: bold;
        border-subtitle-color: $text 30%;
        padding-bottom: 1;
    }
    .command-form-command-group:focus-within {
        border: panel $primary;
    }
    .command-form-control-help-text {        
        height: auto;
        color: $text 40%;
        padding-top: 0;
        padding-left: 1;
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
        self.first_control: ParameterControls | None = None

    def compose(self) -> ComposeResult:
        path_from_root = iter(reversed(self.command_schema.path_from_root))
        command_node = next(path_from_root)
        with VerticalScroll() as vs:
            vs.can_focus = False

            yield Input(
                placeholder="Search...",
                classes="command-form-filter-input",
                id="search",
            )

            while command_node is not None:
                options = command_node.options
                arguments = command_node.arguments
                if options or arguments:
                    with Vertical(
                        classes="command-form-command-group", id=command_node.key
                    ) as v:
                        is_inherited = command_node is not self.command_schema
                        v.border_title = (
                            f"{'↪ ' if is_inherited else ''}{command_node.name}"
                        )
                        if is_inherited:
                            v.border_title += " [dim not bold](inherited)"
                        if arguments:
                            yield Label(f"Arguments", classes="command-form-heading")
                            for argument in arguments:
                                controls = ParameterControls(argument, id=argument.key)
                                if self.first_control is None:
                                    self.first_control = controls
                                yield controls

                        if options:
                            yield Label(f"Options", classes="command-form-heading")
                            for option in options:
                                controls = ParameterControls(option, id=option.key)
                                if self.first_control is None:
                                    self.first_control = controls
                                yield controls

                command_node = next(path_from_root, None)

    def on_mount(self) -> None:
        self._form_changed()

    def on_input_changed(self) -> None:
        self._form_changed()

    def on_select_changed(self) -> None:
        self._form_changed()

    def on_checkbox_changed(self) -> None:
        self._form_changed()

    def on_multiple_choice_changed(self) -> None:
        self._form_changed()

    def _form_changed(self) -> None:
        """Take the current state of the form and build a UserCommandData from it,
        then post a FormChanged message"""

        command_schema = self.command_schema
        path_from_root = command_schema.path_from_root

        # Sentinel root value to make constructing the tree a little easier.
        parent_command_data = UserCommandData(
            name=CommandName("_"), options=[], arguments=[]
        )

        root_command_data = parent_command_data
        for command in path_from_root:
            option_datas = []
            # For each of the options in the schema for this command,
            # lets grab the values the user has supplied for them in the form.
            for option in command.options:
                parameter_control = self.query_one(f"#{option.key}", ParameterControls)
                value = parameter_control.get_values()
                for v in value.values:
                    assert isinstance(v, tuple)
                    option_data = UserOptionData(option.name, v, option)
                    option_datas.append(option_data)

            # Now do the same for the arguments
            argument_datas = []
            for argument in command.arguments:
                form_control_widget = self.query_one(
                    f"#{argument.key}", ParameterControls
                )
                value = form_control_widget.get_values()
                # This should only ever loop once since arguments can be multi-value but not multiple=True.
                for v in value.values:
                    assert isinstance(v, tuple)
                    argument_data = UserArgumentData(argument.name, v, argument)
                    argument_datas.append(argument_data)

            assert all(isinstance(option.value, tuple) for option in option_datas)
            assert all(isinstance(argument.value, tuple) for argument in argument_datas)
            command_data = UserCommandData(
                name=command.name,
                options=option_datas,
                arguments=argument_datas,
                parent=parent_command_data,
                command_schema=command,
            )
            parent_command_data.subcommand = command_data
            parent_command_data = command_data

        # Trim the sentinel
        root_command_data = root_command_data.subcommand
        root_command_data.parent = None
        self.post_message(self.Changed(root_command_data))

    def focus(self, scroll_visible: bool = True):
        if self.first_control is not None:
            return self.first_control.focus()

    @on(Input.Changed, ".command-form-filter-input")
    def apply_filter(self, event: Input.Changed) -> None:
        filter_query = event.value
        all_controls = self.query(ParameterControls)
        for control in all_controls:
            filter_query = filter_query.casefold()
            control.apply_filter(filter_query)

from __future__ import annotations

from typing import Any, ClassVar

from rich.text import TextType
from textual import on
from textual.app import ComposeResult
from textual.binding import BindingType, Binding
from textual.containers import VerticalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Checkbox


class NonFocusableVerticalScroll(VerticalScroll, can_focus=False):
    pass


class MultipleChoice(Widget):
    DEFAULT_CSS = """
    MultipleChoice {
        border: round #666;
        width: auto;
        height: auto;
    }
    MultipleChoice > VerticalScroll {
        height: auto;
        width: auto;
    }
    
    MultipleChoice :focus-within {
        border: round $primary-lighten-2;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("down,right", "next_button", "", show=False),
        Binding("up,left", "previous_button", "", show=False),
    ]

    def __init__(
        self,
        options: list[TextType],
        defaults: list[tuple[Any]] | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        if defaults is None:
            defaults = [()]
        self.options = options
        self.defaults = defaults
        self.selected = defaults

    class Changed(Message):
        def __init__(self, selected: list[Checkbox]):
            super().__init__()
            self.selected = selected

    def compose(self) -> ComposeResult:
        with NonFocusableVerticalScroll():
            for option in self.options:
                yield Checkbox(option, value=(option,) in self.defaults)

    @on(Checkbox.Changed)
    def checkbox_toggled(self) -> None:
        checkboxes = self.query(Checkbox)
        selected = []
        for checkbox in checkboxes:
            if checkbox.value is True:
                selected.append(checkbox)
        self.selected = [(checkbox.label.plain,) for checkbox in selected]
        self.post_message(self.Changed(selected))

    def select_by_label(self, label: str) -> None:
        checkboxes = self.query(Checkbox)
        for checkbox in checkboxes:
            checkbox.value = checkbox.label == label

    def action_next_button(self) -> None:
        focused = self.app.focused
        checkboxes = list(self.query(Checkbox))
        if focused is checkboxes[-1]:
            checkboxes[0].focus()
        else:
            self.app.action_focus_next()

    def action_previous_button(self) -> None:
        focused = self.app.focused
        checkboxes = list(self.query(Checkbox))
        if focused is checkboxes[0]:
            checkboxes[-1].focus()
        else:
            self.app.action_focus_previous()

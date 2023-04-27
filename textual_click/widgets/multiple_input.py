from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Button


class MultipleInput(Widget):
    DEFAULT_CSS = """
    MultipleInput {
        height: auto;
    }
    
    MultipleInput > Horizontal {
        height: auto;
        width: auto;
    }
    
    MultipleInput Input {
        width: 1fr;
    }
    MultipleInput Button {
        width: auto;
    }
    
    """

    class Changed(Message):
        def __init__(self):
            super().__init__()

    def __init__(
        self,
        defaults: list[str] = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        super().__init__(
            name=name, id=id, classes=classes, disabled=disabled
        )
        if defaults is None:
            defaults = []
        self.defaults = defaults

    def compose(self) -> ComposeResult:
        if self.defaults:
            for index, default in enumerate(self.defaults):
                with Horizontal():
                    yield Input(value=default)
                    if index == len(self.defaults) - 1:
                        yield self.button
        else:
            with Horizontal():
                yield Input()
                yield self.button

    @property
    def values(self) -> list[str]:
        inputs = self.query(Input)
        return [input_widget.value for input_widget in inputs]

    def on_input_changed(self) -> None:
        self.post_message(self.Changed())

    async def on_input_submitted(self) -> None:
        await self._add_new_row()

    async def on_button_pressed(self) -> None:
        await self._add_new_row()

    async def _add_new_row(self) -> None:
        button = self.query_one(Button)
        await button.remove()
        new_button = self.button
        new_input = Input()
        await self.mount(Horizontal(new_input, new_button))
        new_input.focus()

    @property
    def button(self) -> Button:
        return Button(label="Add another", variant="primary")

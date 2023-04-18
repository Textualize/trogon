from textual.app import App, ComposeResult
from textual.widgets import Label


class TextualClick(App):

    def compose(self) -> ComposeResult:
        yield Label("Hello, world!")


app = TextualClick()
if __name__ == '__main__':
    app.run()

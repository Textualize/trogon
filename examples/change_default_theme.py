import click
from textual.app import App

from trogon import tui


def on_mount(app: App):
    app.theme = 'tokyo-night'

@tui(on_mount=on_mount)
@click.command()
def hello_world():
    """Prints 'Hello world'."""
    click.echo('Hello world.')

if __name__ == "__main__":
    hello_world()
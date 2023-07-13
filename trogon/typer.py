from __future__ import annotations
from trogon.click import click, introspect_click_app
from trogon.constants import DEFAULT_COMMAND_NAME

try:
    import typer
except ImportError as e:
    raise ImportError(
        "The extra `trogon[typer]` is required to enable tui generation from Typer apps."
    ) from e

from trogon.trogon import Trogon


def tui(
    app: typer.Typer,
    name: str | None = None,
    command: str = DEFAULT_COMMAND_NAME,
    help: str = "Open Textual TUI.",
):
    def wrapped_tui():
        Trogon(
            introspect_click_app(typer.main.get_group(app), cmd_ignorelist=[command]),
            app_name=name,
        ).run()

    app.command(name=command, help=help)(wrapped_tui)

    return app

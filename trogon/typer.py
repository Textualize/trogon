import click

try:
    import typer
except ImportError:
    raise ImportError(
        "The extra `trogon[typer]` is required to enable tui generation from Typer apps."
    )

from trogon.trogon import Trogon


def init_tui(app: typer.Typer, name: str | None = None):
    def wrapped_tui():
        Trogon(
            typer.main.get_group(app),
            app_name=name,
            click_context=click.get_current_context(),
        ).run()

    app.command("tui", help="Open Textual TUI.")(wrapped_tui)

    return app

from typing import Annotated

import typer
from trogon.typer import init_tui


app = typer.Typer()


@app.command()
def hello(name: Annotated[str, typer.Argument(help="The person to greet")]):
    typer.echo(f"Hello, {name}!")


init_tui(app)


if __name__ == "__main__":
    app()

import click
from trogon import tui


@tui()
@click.group()
def cli():
    pass


@cli.command()
@click.argument("name", default="Bob")
def hello(name):
    """Print hello."""
    print(f"Hello world and {name}")


@cli.command()
@click.argument("surname", default="Odenkirk")
def hello_surname(name):
    print(f"Hello world and surname {name}")


if __name__ == "__main__":
    cli()

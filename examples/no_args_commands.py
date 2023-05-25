import click

from trogon import tui


@tui()
@click.group()
@click.option("-v", "--verbose", count=True)
def cli(verbose):
    return


@cli.command()
@click.argument("test")
@click.pass_context
def test1():
    return


@cli.command()
@click.pass_context
def test2():
    return


if __name__ == "__main__":
    cli(obj={})

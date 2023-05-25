import click

from trogon import tui


@tui()
@click.group()
def cli():
    pass


@cli.command()
@click.argument("args", nargs=-1)
@click.option("-a")
@click.option("-b")
def command():
    pass


if __name__ == '__main__':
    cli()

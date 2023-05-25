import click
from trogon import tui


@tui()
@click.group()
def main():
    pass


class _TestSuiteCases(click.ParamType):
    name = "thingy"

    def convert(self, value, param, ctx) -> int:
        return 37


@main.command()
@click.argument("input", type=_TestSuiteCases())
def foo(input):
    pass


main()
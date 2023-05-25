import click
from click.testing import CliRunner
import re
from trogon import tui


@tui()
@click.group()
def default():
    pass


@tui(command="custom")
@click.group()
def custom_command():
    pass


@tui(help="Custom help")
@click.group()
def custom_help():
    pass


def test_default_help():
    result = CliRunner().invoke(default, ["--help"])
    assert re.search(r"tui\s+Open Textual TUI", result.output) is not None


def test_custom_command():
    result = CliRunner().invoke(custom_command, ["--help"])
    assert re.search(r"custom\s+Open Textual TUI", result.output) is not None


def test_custom_help():
    result = CliRunner().invoke(custom_help, ["--help"])
    assert re.search(r"tui\s+Custom help", result.output) is not None

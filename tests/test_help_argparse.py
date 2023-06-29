import argparse
from trogon.argparse import add_tui_argument, add_tui_command
import re


def test_default_help(capsys):
    parser = argparse.ArgumentParser()
    add_tui_command(parser)
    parser.print_help()

    result = capsys.readouterr()
    assert re.search(r"tui\s+Open Textual TUI", result.out) is not None


def test_custom_command(capsys):
    parser = argparse.ArgumentParser()
    add_tui_command(parser, command="custom")
    parser.print_help()

    result = capsys.readouterr()
    assert re.search(r"custom\s+Open Textual TUI", result.out) is not None


def test_custom_help(capsys):
    parser = argparse.ArgumentParser()
    add_tui_command(parser, help="Custom help")
    parser.print_help()

    result = capsys.readouterr()
    assert re.search(r"tui\s+Custom help", result.out) is not None


def test_default_help_argument(capsys):
    parser = argparse.ArgumentParser()
    add_tui_argument(parser)
    parser.print_help()

    result = capsys.readouterr()
    assert re.search(r"--tui\s+\[CMD\]\s+Open Textual TUI", result.out) is not None


def test_custom_command_argument(capsys):
    parser = argparse.ArgumentParser()
    add_tui_argument(parser, option_strings="--custom")
    parser.print_help()

    result = capsys.readouterr()
    assert re.search(r"--custom\s+\[CMD\]\s+Open Textual TUI", result.out) is not None


def test_custom_help_argument(capsys):
    parser = argparse.ArgumentParser()
    add_tui_argument(parser, help="Custom help")
    parser.print_help()

    result = capsys.readouterr()
    assert re.search(r"--tui\s+\[CMD\]\s+Custom help", result.out) is not None

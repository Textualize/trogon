import asyncio

import click
import pytest
from textual.app import App, ComposeResult
from textual.widgets import Input

from trogon.introspect import introspect_click_app
from trogon.widgets.parameter_controls import ParameterControls


@pytest.mark.parametrize("parameter_class", [click.Option, click.Argument])
@pytest.mark.parametrize("required", [False, True])
def test_omitted_defaults(parameter_class, required):
    name = "--path" if parameter_class is click.Option else "path"
    parameter = parameter_class([name], type=click.Path(), required=required)
    command = click.Command("example", params=[parameter])

    schema = introspect_click_app(command)["example"]
    parameter_schema = (schema.options + schema.arguments)[0]

    assert parameter_schema.default.values == []


@pytest.mark.parametrize(
    "default, expected",
    [
        (None, []),
        ("", [("",)]),
        (0, [(0,)]),
        (False, [(False,)]),
        ("Sentinel.UNSET", [("Sentinel.UNSET",)]),
        ("example.txt", [("example.txt",)]),
    ],
)
def test_explicit_defaults(default, expected):
    command = click.Command(
        "example", params=[click.Option(["--value"], default=default)]
    )

    schema = introspect_click_app(command)["example"]

    assert schema.options[0].default.values == expected


def test_path_input_without_default_is_empty():
    command = click.Command(
        "example", params=[click.Option(["--path"], type=click.Path())]
    )
    schema = introspect_click_app(command)["example"].options[0]

    class PathApp(App):
        def compose(self) -> ComposeResult:
            yield ParameterControls(schema)

    async def check_input():
        app = PathApp()
        async with app.run_test():
            field = app.query_one(Input)
            assert field.value == ""
            assert "Sentinel.UNSET" not in field.placeholder

    asyncio.run(check_input())

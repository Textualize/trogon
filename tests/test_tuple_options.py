import click
import pytest
from click.testing import CliRunner

from trogon.introspect import introspect_click_app
from trogon.run_command import UserCommandData, UserOptionData


@pytest.mark.parametrize(
    "option_type, default, value, expected_args, expected_value",
    [
        ((int, int), (1, 2), ("2", "1"), ["--pair", "2", "1"], (2, 1)),
        ((int, int), (1, 2), ("1", "2"), [], (1, 2)),
        (
            (int, str),
            (1, "first"),
            ("2", "second"),
            ["--pair", "2", "second"],
            (2, "second"),
        ),
        ((int, str), (1, "first"), ("1", "first"), [], (1, "first")),
        ((float, str), (0.0, "test"), ("0.0", "test"), [], (0.0, "test")),
        (
            (str, str),
            ("left", "right"),
            ("right", "left"),
            ["--pair", "right", "left"],
            ("right", "left"),
        ),
    ],
)
def test_tuple_option_preserves_positions(
    option_type, default, value, expected_args, expected_value
):
    received = []

    @click.command()
    @click.option("--pair", type=option_type, default=default)
    def command(pair):
        received.append(pair)

    schema = introspect_click_app(command)["command"]
    user_command = UserCommandData(
        name=schema.name,
        options=[UserOptionData("--pair", value, schema.options[0])],
    )

    args = user_command.to_cli_args()
    assert args == expected_args
    result = CliRunner().invoke(command, args)
    assert result.exit_code == 0, result.output
    assert received == [expected_value]


def test_mixed_tuple_option_can_be_edited_in_tui():
    import asyncio

    from textual.widgets import Input

    from trogon.trogon import Trogon

    @click.command()
    @click.option("--pair", type=(int, str), default=(1, "first"))
    def command(pair):
        pass

    async def exercise():
        app = Trogon(command, app_name="example")
        async with app.run_test() as pilot:
            await pilot.pause()
            inputs = list(app.query("ParameterControls Input").results(Input))
            assert [control.value for control in inputs] == ["1", "first"]
            assert app.post_run_command == ["command"]
            inputs[0].value = "2"
            inputs[1].value = "second"
            await pilot.pause()
            assert app.post_run_command == ["command", "--pair", "2", "second"]

    asyncio.run(exercise())

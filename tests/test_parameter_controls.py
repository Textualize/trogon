import click
from textual.widgets import Input
from textual_autocomplete import PathAutoComplete

from trogon.trogon import Trogon
from trogon.widgets.parameter_controls import ControlGroup, ParameterControls


@click.group()
@click.option("--in-path", type=click.Path(), help="An input path")
@click.option("--name", type=str, help="A plain string")
def path_cli(in_path, name):
    pass


@path_cli.command()
def sub():
    pass


async def test_path_option_gets_autocomplete_targeting_its_input():
    """A click.Path option's Input is targeted by exactly one PathAutoComplete."""
    app = Trogon(path_cli, app_name="path_cli", command_name="tui")
    async with app.run_test() as pilot:
        app.query_one("CommandTree").focus()
        await pilot.pause()

        autocompletes = list(app.query(PathAutoComplete))
        assert len(autocompletes) == 1

        path_controls = next(
            pc
            for pc in app.query(ParameterControls)
            if pc.schema.name == ["--in-path"]
        )
        path_input = path_controls.query_one(f".{path_controls.schema.key}", Input)
        assert autocompletes[0].target is path_input


async def test_non_path_option_has_no_autocomplete():
    """A plain string option gets no PathAutoComplete, and single-item styling
    still counts only the real control widgets."""
    app = Trogon(path_cli, app_name="path_cli", command_name="tui")
    async with app.run_test() as pilot:
        app.query_one("CommandTree").focus()
        await pilot.pause()

        name_controls = next(
            pc for pc in app.query(ParameterControls) if pc.schema.name == ["--name"]
        )
        assert not list(name_controls.query(PathAutoComplete))

        for control_group in app.query(ControlGroup):
            children = list(control_group.children)
            real_controls = [
                c for c in children if not isinstance(c, PathAutoComplete)
            ]
            if "single-item" in control_group.classes:
                assert len(real_controls) == 1

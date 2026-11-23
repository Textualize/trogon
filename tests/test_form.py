import asyncio

import click
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll

from trogon.introspect import introspect_click_app
from trogon.trogon import Trogon
from trogon.widgets.form import CommandForm


def test_focus_without_scroll_visible_does_not_scroll():
    command = click.Command(
        "cmd", params=[click.Option([f"--option-{i}"]) for i in range(20)]
    )
    command_schemas = introspect_click_app(command)
    (command_schema,) = command_schemas.values()

    class FormApp(App[None]):
        CSS_PATH = Trogon.CSS_PATH

        def compose(self) -> ComposeResult:
            yield CommandForm(
                command_schema=command_schema, command_schemas=command_schemas
            )

    async def run() -> None:
        app = FormApp()
        async with app.run_test(size=(80, 20)) as pilot:
            form = app.query_one(CommandForm)
            scroll = form.query_one(VerticalScroll)
            scroll.scroll_end(animate=False)
            await pilot.pause()
            scroll_y = scroll.scroll_y
            assert scroll_y > 0

            form.focus(scroll_visible=False)
            await pilot.wait_for_scheduled_animations()

            assert app.focused is form.first_control.first_control
            assert scroll.scroll_y == scroll_y

    asyncio.run(run())

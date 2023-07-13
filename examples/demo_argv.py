#!/usr/bin/env python3

from __future__ import annotations

import sys

from trogon import Trogon
from trogon.schemas import ArgumentSchema, CommandName, CommandSchema, OptionSchema
from trogon.constants import DEFAULT_COMMAND_NAME

root_schema: CommandSchema = CommandSchema(
    name=CommandName("hello"),
    docstring="just sayin'",
    options=[
        OptionSchema(
            name=["--name"],
            default="world",
        ),
        OptionSchema(
            name=["-u", "--to-upper"],
            type=bool,
            is_flag=True,
        ),
        OptionSchema(name=["-t", "--test"], type=int, choices=[1, 2, 3]),
        OptionSchema(
            name=["-s", "--subjects"], type=str, multiple=True, multi_value=True
        ),
    ],
    arguments=[
        ArgumentSchema(name=["subjects"], type=str, multiple=True, multi_value=True),
    ],
)

subcmd_1: CommandSchema = CommandSchema(
    name=CommandName("wat"),
    arguments=[
        ArgumentSchema(name="anything", help="wat!"),
    ],
    options=[
        OptionSchema(
            name=["--name"],
            default="world",
        ),
        OptionSchema(
            name=["--to-upper"],
            type=bool,
            is_flag=True,
        ),
    ],
)

tui: Trogon = Trogon.from_schemas(root_schema, subcmd_1, app_name=None)

if __name__ == "__main__":
    if DEFAULT_COMMAND_NAME in sys.argv:
        tui.run()
    else:
        print(sys.argv)

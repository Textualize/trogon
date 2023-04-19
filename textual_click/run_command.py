from __future__ import annotations

import sys
from typing import List, Any

import click


def validate_and_run_command(data: dict[str, Any], user_command: List[str]) -> None:
    def find_command(cmd_data: dict[str, Any], remaining_path: List[str]):
        if not remaining_path:
            return cmd_data

        next_cmd = remaining_path.pop(0)
        if next_cmd in cmd_data['subcommands']:
            return find_command(cmd_data['subcommands'][next_cmd], remaining_path)
        else:
            raise ValueError(f"Invalid command: {next_cmd}")

    cmd_path = user_command
    try:
        cmd_data = find_command(data, cmd_path)
        cmd_obj = cmd_data['function'].__self__
        ctx = click.Context(cmd_obj, info_name=cmd_obj.name, parent=None)
        cmd_obj.invoke(ctx)
    except ValueError as e:
        print(e)
    except click.ClickException as e:
        e.show()
        sys.exit(e.exit_code)

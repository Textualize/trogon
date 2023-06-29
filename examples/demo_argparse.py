#!/usr/bin/env python3

import sys
import argparse

from trogon.argparse import add_tui_argument, add_tui_command

from getpass import getpass
from pprint import pprint


def _print_args(command: str, **kwargs):
    print("---")
    print("*** Command:", command)
    print("*** kwargs:")
    pprint(kwargs)


def root(**kwargs):
    _print_args("root", **kwargs)


def add(**kwargs):
    _print_args("add", **kwargs)


def remove(**kwargs):
    _print_args("remove", **kwargs)


def auth(password: str, **kwargs):
    if not password:
        password = getpass("Password: ")
    _print_args("auth", password=password, **kwargs)


def list_tasks(**kwargs):
    _print_args("list_tasks", **kwargs)


def cant_see_me(**kwargs):
    _print_args("cant_see_me", **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--verbose", "-v", action="count", default=0, help="Increase verbosity level."
    )
    parser.add_argument("--hidden-arg", help=argparse.SUPPRESS)
    parser.set_defaults(_func=root)

    subparsers = parser.add_subparsers()

    sp_add = subparsers.add_parser("add")
    sp_add.set_defaults(_func=add)
    sp_add.add_argument("task")
    sp_add.add_argument(
        "--priority", "-p", default=1, help="Set task priority (default: 1)"
    )
    sp_add.add_argument(
        "--tags", "-t", action="append", help="Add tags to the task (repeatable)"
    )
    sp_add.add_argument(
        "--extra",
        "-e",
        nargs=2,
        type=str,
        default=[("one", "1"), ("two", "2")],
        action="append",
    )
    sp_add.add_argument(
        "--category", "-c", default="home", choices=["work", "home", "leisure"]
    )
    sp_add.add_argument(
        "--labels",
        "-l",
        action="append",
        choices=["important", "urgent", "later"],
        default=["urgent"],
        help="Add labels to the task (repeatable)",
    )

    sp_remove = subparsers.add_parser("remove")
    sp_remove.set_defaults(_func=remove)
    sp_remove.add_argument("task_id", type=int)

    sp_auth = subparsers.add_parser("auth")
    sp_auth.set_defaults(_func=auth)
    sp_auth.add_argument("--user", help="User Name")
    sp_auth.add_argument("--password", help="User Password. <secret, prompt>")
    sp_auth.add_argument("--tokens", action="append", help="Sensitive input. <secret>")

    sp_list_tasks = subparsers.add_parser("list-tasks")
    sp_list_tasks.set_defaults(_func=list_tasks)
    if sys.version_info >= (3, 9):
        sp_list_tasks.add_argument("--all", default=True, action=argparse.BooleanOptionalAction)
    sp_list_tasks.add_argument("--completed", "-c", action="store_true")

    sp_cant_see_me = subparsers.add_parser("cant-see-me", description=argparse.SUPPRESS)
    sp_cant_see_me.set_defaults(_func=cant_see_me)
    sp_cant_see_me.add_argument("--user")

    # add tui argument (my-cli --tui)
    add_tui_argument(parser)
    # and/or, add tui command (my-cli tui)
    add_tui_command(parser)

    args = sys.argv[1:]

    if not args:
        # if no args given, print help and exit.
        parser.print_help()
        parser.exit()

    # parse args
    parsed_args = parser.parse_args(args)

    # call matching function with parsed args
    parsed_args._func(
        **{k: v for k, v in vars(parsed_args).items() if not k.startswith("_")}
    )

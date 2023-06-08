#!/usr/bin/env python3

import click
from trogon.click import tui


@tui()
@click.option("--verbose", "-v", count=True, help="Increase verbosity level.")
@click.option(
    "--priority", "-p", type=int, default=1, help="Set task priority (default: 1)"
)
@click.option("--tags", "-t", multiple=True, help="Add tags to the task (repeatable)")
@click.option(
    "--extra",
    "-e",
    nargs=2,
    type=(str, int),
    multiple=True,
    default=[("one", 1), ("two", 2)],
    help="Add extra data as key-value pairs (repeatable)",
)
@click.option(
    "--category",
    "-c",
    type=click.Choice(["work", "home", "leisure"], case_sensitive=False),
    help="Choose a category for the task",
)
@click.option(
    "--labels",
    "-l",
    type=click.Choice(["important", "urgent", "later"], case_sensitive=False),
    multiple=True,
    help="Add labels to the task (repeatable)",
)
@click.argument("task")
@click.command()
def add(verbose, task, priority, tags, extra, category, labels):
    """Add a new task to the to-do list."""
    if verbose >= 2:
        click.echo(f"Adding task: {task}")
        click.echo(f"Priority: {priority}")
        click.echo(f'Tags: {", ".join(tags)}')
        click.echo(f"Extra data: {extra}")
        click.echo(f"Category: {category}")
        click.echo(f'Labels: {", ".join(labels)}')
    elif verbose >= 1:
        click.echo(f"Adding task: {task}")
    else:
        pass
    # Implement the task adding functionality here


if __name__ == "__main__":
    add()

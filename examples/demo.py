import click

from trogon import tui


@tui()
@click.group()
@click.option(
    "--verbose", "-v", count=True, default=1, help="Increase verbosity level."
)
@click.pass_context
def cli(ctx, verbose):
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@cli.command()
@click.argument("task")
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
    default="home",
    type=click.Choice(["work", "home", "leisure"], case_sensitive=False),
    help="Choose a category for the task",
)
@click.option(
    "--labels",
    "-l",
    type=click.Choice(["important", "urgent", "later"], case_sensitive=False),
    multiple=True,
    default=["urgent"],
    help="Add labels to the task (repeatable)",
)
@click.pass_context
def add(ctx, task, priority, tags, extra):
    """Add a new task to the to-do list.
    Note:
    Control the output of this using the verbosity option.
    """
    if ctx.obj["verbose"] >= 2:
        click.echo(f"Adding task: {task}")
        click.echo(f"Priority: {priority}")
        click.echo(f'Tags: {", ".join(tags)}')
        click.echo(f"Extra data: {extra}")
    elif ctx.obj["verbose"] >= 1:
        click.echo(f"Adding task: {task}")
    else:
        pass
    # Implement the task adding functionality here


@cli.command()
@click.argument("task_id", type=int)
@click.pass_context
def remove(ctx, task_id):
    """Remove a task from the to-do list by its ID."""
    if ctx.obj["verbose"] >= 1:
        click.echo(f"Removing task with ID: {task_id}")
    # Implement the task removal functionality here


@cli.command()
@click.option(
    "--all/--not-all", default=True, help="List all tasks, including completed ones."
)
@click.option("--completed", "-c", is_flag=True, help="List only completed tasks.")
@click.pass_context
def list_tasks(ctx, all, completed):
    """List tasks from the to-do list."""
    if ctx.obj["verbose"] >= 1:
        click.echo(f"Listing tasks:")
    # Implement the task listing functionality here


if __name__ == "__main__":
    cli(obj={})


import click
import typing as t
import inspect
import trogon

class LazyCommand(click.Command):
    """
    This class is a wrapper meant to only load a command's module (file) when
    it's absolutely necessary. This is so we don't have to load potentially
    dozens of script files every time we do a CLI command, and also so that if
    a script happens to be broken, it will be compartmentalized and not affect
    running other scripts.
    """

    def __init__(self,
                 name: str,
                 callback: t.Callable[[], click.Command],
                 short_help: str,
                 params = [],
                 *args,
                 **kwargs):
        assert len(params) == 0,\
                "Additional params were given to a LazyCommand class. "\
                "These should be added to the base command to be called. "
        assert len(kwargs) == 0 and len(args) == 0,\
                "Additional arguments were supplied to a LazyCommand class. "\
                "The only allowed arguments are: name, short_help. "\
                f"Found: {', '.join(kwargs.keys())}"
        super().__init__(name)
        self.short_help = short_help
        self.callback = callback
        self.cmd: click.Command | None = None
        self.hidden = False

    def to_info_dict(self, ctx: click.Context):
        return self._get_cmd().to_info_dict(ctx)
    
    def get_params(self, ctx: click.Context) -> t.List["click.Parameter"]:
        return self._get_cmd().get_params(ctx)
    
    def get_usage(self, ctx: click.Context) -> str:
        return self._get_cmd().get_usage(ctx)

    def get_help(self, ctx: click.Context) -> str:
        return self._get_cmd().get_help(ctx)
    
    def parse_args(self, ctx: click.Context, args: t.List[str]) -> t.List[str]:
        return self._get_cmd().parse_args(ctx, args)

    def invoke(self, ctx: click.Context):
        return self._get_cmd().invoke(ctx)
    
    def get_short_help_str(self, limit: int = 45) -> str:
        return inspect.cleandoc(self.short_help).strip()

    def _get_cmd(self):
        if self.cmd is None:
            self.cmd = self.callback()
        return self.cmd

@trogon.tui(run_if_no_command=True)
@click.group()
def cli():
    """
    Super cool and great CLI
    """
    pass

@click.command()
@click.option('-t', help="Turns on the trigger")
def cmd_1(t):
    """
    cmd_1 finds all the problems you have, and prints them
    """

@click.command()
@click.argument('path')
def cmd_2(path):
    """
    cmd_2 fixes all the problems you have, and prints a report, given a PATH
    """

cmd_1_lazy = LazyCommand("cmd_1", lambda: cmd_1, "Really great command")
cmd_2_lazy = LazyCommand("cmd_2", lambda: cmd_2, "Really amazing command")
cli.add_command(cmd_1_lazy)
cli.add_command(cmd_2_lazy)

def test_lazy_commands():
    cli()

if __name__ == "__main__":
    test_lazy_commands()

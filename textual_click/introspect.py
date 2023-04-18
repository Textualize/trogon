from typing import Dict, Any

import click


def introspect_click_app(app: click.Group) -> Dict[str, Any]:
    """
        Introspect a Click application and build a data structure containing
        information about all commands, options, arguments, and subcommands.

        This function recursively processes each command and its subcommands
        (if any), creating a nested dictionary that includes details about
        options, arguments, and subcommands.

        Args:
            app (click.Group): The Click application's top-level group instance.

        Returns:
            Dict[str, Any]: A nested dictionary containing the Click application's
            structure, including information about commands, options, arguments,
            and subcommands. The dictionary has the following structure:

            {
                'command_name': {
                    'options': [
                        {
                            'name': str,
                            'type': str,
                            'default': Any,
                            'help': Optional[str]
                        },
                        ...
                    ],
                    'arguments': [
                        {
                            'name': str,
                            'type': str,
                            'required': bool
                        },
                        ...
                    ],
                    'subcommands': {
                        'subcommand_name': { ... },
                        ...
                    }
                },
                ...
            }
        """
    data: Dict[str, Any] = {}

    def process_command(cmd_name: str, cmd_obj: click.Command) -> Dict[str, Any]:
        cmd_data: Dict[str, Any] = {
            'docstring': cmd_obj.help,
            'options': [],
            'arguments': [],
            'subcommands': {}
        }

        for param in cmd_obj.params:
            if isinstance(param, click.Option):
                cmd_data['options'].append({
                    'name': param.name,
                    'type': param.type.name,
                    'default': param.default,
                    'help': param.help
                })
            elif isinstance(param, click.Argument):
                cmd_data['arguments'].append({
                    'name': param.name,
                    'type': param.type.name,
                    'required': param.required
                })

        if isinstance(cmd_obj, click.core.Group):
            for subcmd_name, subcmd_obj in cmd_obj.commands.items():
                cmd_data['subcommands'][subcmd_name] = process_command(subcmd_name, subcmd_obj)

        return cmd_data

    for cmd_name, cmd_obj in app.commands.items():
        data[cmd_name] = process_command(cmd_name, cmd_obj)

    return data

<p align="center">
    <img src="https://github.com/Textualize/textualize-cli/assets/554369/bc0b3552-88d8-4eb8-ad14-943be7221120" width="300" align="center">
</p>
    
[![Discord](https://img.shields.io/discord/1026214085173461072)](https://discord.gg/Enf6Z3qhVr)


# Trogon

Trogon generates friendly terminal user interfaces for command line apps.

Currently Trogon works with the popular [Click](https://click.palletsprojects.com/) library for Python, but in the future may support other libraries and languages other than Python.

Trogon inspects the Click app and extracts a *schema* which describes the options / switches / help etc.
It uses the information in the schema to builds a UI.
Ultimately we would like to formalize this schema and a protocol to extract or expose it from apps, which would allow Trogon to build TUIs for any CLI app, regardless of how it was build.
If you are familiar with Swagger, think Swagger for CLIs.

## Why?

Command line apps reward repeated use, but they lack in *discoverability*.
If you don't use a CLI app frequently, or its too large to commit to memory, a Trogon TUI interface can help you (re)discover options and switches.


## Quickstart

1. Import `from textual_click import tui`
2. Add the `@tui` decorator above your click app. e.g.
    ```python
    @tui()
    @click.group(...)
    def cli():
        ...
    ```
3. Your click app will have a new `tui` command available.

See also the `examples` folder for two example apps.

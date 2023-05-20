# Trogon

**WIP, please wait for full release.**

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

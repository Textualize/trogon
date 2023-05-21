
<p align="center">
    <img src="https://github.com/Textualize/trogon/assets/554369/f4751783-c322-4143-a6c1-d8c564d4e38f" alt="A picture of a trogon (bird) sitting on a laptop" width="300" align="center">
</p>
    
[![Discord](https://img.shields.io/discord/1026214085173461072)](https://discord.gg/Enf6Z3qhVr)


# Trogon

Auto-generate friendly terminal user interfaces for command line apps.


<details>  
  <summary> 🎬 Video demonstration </summary>

&nbsp;
    
A quick tour of a Trogon app applied to [sqlite-utils](https://github.com/simonw/sqlite-utils).

https://github.com/Textualize/trogon/assets/554369/c9e5dabb-5624-45cb-8612-f6ecfde70362

</details>


Trogon works with the popular [Click](https://click.palletsprojects.com/) library for Python, but will support other libraries and languages in the future.

## How it works

Trogon inspects your (command line) app and extracts a *schema* which describes the options / switches / help etc.
It then uses that information to build a [Textual](https://github.com/textualize/textual) UI you can use to edit and run the command. 

Ultimately we would like to formalize this schema and a protocol to extract or expose it from apps.
This which would allow Trogon to build TUIs for any CLI app, regardless of how it was built.
If you are familiar with Swagger, think Swagger for CLIs.

## Screenshots

<table>

<tr>
<td>
<img width="100%" alt="Screenshot 2023-05-20 at 12 07 31" src="https://github.com/Textualize/trogon/assets/554369/009cf3f2-f0c4-464b-bd74-60e303864443">
</td>

<td>
<img width="100%" alt="Screenshot 2023-05-20 at 12 08 21" src="https://github.com/Textualize/trogon/assets/554369/b1039ee6-4ba6-4123-b0dd-aa7b2341672f">
</td>
</tr>

<tr>

<td>
<img width="100%" alt="Screenshot 2023-05-20 at 12 08 53" src="https://github.com/Textualize/trogon/assets/554369/c0a42277-e946-4bef-b0d0-3fa87e4ab55b">
</td>

<td>
<img width="100%" alt="Screenshot 2023-05-20 at 12 09 47" src="https://github.com/Textualize/trogon/assets/554369/55477f6c-e6b8-49b6-85c1-b01bee006c8e">
</td>

</tr>

</table>

## Why?

Command line apps reward repeated use, but they lack in *discoverability*.
If you don't use a CLI app frequently, or there are too many options to commit to memory, a Trogon TUI interface can help you (re)discover options and switches.

## What does the name mean?

This project started life as a [Textual](https://github.com/Textualize/textual) experiement, which we have been giving give bird's names to.
A [Trogon](https://www.willmcgugan.com/blog/photography/post/costa-rica-trip-report-2017/#bird) is a beautiful bird I was lucky enough to photograph in 2017.

See also [Frogmouth](https://github.com/Textualize/frogmouth), a Markdown browser for the terminal.

## Roadmap

Trogon is usable now. It is only 2 lines (!) of code to add to an existing project.

It is still in an early stage of development, and we have lots of improvements planned for it.

## Installing

Trogon may be installed with PyPI.

```bash
pip install trogon
```

## Quickstart

1. Import `from trogon import tui`
2. Add the `@tui` decorator above your click app. e.g.
    ```python
    @tui()
    @click.group(...)
    def cli():
        ...
    ```
3. Your click app will have a new `tui` command available.

See also the `examples` folder for two example apps.

## Follow this project

If this app interests you, you may want to join the Textual [Discord server](https://discord.gg/Enf6Z3qhVr) where you can talk to Textual developers / community.

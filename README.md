<p align="center">
    <img src="https://github.com/Textualize/textualize-cli/assets/554369/bc0b3552-88d8-4eb8-ad14-943be7221120" alt="A picture of a trogon (bird) sitting on a laptop" width="300" align="center">
</p>
    
[![Discord](https://img.shields.io/discord/1026214085173461072)](https://discord.gg/Enf6Z3qhVr)


# Trogon

Auto-generate friendly terminal user interfaces for command line apps.


<details>  
  <summary> 🎬 Video demonstration </summary>
  <hr>

A quick tour of a Trogon app applied to [sqlite-utils](https://github.com/simonw/sqlite-utils).


https://github.com/Textualize/trogon/assets/554369/5ad8de04-d9f9-45af-aa21-7cb593951eff

</details>


Trogon works with the popular [Click](https://click.palletsprojects.com/) library for Python, but will support other libraries and even other languages in the future.

## How it works

Trogon inspects your app and extracts a *schema* which describes the options / switches / help etc.
It then uses that information to build a form with a familiar control for each option.
Updating the form generates a command line which you can run with <kbd>ctrl+R</kbd>.

Ultimately we would like to formalize this schema and a protocol to extract or expose it from apps, which would allow Trogon to build TUIs for any CLI app, regardless of how it was build.
If you are familiar with Swagger, think Swagger for CLIs.

## Screenshots


<table>

<tr>
<td>
<img width="100%" alt="Screenshot 2023-05-20 at 12 07 31" src="https://github.com/Textualize/trogon/assets/554369/7b67b9ae-d3e3-4e51-b13c-088bc99ad736">
</td>

<td>
<img width="100%" alt="Screenshot 2023-05-20 at 12 08 21" src="https://github.com/Textualize/trogon/assets/554369/04245bad-4f76-453e-be25-c26d013474db">
</td>
</tr>

<tr>

<td>
<img width="100%" alt="Screenshot 2023-05-20 at 12 08 53" src="https://github.com/Textualize/trogon/assets/554369/8b12fa2e-7d0c-4d21-bdc0-688408cf3cf6">
</td>

<td>
<img width="100%" alt="Screenshot 2023-05-20 at 12 09 47" src="https://github.com/Textualize/trogon/assets/554369/c99d487a-7651-40e5-9bd5-7653e3be713a">
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

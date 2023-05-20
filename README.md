<p align="center">
    <img src="https://github.com/Textualize/textualize-cli/assets/554369/bc0b3552-88d8-4eb8-ad14-943be7221120" width="300" align="center">
</p>
    
[![Discord](https://img.shields.io/discord/1026214085173461072)](https://discord.gg/Enf6Z3qhVr)


# Trogon

Trogon generates friendly terminal user interfaces for command line apps.

Currently Trogon works with the popular [Click](https://click.palletsprojects.com/) library for Python, but in the future may support other libraries and languages other than Python.


<details>  
  <summary> 🎬 Demonstration </summary>
  <hr>

A quick tour of a Trogon app applied to [sqlite-utils](https://github.com/simonw/sqlite-utils).


Uploading Screen Recording 2023-05-20 at 12.24.35.mov…

</details>





Trogon inspects the Click app and extracts a *schema* which describes the options / switches / help etc.
It uses the information in the schema to builds a UI.
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
If you don't use a CLI app frequently, or its too large to commit to memory, a Trogon TUI interface can help you (re)discover options and switches.

## What does the name mean?

This project started life as a [Textual](https://github.com/Textualize/textual) experiement, which we give give bird's names to.
A [Trogon](https://www.willmcgugan.com/blog/photography/post/costa-rica-trip-report-2017/#bird) is a very beautiful bird I was lucky enough to photograph in 2017.

## Roadmap



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

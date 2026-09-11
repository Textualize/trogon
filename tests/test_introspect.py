import click
import pytest

from trogon.introspect import CommandName, introspect_click_app


def test_introspect_click_group_explicit_name():
    @click.group("my_custom_group")
    def cli():
        pass

    @cli.command()
    def sub():
        pass

    data = introspect_click_app(cli)
    assert CommandName("my_custom_group") in data
    assert CommandName("root") not in data

    root_schema = data[CommandName("my_custom_group")]
    assert root_schema.name == "my_custom_group"
    assert root_schema.is_group is True
    assert CommandName("sub") in root_schema.subcommands

    sub_schema = root_schema.subcommands[CommandName("sub")]
    assert sub_schema.name == "sub"
    assert sub_schema.parent == root_schema
    assert [s.name for s in sub_schema.path_from_root] == ["my_custom_group", "sub"]


def test_introspect_click_group_function_name():
    @click.group()
    def sample_cli():
        pass

    @sample_cli.command()
    def process():
        pass

    data = introspect_click_app(sample_cli)
    expected_name = CommandName(sample_cli.name)
    assert expected_name in data
    root_schema = data[expected_name]
    assert root_schema.name == sample_cli.name
    assert root_schema.is_group is True
    assert CommandName("process") in root_schema.subcommands


def test_introspect_click_group_nameless_fallback():
    group = click.Group()

    @group.command("test_cmd")
    def test_cmd():
        pass

    data = introspect_click_app(group)
    assert CommandName("root") in data
    root_schema = data[CommandName("root")]
    assert root_schema.name == "root"
    assert CommandName("test_cmd") in root_schema.subcommands


def test_introspect_click_command():
    @click.command("run_task")
    def run_task():
        pass

    data = introspect_click_app(run_task)
    assert CommandName("run_task") in data
    assert data[CommandName("run_task")].name == "run_task"
    assert data[CommandName("run_task")].is_group is False

import click
import pytest

from trogon.introspect import (
    CommandSchema,
    OptionSchema,
    ArgumentSchema,
    CommandName, MultiValueParamData,
)
from trogon.run_command import UserCommandData, UserOptionData, UserArgumentData


@pytest.fixture
def command_schema():
    return CommandSchema(
        name=CommandName("test"),
        arguments=[
            ArgumentSchema(name="arg1", type=click.INT, required=False, default=MultiValueParamData([(123,)])),
        ],
        options=[
            OptionSchema(
                name=["--option1"], type=click.STRING, required=False, default=MultiValueParamData([("default1",)])
            ),
            OptionSchema(
                name=["--option2"], type=click.INT, required=False, default=MultiValueParamData([(42,)])
            ),
        ],
        subcommands={},
        function=lambda: 1,
    )


@pytest.fixture
def command_schema_with_subcommand(command_schema):
    command_schema.subcommands = {
        "sub": CommandSchema(
            name=CommandName("sub"),
            options=[
                OptionSchema(
                    name=["--sub-option"], type=click.BOOL, required=False, default=MultiValueParamData([(False,)])
                )
            ],
            arguments=[],
            function=lambda: 2,
        )
    }
    return command_schema


@pytest.fixture
def user_command_data_no_subcommand():
    return UserCommandData(
        name=CommandName("test"),
        options=[
            UserOptionData(name="--option1", value=("value1",),
                           option_schema=OptionSchema(name=["--option1", "-o1"], type=click.STRING)),
            UserOptionData(name="--option2", value=("42",),
                           option_schema=OptionSchema(name=["--option2", "-o2"], type=click.STRING)),
        ],
        arguments=[
            UserArgumentData(name="arg1", value=("123",), argument_schema=ArgumentSchema("arg1", click.INT)),
        ],
    )


@pytest.fixture
def user_command_data_with_subcommand(user_command_data_no_subcommand):
    return UserCommandData(
        name=CommandName("test"),
        options=user_command_data_no_subcommand.options,
        arguments=user_command_data_no_subcommand.arguments,
        subcommand=UserCommandData(
            name=CommandName("sub"),
            options=[
                UserOptionData(name="--sub-option", value=("True",),
                               option_schema=OptionSchema(name=["--sub-option"], type=click.BOOL))
            ],
            arguments=[],
        ),
    )


def test_to_cli_args_no_subcommand(user_command_data_no_subcommand):
    cli_args = user_command_data_no_subcommand.to_cli_args(True)
    assert cli_args == ["test", "--option1", "value1", "--option2", "42", "123"]


def test_to_cli_args_with_subcommand(user_command_data_with_subcommand):
    cli_args = user_command_data_with_subcommand.to_cli_args(True)
    assert cli_args == [
        "test",
        "--option1",
        "value1",
        "--option2",
        "42",
        "123",
        "sub",
        "--sub-option",
        "True",
    ]


def test_to_cli_string_no_subcommand(user_command_data_no_subcommand):
    cli_string = user_command_data_no_subcommand.to_cli_string(True)

    assert cli_string.plain == "test --option1 value1 --option2 42 123"


def test_to_cli_string_with_subcommand(user_command_data_with_subcommand):
    cli_string = user_command_data_with_subcommand.to_cli_string(True)

    assert cli_string.plain == "test --option1 value1 --option2 42 123 sub --sub-option True"

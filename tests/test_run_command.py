import pytest

from trogon.schemas import (
    ArgumentSchema,
    CommandName,
    CommandSchema,
    MultiValueParamData,
    OptionSchema,
)
from trogon.run_command import UserCommandData, UserOptionData, UserArgumentData


@pytest.fixture
def command_schema():
    return CommandSchema(
        name=CommandName("test"),
        arguments=[
            ArgumentSchema(
                name="arg1",
                type=int,
                required=False,
                default=MultiValueParamData([(123,)]),
            ),
        ],
        options=[
            OptionSchema(
                name=["--option1"],
                type=str,
                required=False,
                default=MultiValueParamData([("default1",)]),
            ),
            OptionSchema(
                name=["--option2"],
                type=int,
                required=False,
                default=MultiValueParamData([(42,)]),
            ),
        ],
        subcommands={},
    )


@pytest.fixture
def command_schema_with_subcommand(command_schema):
    command_schema.subcommands = {
        "sub": CommandSchema(
            name=CommandName("sub"),
            options=[
                OptionSchema(
                    name=["--sub-option"],
                    type=bool,
                    required=False,
                    default=MultiValueParamData([(False,)]),
                )
            ],
            arguments=[],
        )
    }
    return command_schema


@pytest.fixture
def user_command_data_no_subcommand():
    return UserCommandData(
        name=CommandName("test"),
        options=[
            UserOptionData(
                name="--option1",
                value=("value1",),
                option_schema=OptionSchema(name=["--option1", "-o1"], type=str),
            ),
            UserOptionData(
                name="--option2",
                value=("42",),
                option_schema=OptionSchema(name=["--option2", "-o2"], type=str),
            ),
        ],
        arguments=[
            UserArgumentData(
                name="arg1",
                value=("123",),
                argument_schema=ArgumentSchema("arg1", int),
            ),
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
                UserOptionData(
                    name="--sub-option",
                    value=("True",),
                    option_schema=OptionSchema(name=["--sub-option"], type=bool),
                )
            ],
            arguments=[],
        ),
    )


def test_to_cli_args_no_subcommand(user_command_data_no_subcommand):
    cli_args = user_command_data_no_subcommand.to_cli_args(True)
    assert cli_args == ["test", "123", "--option1", "value1", "--option2", "42"]


def test_to_cli_args_with_subcommand(user_command_data_with_subcommand):
    cli_args = user_command_data_with_subcommand.to_cli_args(True)
    assert cli_args == [
        "test",
        "123",
        "--option1",
        "value1",
        "--option2",
        "42",
        "sub",
        "--sub-option",
        "True",
    ]


def test_to_cli_string_no_subcommand(user_command_data_no_subcommand):
    cli_string = user_command_data_no_subcommand.to_cli_string(True)

    assert cli_string.plain == "test 123 --option1 value1 --option2 42"


def test_to_cli_string_with_subcommand(user_command_data_with_subcommand):
    cli_string = user_command_data_with_subcommand.to_cli_string(True)

    assert (
        cli_string.plain
        == "test 123 --option1 value1 --option2 42 sub --sub-option True"
    )

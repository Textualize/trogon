import pytest

from textual_click.introspect import CommandSchema, OptionSchema, ArgumentSchema, CommandName
from textual_click.run_command import UserCommandData, UserOptionData, UserArgumentData


@pytest.fixture
def command_schema():
    return CommandSchema(
        name=CommandName("test"),
        arguments=[
            ArgumentSchema(name="arg1", type="int", required=False, default=123),
        ],
        options=[
            OptionSchema(name="option1", type="text", required=False, default="default1"),
            OptionSchema(name="option2", type="int", required=False, default=42),
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
                OptionSchema(name="sub_option", type="bool", required=False, default=False)
            ],
            arguments=[],
            function=lambda: 2,
        )
    }
    return command_schema


@pytest.fixture
def user_command_data_no_subcommand():
    return UserCommandData(
        name="test",
        options=[
            UserOptionData(name="option1", value="value1"),
            UserOptionData(name="option2", value="42"),
        ],
        arguments=[
            UserArgumentData(name="arg1", value=123),
        ],
    )


@pytest.fixture
def user_command_data_with_subcommand(user_command_data_no_subcommand):
    return UserCommandData(
        name="test",
        options=user_command_data_no_subcommand.options,
        arguments=user_command_data_no_subcommand.arguments,
        subcommand=UserCommandData(
            name="sub",
            options=[UserOptionData(name="sub_option", value="True")],
            arguments=[],
        ),
    )


def test_prefill_defaults_no_subcommand(command_schema):
    user_command_data = UserCommandData(name="test", options=[], arguments=[])

    user_command_data.fill_defaults(command_schema)

    assert len(user_command_data.options) == 2

    # We've prefilled the default arguments inside the UserOptionData with defaults.
    assert user_command_data.options[0] == UserOptionData(name="option1", value="default1")
    assert user_command_data.options[1] == UserOptionData(name="option2", value=42)
    assert len(user_command_data.arguments) == 1
    assert user_command_data.arguments[0] == UserArgumentData(name="arg1", value=123)
    assert user_command_data.subcommand is None


def test_prefill_defaults_with_subcommand(command_schema):
    test_subcommand_schema = CommandSchema(
        name=CommandName("sub"),
        options=[
            OptionSchema(name="sub_option", type="boolean", required=False, default=True),
        ],
        arguments=[],
        subcommands={},
        function=lambda: 1,
    )

    command_schema.subcommands = {CommandName("sub"): test_subcommand_schema}

    user_command_data = UserCommandData(
        name="test",
        options=[],
        arguments=[],
        subcommand=UserCommandData(name="sub", options=[], arguments=[]),
    )

    user_command_data.fill_defaults(command_schema)

    assert len(user_command_data.options) == 2
    assert user_command_data.options[0] == UserOptionData(name="option1", value="default1")
    assert user_command_data.options[1] == UserOptionData(name="option2", value=42)
    assert len(user_command_data.arguments) == 1
    assert user_command_data.arguments[0] == UserArgumentData(name="arg1", value=123)
    assert user_command_data.subcommand is not None
    assert len(user_command_data.subcommand.options) == 1
    assert user_command_data.subcommand.options[0] == UserOptionData(name="sub_option", value=True)
    assert len(user_command_data.subcommand.arguments) == 0


def test_to_cli_args_no_subcommand(user_command_data_no_subcommand):
    cli_args = user_command_data_no_subcommand.to_cli_args()
    assert cli_args == ["test", "--option1", "value1", "--option2", "42", "123"]


def test_to_cli_args_with_subcommand(user_command_data_with_subcommand):
    cli_args = user_command_data_with_subcommand.to_cli_args()
    assert cli_args == [
        "test",
        "--option1",
        "value1",
        "--option2",
        "42",
        "123",
        "sub",
        "--sub_option",
        "True",
    ]


def test_to_cli_string_no_subcommand(user_command_data_no_subcommand):
    cli_string = user_command_data_no_subcommand.to_cli_string()

    assert cli_string == "test --option1 value1 --option2 42 123"


def test_to_cli_string_with_subcommand(user_command_data_with_subcommand):
    cli_string = user_command_data_with_subcommand.to_cli_string()

    assert cli_string == "test --option1 value1 --option2 42 123 sub --sub_option True"

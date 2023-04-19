from textual_click.introspect import CommandSchema, OptionSchema, ArgumentSchema, CommandName
from textual_click.run_command import UserCommandData, UserOptionData, UserArgumentData

# Test data
test_command_schema = CommandSchema(
    name=CommandName("test"),
    options=[
        OptionSchema(name="option1", type="text", required=False, default="default1"),
        OptionSchema(name="option2", type="int", required=False, default=42),
    ],
    arguments=[
        ArgumentSchema(name="arg1", type="text", required=False, default="arg_default1"),
    ],
    subcommands={},
    function=lambda: 1,
)


def test_prefill_defaults_no_subcommand():
    user_command_data = UserCommandData(name="test", options=[], arguments=[])

    user_command_data.prefill_defaults(test_command_schema)

    assert len(user_command_data.options) == 2

    # We've prefilled the default arguments inside the UserOptionData with defaults.
    assert user_command_data.options[0] == UserOptionData(name="option1", value="default1")
    assert user_command_data.options[1] == UserOptionData(name="option2", value=42)
    assert len(user_command_data.arguments) == 1
    assert user_command_data.arguments[0] == UserArgumentData(name="arg1", value="arg_default1")
    assert user_command_data.subcommand is None


def test_prefill_defaults_with_subcommand():
    test_subcommand_schema = CommandSchema(
        name=CommandName("sub"),
        options=[
            OptionSchema(name="sub_option", type=bool, required=False, default=True),
        ],
        arguments=[],
        subcommands={},
        function=lambda: 1,
    )

    test_command_schema.subcommands = {CommandName("sub"): test_subcommand_schema}

    user_command_data = UserCommandData(
        name="test",
        options=[],
        arguments=[],
        subcommand=UserCommandData(name="sub", options=[], arguments=[]),
    )

    user_command_data.prefill_defaults(test_command_schema)

    assert len(user_command_data.options) == 2
    assert user_command_data.options[0] == UserOptionData(name="option1", value="default1")
    assert user_command_data.options[1] == UserOptionData(name="option2", value=42)
    assert len(user_command_data.arguments) == 1
    assert user_command_data.arguments[0] == UserArgumentData(name="arg1", value="arg_default1")
    assert user_command_data.subcommand is not None
    assert len(user_command_data.subcommand.options) == 1
    assert user_command_data.subcommand.options[0] == UserOptionData(name="sub_option", value=True)
    assert len(user_command_data.subcommand.arguments) == 0

import click

from trogon.introspect import MultiValueParamData, introspect_click_app


def test_option_with_no_default_does_not_leak_click_sentinel():
    @click.command()
    @click.option("--path", type=click.Path())
    def cli(path):
        pass

    data = introspect_click_app(cli)
    option = data["cli"].options[0]

    assert option.default == MultiValueParamData([])


def test_argument_with_no_default_does_not_leak_click_sentinel():
    @click.command()
    @click.argument("path", type=click.Path(), required=False)
    def cli(path):
        pass

    data = introspect_click_app(cli)
    argument = data["cli"].arguments[0]

    assert argument.default == MultiValueParamData([])


def test_option_with_explicit_default_is_preserved():
    @click.command()
    @click.option("--name", type=click.STRING, default="trogon")
    def cli(name):
        pass

    data = introspect_click_app(cli)
    option = data["cli"].options[0]

    assert option.default == MultiValueParamData([("trogon",)])

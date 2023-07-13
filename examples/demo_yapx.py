#!/usr/bin/env python3

import yapx


def hello(name):
    print(f"Hello {name}")


def goodbye(name, formal=False):
    if formal:
        print(f"Goodbye Ms. {name}. Have a good day.")
    else:
        print(f"Bye {name}!")


if __name__ == "__main__":
    yapx.run_commands([hello, goodbye])

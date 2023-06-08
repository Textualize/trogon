from myke import task

@task(root=True)
def setup(log_level="info"):
    print(f"Log level: {log_level}")

@task
def hello(name):
    print(f"Hello {name}")

@task
def goodbye(name, formal=False):
    if formal:
        print(f"Goodbye Ms. {name}. Have a good day.")
    else:
        print(f"Bye {name}!")


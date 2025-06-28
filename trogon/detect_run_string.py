from __future__ import annotations

import os
import sys
from types import ModuleType

import oslex


def get_orig_argv() -> list[str]:
    """Polyfil for orig_argv"""
    if hasattr(sys, "orig_argv"):
        return sys.orig_argv
    import ctypes

    _argv = ctypes.POINTER(ctypes.c_wchar_p)()
    _argc = ctypes.c_int()

    ctypes.pythonapi.Py_GetArgcArgv(ctypes.byref(_argc), ctypes.byref(_argv))

    argv = _argv[: _argc.value]
    return argv


def detect_run_string(_main: ModuleType = sys.modules["__main__"]) -> str:
    """Determine the command used to run the program, for use in preview text only.

    This doesn't try to be too precise.
    This is a slightly modified version of a function from Click.
    """
    path = sys.argv[0]

    # The value of __package__ indicates how Python was called. It may
    # not exist if a setuptools script is installed as an egg. It may be
    # set incorrectly for entry points created with pip on Windows.
    if getattr(_main, "__package__", None) is None or (
        os.name == "nt"
        and _main.__package__ == ""
        and not os.path.exists(path)
        and os.path.exists(f"{path}.exe")
    ):
        # Executed a file, like "python app.py".
        file_path = oslex.quote(os.path.basename(path))
        argv = get_orig_argv()
        if argv[0] == "python":
            prefix = f"{argv[0]} "
        else:
            prefix = ""
        return f"{prefix}{file_path}"

    # Executed a module, like "python -m example".
    # Rewritten by Python from "-m script" to "/path/to/script.py".
    # Need to look at main module to determine how it was executed.
    py_module = _main.__package__
    name = os.path.splitext(os.path.basename(path))[0]

    # A submodule like "example.cli".
    if name != "__main__":
        py_module = f"{py_module}.{name}"

    return f"python -m {py_module.lstrip('.')}"


def exact_run_commands() -> list[str]:
    """Get the calling command to re-execute it as it was called originally."""
    num_of_script_args = len(sys.argv) - 1
    # sys.orig_argv is nearly perfect, just contain a wrong interpreter in case of a venv
    calling_command_args = get_orig_argv()[1:-num_of_script_args]
    return [sys.executable, *calling_command_args]

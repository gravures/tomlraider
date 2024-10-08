#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
#
# Copyright (c) 2024 - Gilles Coissac
#
# tomlraider is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# tomlraider is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with tomlraider. If not, see <https://www.gnu.org/licenses/>
#
"""Retrieve properties from toml files."""

from __future__ import annotations

import argparse
import fileinput
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from deluxe.console import PrettyParser

from tomlraider._version import __version__
from tomlraider.core import (
    PATH_SEPARATOR,
    Output,
    TOMLDecodeError,
    TOMLLookUpError,
    TOMLPathFormatError,
    dumps,
    join_path,
    parse_path,
    read_toml,
)


if TYPE_CHECKING:
    from collections.abc import Sequence

    from tomlraider.core import TomlAtomicType, TomlContainerType


PROG_NAME = "tomlraider"


def _message(value: str, quiet: bool) -> None:
    if quiet:
        return
    sys.stderr.write(f"{PROG_NAME}: {value}\n")


class _CLIError(Exception):
    _error_codes: ClassVar[dict[type[BaseException], int]] = {
        SystemExit: 0,
        Exception: 1,
        TOMLDecodeError: 2,
        TOMLPathFormatError: 3,
        TOMLLookUpError: 4,
        KeyError: 5,
        IndexError: 6,
    }

    def __init__(self, msg: str | None, quiet: bool, _from: BaseException | None = None) -> None:
        self.msg: str = msg or ""
        self.quiet: bool = quiet
        self.code: int = self._error_codes.get(type(_from), 1) if _from else 1
        super().__init__()


def _get_parser() -> argparse.ArgumentParser:
    parser = PrettyParser(
        prog=PROG_NAME,
        version=__version__,
        prefix=f"{PROG_NAME} {__version__}",
        exit_on_error=False,
        shell_completion=True,
    )
    parser.add_argument(
        "-j",
        "--json",
        dest="json",
        action="store_true",
        help="output property as a json string",
    )
    exclusive = parser.add_mutually_exclusive_group()
    exclusive.add_argument(
        "-p",
        "--pyproject",
        dest="pyproject",
        action="store_true",
        help="looks for a pyproject.toml file in the current\n"
        "directory or MESON_SOURCE_ROOT if set",
    )
    exclusive.add_argument(
        "-f",
        "--file",
        dest="file",
        action="store",
        default=None,
        help="toml file to read from ('-' for stdin)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        dest="quiet",
        action="store_true",
        help="don't print any message to stderr",
    )
    parser.add_argument(
        "property",
        action="store",
        help="property to retrieve from toml file",
    )
    return parser


def _parse_argv(
    parser: argparse.ArgumentParser, argv: Sequence[str] | None = None
) -> argparse.Namespace:
    try:
        params: argparse.Namespace = parser.parse_args(argv)
    except (argparse.ArgumentError, argparse.ArgumentTypeError) as e:
        raise _CLIError(msg=str(e), quiet=False) from None
    except SystemExit as e:
        raise _CLIError(msg=None, quiet=False, _from=e) from None

    try:
        params.property_path = parse_path(params.property)
    except TOMLPathFormatError as e:
        raise _CLIError(e.msg, params.quiet, e) from None
    params.output = Output.JSON if params.json else Output.SHELL

    # Verify input file
    if params.pyproject:
        # looking for a <pyproject.toml> file
        meson_root = os.environ.get("MESON_SOURCE_ROOT", None)
        root: Path = Path(meson_root) if meson_root else Path.cwd()
        tmp = root / "pyproject.toml"
        if not tmp.exists():
            raise _CLIError(msg="<pyproject.toml> file not found", quiet=params.quiet)
        params.file = str(tmp)
    elif params.file not in {"-", None} and not Path(str(params.file)).exists():
        raise _CLIError(msg=f"File not found: {params.file}", quiet=params.quiet)
    return params


def _read_buffer(params: argparse.Namespace) -> str:
    # Format sys.argv for fileinput module
    # FIXME: - main called from python
    #        - what when argparse exit by itself
    sys.argv = [sys.argv[0]]
    if params.file:
        sys.argv.append(params.file)

    with fileinput.input(mode="r", encoding="utf-8") as _file:
        file_name = params.file or "stdin"
        _message(
            f"Reading property <{join_path(params.property_path)}> from <{file_name}>...\n",
            params.quiet,
        )
        return "".join(list(_file))


def _parse_request(buffer: str, params: argparse.Namespace) -> None:
    try:
        value: TomlAtomicType | TomlContainerType = read_toml(buffer, params.property_path)
    except TOMLDecodeError as e:
        msg = f"error decoding <{params.file_name}>, {e}"
        raise _CLIError(msg, params.quiet, e) from None
    except TOMLLookUpError as e:
        raise _CLIError(e.msg, params.quiet, e) from None
    else:
        sys.stdout.write(
            dumps(value=value, output=params.output, path=params.property.strip(PATH_SEPARATOR))
        )


def main(*args: str) -> int:  # noqa: D417
    """Entry point of the program.

    Args:
        Command line arguments.

    Returns:
        The exit code of the program.
    """
    try:
        parser = _get_parser()
        params = _parse_argv(parser, argv=args or None)
        buffer = _read_buffer(params)
        _parse_request(buffer, params)
    except _CLIError as e:
        if e.msg:
            _message(value=e.msg, quiet=e.quiet)
        return e.code
    return 0


if __name__ == "__main__":
    sys.exit(main())

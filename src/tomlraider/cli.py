#!/usr/bin/env python3
"""Retrieve properties from toml files."""

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

from __future__ import annotations

import argparse
import fileinput
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from tomlraider._version import __version__
from tomlraider.core import (
    PATH_SEPARTOR,
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
    from collections.abc import Iterable, Sequence

    from tomlraider.core import TomlAtomicType, TomlContainerType, TomlPath


PROG_NAME = "tomlraider"
DOC = __doc__


def _message(value: str, quiet: bool) -> None:
    if quiet:
        return
    sys.stderr.write(f"{PROG_NAME}: {value}\n")


class _CLIError(Exception):
    _error_codes: ClassVar[dict[type[Exception], int]] = {
        TOMLDecodeError: 2,
        TOMLPathFormatError: 3,
        TOMLLookUpError: 4,
        KeyError: 5,
        IndexError: 6,
    }

    def __init__(self, msg: str, quiet: bool, _from: Exception | None = None) -> None:
        self.msg: str = msg
        self.quiet: bool = quiet
        self.code: int = self._error_codes.get(type(_from), 1) if _from else 1
        super().__init__()


class _HelpFormatter(argparse.HelpFormatter):
    def add_usage(
        self,
        usage: str | None,
        actions: Iterable[argparse.Action],
        groups: Iterable[argparse._MutuallyExclusiveGroup],  # type: ignore[reportPrivateUsage]
        prefix: str | None = None,
    ) -> None:
        if prefix is None:
            prefix = f"{PROG_NAME} {__version__}\n{DOC}\n\nUsage: "
        return super().add_usage(usage, actions, groups, prefix)


def _parse_argv(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog=PROG_NAME,
        formatter_class=_HelpFormatter,
    )
    parser.add_argument(
        "property",
        action="store",
        help="property to retrieve from toml file",
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
        "-v",
        "--version",
        action="version",
        version=f"{PROG_NAME} {__version__}",
        help="print version and exit",
    )

    args: argparse.Namespace = parser.parse_args(argv)
    try:
        property_path: TomlPath = parse_path(args.property)
    except TOMLPathFormatError as e:
        raise _CLIError(e.msg, args.quiet, e) from None
    output: Output = Output.JSON if args.json else Output.SHELL
    input_file: str | None = args.file

    # Verify input file
    if args.pyproject:
        # looking for a <pyproject.toml> file
        meson_root = os.environ.get("MESON_SOURCE_ROOT", None)
        root: Path = Path(meson_root) if meson_root else Path.cwd()
        tmp = root / "pyproject.toml"
        if not tmp.exists():
            raise _CLIError(msg="<pyproject.toml> file not found", quiet=args.quiet)
        input_file = str(tmp)
    elif input_file not in {"-", None} and not Path(str(input_file)).exists():
        raise _CLIError(msg=f"File not found: {input_file}", quiet=args.quiet)

    # Format sys.argv for fileinput module
    # FIXME: - main called from python
    #        - what when argparse exit by itself
    sys.argv = [sys.argv[0]]
    if input_file:
        sys.argv.append(input_file)

    with fileinput.input(mode="r", encoding="utf-8") as _file:
        file_name = input_file or "stdin"
        _message(
            f"Reading property <{join_path(property_path)}> from <{file_name}>...\n",
            args.quiet,
        )
        buffer = "".join(list(_file))

    try:
        value: TomlAtomicType | TomlContainerType = read_toml(buffer, property_path)
    except TOMLDecodeError as e:
        msg = f"error decoding <{file_name}>, {e}"
        raise _CLIError(msg, args.quiet, e) from None
    except TOMLLookUpError as e:
        raise _CLIError(e.msg, args.quiet, e) from None
    else:
        sys.stdout.write(
            dumps(value=value, output=output, path=args.property.strip(PATH_SEPARTOR))
        )


def main(*args: str) -> int:
    """Entry point of the program.

    - Args:
        - *args (str): Command line arguments.

    - Returns:
        - int: The exit code of the program.
    """
    try:
        _parse_argv(args)
    except _CLIError as e:
        _message(value=e.msg, quiet=e.quiet)
        return e.code
    return 0


if __name__ == "__main__":
    sys.exit(main())

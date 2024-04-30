#!/usr/bin/env python3
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

"""Retrieve properties from toml files."""

from __future__ import annotations

import argparse
import enum
import fileinput
import json
import os
import re
import sys
import tomllib
from datetime import date, datetime, time
from pathlib import Path
from typing import TYPE_CHECKING, NewType, TypeAlias

from tomlraider._version import __version__


if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


PROG_NAME = "tomlraider"
PATH_SEPARTOR = "."
SHELL_LIST_SEPARATOR = " "
DOC = __doc__


@enum.unique
class Output(enum.Enum):
    """Output formats supported by the application.

    The `Output` enum defines the available output formats
    that the application can produce. The `SHELL` format is used
    for human-readable output in a terminal, while the `JSON`
    format is used for machine-readable output.
    """

    SHELL = enum.auto()
    JSON = enum.auto()


TomlAtomicType: TypeAlias = bool | str | int | float | datetime | date | time
TomlContainerType: TypeAlias = "dict[str, TomlType] | list[TomlType]"
TomlType: TypeAlias = TomlAtomicType | TomlContainerType

TomlIndex = NewType("TomlIndex", int)
TomlKey = NewType("TomlKey", str)
TomlPathPart: TypeAlias = TomlKey | TomlIndex
TomlPath: TypeAlias = list[TomlPathPart]


class _TomlContainer:
    """Generic Toml container."""

    __slots__ = ("real",)

    def __init__(self, container: TomlContainerType) -> None:
        super().__init__()
        self.real = container

    def __getitem__(self, key: TomlPathPart) -> TomlAtomicType | TomlContainerType:
        if isinstance(self.real, list) and isinstance(key, int):
            return self.real[key]
        if isinstance(self.real, dict) and isinstance(key, str):
            return self.real[key]
        raise TypeError


def read_toml(buffer: str, path: TomlPath) -> TomlAtomicType | TomlContainerType:
    """Returns property from a toml string buffer."""
    root = tomllib.loads(buffer)
    locations: list[_TomlContainer] = [_TomlContainer(root)]

    if not path:
        return root

    if isinstance(path[0], int):
        msg = "first part of a path can't be an index, toml's root is always a Table"
        raise TypeError(msg)

    for part in path[:-1]:
        loc: _TomlContainer = locations[-1]
        if isinstance(loc[part], (dict, list)):
            locations.append(_TomlContainer(loc[part]))  # type: ignore[rerportAssignmentType]
            continue

        msg = "any atomic value are only valid for the last part of a path"
        raise TypeError(msg)

    return locations[-1][path[-1]]


def _dumps(value: TomlType, output: Output, path: str) -> str:
    if output is Output.JSON:
        return json.dumps(value)

    match value:
        case bool():
            ret = "1" if value else "0"
        case str() | int() | float():
            ret = str(value)
        case datetime():
            ret = str(value)
        case time():
            ret = str(value)
        case list():
            ret = SHELL_LIST_SEPARATOR.join(map(str, value))
        case dict():
            ret = f"{PATH_SEPARTOR}{path}"
        case _:
            # should never happened
            msg = f"Unsupported type: {type(value)}"
            raise NotImplementedError(msg)
    return ret


def _validate_key(key: str) -> bool:
    try:
        tomllib.loads(f"{key}='test'")
    except tomllib.TOMLDecodeError:
        return False
    else:
        return True


def _look_for_key_indice(key: str) -> tuple[str, str] | None:
    regex: re.Pattern[str] = re.compile(r"^(.+)\[(-?\d*)\]$")
    if match := regex.match(key):
        _key, _index = match.groups()
        return (_key, _index) if _validate_key(_key) else None
    return None


def parse_path(path: str) -> TomlPath:
    """Parses a path string into a list of keys."""
    out: TomlPath = []
    for part in path.split(PATH_SEPARTOR):
        if not part:
            continue
        if _validate_key(part):
            out.append(TomlKey(part))
        elif search := _look_for_key_indice(part):
            out.extend((TomlKey(search[0]), TomlIndex(int(search[1]))))
        else:
            msg = f"Invalid key: {part}"
            raise _CliError(msg, quiet=False) from None  # FIXME: quiet=False
    return out


def join_path(path: TomlPath) -> str:
    """Join a TomlPath into a string."""
    return PATH_SEPARTOR.join(map(str, path))


def _cli_message(value: str, quiet: bool) -> None:
    if quiet:
        return
    sys.stderr.write(f"{PROG_NAME}: {value}\n")


class _CliError(Exception):
    def __init__(self, msg: str, quiet: bool, code: int = 1) -> None:
        self.msg: str = msg
        self.quiet: bool = quiet
        self.code: int = code
        super().__init__()


class _CliHelpFormatter(argparse.HelpFormatter):
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


def _cli_parse_argv(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog=PROG_NAME,
        formatter_class=_CliHelpFormatter,
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
    property_path: TomlPath = parse_path(args.property)
    output: Output = Output.JSON if args.json else Output.SHELL
    input_file: str | None = args.file

    # Verify input file
    if args.pyproject:
        # looking for a <pyproject.toml> file
        meson_root = os.environ.get("MESON_SOURCE_ROOT", None)
        root: Path = Path(meson_root) if meson_root else Path.cwd()
        tmp = root / "pyproject.toml"
        if not tmp.exists():
            raise _CliError(msg="<pyproject.toml> file not found", quiet=args.quiet, code=1)
        input_file = str(tmp)
    elif input_file not in {"-", None} and not Path(str(input_file)).exists():
        raise _CliError(msg=f"File not found: {input_file}", quiet=args.quiet, code=1)

    # Format sys.argv for fileinput module
    # FIXME: - main called from python
    #        - what when argparse exit by itself
    sys.argv = [sys.argv[0]]
    if input_file:
        sys.argv.append(input_file)

    with fileinput.input(mode="r", encoding="utf-8") as _file:
        file_name = input_file or "stdin"
        _cli_message(
            f"Reading property <{join_path(property_path)}> from <{file_name}>...\n",
            args.quiet,
        )
        buffer = "".join(list(_file))

    try:
        value: TomlAtomicType | TomlContainerType = read_toml(buffer, property_path)
    except tomllib.TOMLDecodeError as e:
        raise _CliError(msg=f"error decoding <{file_name}>, {e}", quiet=args.quiet, code=1) from e
    except AttributeError:
        raise _CliError(
            msg=f"error reading property <{args.property}>, <{property_path[-2]}> is not a table",
            quiet=args.quiet,
            code=1,
        ) from None
    else:
        sys.stdout.write(
            _dumps(value=value, output=output, path=args.property.strip(PATH_SEPARTOR))
        )


def main(*args: str) -> int:
    """Entry point of the program.

    - Args:
        - *args (str): Command line arguments.

    - Returns:
        - int: The exit code of the program.
    """
    try:
        _cli_parse_argv(args)
    except _CliError as e:
        _cli_message(value=e.msg, quiet=e.quiet)
        return e.code
    return 0


if __name__ == "__main__":
    sys.exit(main())

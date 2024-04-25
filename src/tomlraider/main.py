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
import datetime
import enum
import fileinput
import json
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn, TypeAlias

import tomllib

from tomlraider._version import __version__


if TYPE_CHECKING:
    from collections.abc import Iterable


PATH_SEPARTOR = "."
DOC = __doc__

Toml_T: TypeAlias = (
    None
    | bool
    | str
    | int
    | float
    | datetime.datetime
    | datetime.date
    | datetime.time
    | list[Any]
    | dict[str, Any]
)


@enum.unique
class Output(enum.Enum):
    SHELL = enum.auto()
    JSON = enum.auto()


def message(value: str, quiet: bool) -> None:
    if quiet:
        return
    me = Path(__file__).name
    print(f"{me}: {value}", file=sys.stderr)


def exit_with_error(mesg: str, quiet: bool) -> NoReturn:
    message(mesg, quiet)
    sys.exit(1)


def parse_path(path: str) -> list[str]:
    """Parses a path string into a list of keys."""
    return [part for part in path.split(PATH_SEPARTOR) if part]


def read_toml(buffer: str, path: list[str]) -> Toml_T:
    """Returns property from a toml string buffer."""
    toml_loc = tomllib.loads(buffer)
    if not path:
        return toml_loc
    for entry in path[:-1]:
        toml_loc = toml_loc.get(entry, None)
        if toml_loc is None:
            return None
    return toml_loc.get(path[-1], None)


def dumps(value: Toml_T, output: Output, path: str) -> str:
    if output is Output.JSON:
        return json.dumps(value)

    match value:
        case None:
            ret = "__null"
        case bool():
            ret = "1" if value else "0"
        case str() | int() | float():
            ret = str(value)
        case datetime.datetime():
            ret = str(value)
        case datetime.time():
            ret = str(value)
        case list():
            ret = " ".join(value)
        case dict():
            ret = f"{PATH_SEPARTOR}{path}"
        case _:
            # should never happened
            msg = f"Unsupported type: {type(value)}"
            raise NotImplementedError(msg)
    return ret


def main() -> NoReturn:
    class CapitalisedHelpFormatter(argparse.HelpFormatter):
        def add_usage(
            self,
            usage: str | None,
            actions: Iterable[argparse.Action],
            groups: Iterable[argparse._MutuallyExclusiveGroup],  # type: ignore[reportPrivateUsage]
            prefix: str | None = None,
        ) -> None:
            if prefix is None:
                prefix = f"{Path(__file__).stem} {__version__}\n{DOC}\n\nUsage: "
            return super().add_usage(usage, actions, groups, prefix)

    parser = argparse.ArgumentParser(
        prog=Path(__file__).stem,
        formatter_class=CapitalisedHelpFormatter,
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
        version=f"{Path(__file__).name} {__version__}",
        help="print version and exit",
    )

    args = parser.parse_args()
    property_path: list[str] = parse_path(args.property)
    output: Output = Output.JSON if args.json else Output.SHELL
    input_file: str | None = args.file

    # Verify input file
    if args.pyproject:
        # looking for a <pyproject.toml> file
        meson_root = os.environ.get("MESON_SOURCE_ROOT", None)
        root: Path = Path(meson_root) if meson_root else Path.cwd()
        tmp = root / "pyproject.toml"
        if not tmp.exists():
            exit_with_error("<pyproject.toml> file not found", args.quiet)
        input_file = str(tmp)
    elif input_file not in {"-", None} and not Path(str(input_file)).exists():
        exit_with_error(f"File not found: {input_file}", args.quiet)

    # Format sys.argv for fileinput module
    sys.argv = [sys.argv[0]]
    if input_file:
        sys.argv.append(input_file)

    with fileinput.input(mode="r", encoding="utf-8") as _file:
        file_name = input_file or "stdin"
        message(
            f"Reading property <{'.'.join(property_path)}> from <{file_name}>...\n",
            args.quiet,
        )
        buffer = "".join(list(_file))

    try:
        value: Toml_T = read_toml(buffer, property_path)
    except tomllib.TOMLDecodeError as e:
        exit_with_error(f"error decoding <{file_name}>, {e}", args.quiet)
    except AttributeError:
        exit_with_error(
            f"error reading property <{args.property}>, <{property_path[-2]}> is not a table",
            args.quiet,
        )
    else:
        sys.stdout.write(
            dumps(value=value, output=output, path=args.property.strip(PATH_SEPARTOR))
        )
        sys.exit(0)


if __name__ == "__main__":
    main()

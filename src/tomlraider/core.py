"""Tomlraider core functions."""

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

import enum
import json
import re
import tomllib
from datetime import date, datetime, time
from tomllib import TOMLDecodeError as _TOMLDecodeError
from typing import NewType, TypeAlias


PATH_SEPARATOR = "."
SHELL_LIST_SEPARATOR = " "

TOMLDecodeError = _TOMLDecodeError


class TOMLPathFormatError(Exception):
    """An error raised if a TomlPath is invalid."""

    def __init__(self, msg: str) -> None:
        self.msg: str = msg
        super().__init__()


class TOMLLookUpError(Exception):
    """An error raised with a faulty Toml property access."""

    def __init__(self, msg: str) -> None:
        self.msg: str = msg
        super().__init__()


TomlAtomicType: TypeAlias = bool | str | int | float | datetime | date | time
TomlContainerType: TypeAlias = "dict[str, TomlType] | list[TomlType]"
TomlType: TypeAlias = "TomlAtomicType | TomlContainerType"

TomlIndex = NewType("TomlIndex", int)
TomlKey = NewType("TomlKey", str)
TomlPathPart: TypeAlias = TomlKey | TomlIndex
TomlPath: TypeAlias = list[TomlPathPart]


class TomlContainer:
    """Generic Toml container."""

    __slots__ = ("real",)

    def __init__(self, container: TomlContainerType) -> None:
        self.real = container

    def __getitem__(self, key: TomlPathPart) -> TomlAtomicType | TomlContainerType:
        if isinstance(self.real, list) and isinstance(key, int):
            return self.real[key]
        if isinstance(self.real, dict) and isinstance(key, str):
            return self.real[key]

        _t = "array" if isinstance(self.real, list) else "table"
        _i = "TomlKey" if isinstance(key, str) else "TomlIndex"
        msg = f"trying to access a Toml's {_t} with a {_i}"
        raise TOMLLookUpError(msg)


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


def read_toml(buffer: str, path: TomlPath) -> TomlAtomicType | TomlContainerType:
    """Returns property from a toml string buffer."""
    root = tomllib.loads(buffer)
    locations: list[TomlContainer] = [TomlContainer(root)]

    if not path:
        return root

    if isinstance(path[0], int):
        msg = "trying to address the Toml's global table with an index"
        raise TOMLLookUpError(msg)

    for part in path[:-1]:
        loc: TomlContainer = locations[-1]
        if isinstance(loc[part], (dict, list)):
            locations.append(
                TomlContainer(loc[part]),  # type: ignore[rerportAssignmentType]
            )
            continue

        # any atomic value are only valid for the last part of a path
        msg = f"trying to address an atomic Toml value, {type(loc[part])} is not subscriptable"
        raise TOMLLookUpError(msg)

    return locations[-1][path[-1]]


def _validate_key(key: str) -> bool:
    try:
        tomllib.loads(f"{key}='test'")
    except TOMLDecodeError:
        return False
    else:
        return True


# TODO: include slice pattern
def _look_for_key_indice(key: str) -> tuple[str, str] | None:
    regex: re.Pattern[str] = re.compile(r"^(.+)\[(-?\d*)\]$")
    if match := regex.match(key):
        _key, _index = match.groups()
        return (_key, _index) if _validate_key(_key) else None
    return None


def parse_path(path: str) -> TomlPath:
    """Parses a string into a TomlPath."""
    out: TomlPath = []
    for part in path.split(PATH_SEPARATOR):
        if not part:
            continue
        if _validate_key(part):
            out.append(TomlKey(part))
        elif search := _look_for_key_indice(part):
            out.extend((TomlKey(search[0]), TomlIndex(int(search[1]))))
        else:
            msg = f"Invalid key in TomlPath: {part}"
            raise TOMLPathFormatError(msg) from None
    return out


def join_path(path: TomlPath) -> str:
    """Join a TomlPath into a string."""
    out: list[str] = []
    for part in path:
        match part:
            case str():
                out.extend((PATH_SEPARATOR, part))
            case int():
                out.append(f"[{part}]")
    return "".join(out)


def dumps(value: TomlType, output: Output, path: str) -> str:
    """Return a string from a TomlType."""
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
            ret = f"{PATH_SEPARATOR}{path}"
        case _:
            # should never happened
            msg = f"Unsupported type: {type(value)}"
            raise NotImplementedError(msg)
    return ret

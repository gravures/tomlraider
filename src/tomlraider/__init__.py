# noqa: D104
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
from __future__ import annotations

from tomlraider._version import __version__
from tomlraider.cli import __doc__, main
from tomlraider.core import (
    PATH_SEPARATOR,
    SHELL_LIST_SEPARATOR,
    Output,
    TomlAtomicType,
    TomlContainerType,
    TOMLDecodeError,
    TomlIndex,
    TomlKey,
    TOMLLookUpError,
    TomlPath,
    TOMLPathFormatError,
    TomlPathPart,
    TomlType,
    join_path,
    parse_path,
    read_toml,
)


__all__ = [
    "PATH_SEPARATOR",
    "SHELL_LIST_SEPARATOR",
    "Output",
    "TOMLDecodeError",
    "TOMLLookUpError",
    "TOMLPathFormatError",
    "TomlAtomicType",
    "TomlContainerType",
    "TomlIndex",
    "TomlKey",
    "TomlPath",
    "TomlPathPart",
    "TomlType",
    "__doc__",
    "__version__",
    "join_path",
    "main",
    "parse_path",
    "read_toml",
]

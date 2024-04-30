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
# type: ignore[reportMissingTypeStubs]
#
# Testing data comes from https://github.com/toml-lang/toml-test
"""cases:

./tomlraider
./tomlraider project.name
./tomlraider project.name -f -
./tomlraider -f -
./tomlraider -f - .
./tomlraider -h
bin/toml -f installer/packages.toml .
cat  installer/packages.toml
bin/tomlraider -f installer/packages.toml .
cat  installer/packages.toml | bin/tomlraider .packaging.
cat  installer/packages.toml | bin/tomlraider packaging.
cat  installer/packages.toml | bin/tomlraider .packaging.apt
cat  installer/packages.toml | bin/tomlraider packaging.apt
cat  installer/packages.toml | bin/tomlraider packaging.flatpak
cat  installer/packages.toml | bin/tomlraider packaging
cat  installer/packages.toml | bin/tomlraider packaging.packages
cat  installer/packages.toml | bin/tomlraider packaging.packages.apt
cat  installer/packages. | bin/tomlraider .packaging.truc
cat  installer/packages.toml | bin/tomlraider .packaging.packages.apt.
cat  installer/install_helix.sh | bin/tomlraider .packaging.packages.apt.w
cat  installer/packages.toml | bin/tomlraider packaging.apt.w
cat  installer/packages.toml | bin/tomlraider .packaging.packages.apt.w
cat  installer/packages.toml | bin/tomlraider
./bin/tomlraider
./bin/tomlraider -h
cat  installer/packages.toml | bin/tomlraider .name -j
cat  installer/packages.toml | bin/tomlraider .packaging.packages.apt
cat  installer/packages.toml | bin/tomlraider .packaging.packages.apt -j
cat  installer/packages.toml | bin/tomlraider .packaging.name
cat  installer/packages.toml | bin/tomlraider version
cat  installer/packages.toml | bin/tomlraider test
cat  installer/packages.toml | bin/tomlraider .
cat  installer/packages.toml | bin/tomlraider .name
cat  installer/packages.toml | bin/tomlraider .packaging
cat  installer/packages.toml | bin/tomlraider .packaging.packages
cat  installer/packages.toml | bin/tomlraider .packaging.packages.apt -q
cat  installer/packages.toml | bin/tomlraider .source
cat  installer/packages.toml | bin/tomlraider .source.aptz.g

version: str = tomlraider.__version__
"""

from __future__ import annotations

import tomllib
from pathlib import Path

# from pprint import pprint
from typing import Any, Generator, TypeAlias

import pytest
import tree


# from hypothesis import given
# from hypothesis import strategies as st

# import tomlraider


TomlPathValue: TypeAlias = tuple[tuple[str, ...], Any]


def data_set() -> Generator:
    for _file in Path("tests/assets/valid/table").glob("*.toml"):
        with _file.open("r") as toml_file:
            buffer: str = toml_file.read()
            toml_str = tomllib.loads(buffer)
        yield (_file, tree.flatten_with_path(toml_str))


@pytest.mark.parametrize("toml_file,paths", data_set())  # noqa: PT006
def test_path_v0(toml_file: Path, paths: list[TomlPathValue]) -> None:
    print(f"\n{toml_file.name}")
    for p in paths:
        expected = p[0]  # ".".join(p[0])
        value = p[1]
        print(f"{expected} = {value}")

    # print(buffer)
    # pprint(toml_str)
    # print(tree.flatten(toml_str))

    # pprint(tree.flatten_with_path(toml_str))

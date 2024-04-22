import tomlraider

# ./tomlraider
# ./tomlraider project.name
# ./tomlraider project.name -f -
# ./tomlraider -f -
# ./tomlraider -f - .
# ./tomlraider -h
# cd ..
# ls
# bin/toml -f installer/packages.toml .
# cat  installer/packages.toml
# bin/tomlraider -f installer/packages.toml .
# cat  installer/packages.toml | bin/tomlraider .packaging.
# cat  installer/packages.toml | bin/tomlraider packaging.
# cat  installer/packages.toml | bin/tomlraider .packaging.apt
# cat  installer/packages.toml | bin/tomlraider packaging.apt
# cat  installer/packages.toml | bin/tomlraider packaging.flatpak
# cls
# cat  installer/packages.toml | bin/tomlraider packaging
# cat  installer/packages.toml | bin/tomlraider packaging.packages
# cat  installer/packages.toml | bin/tomlraider packaging.packages.apt
# cat  installer/packages. | bin/tomlraider .packaging.truc
# ipythoon
# ipython
# cat  installer/packages.toml | bin/tomlraider .packaging.packages.apt.
# cat  installer/install_helix.sh | bin/tomlraider .packaging.packages.apt.w
# cat  installer/packages.toml | bin/tomlraider packaging.apt.w
# cat  installer/packages.toml | bin/tomlraider .packaging.packages.apt.w
# cat  installer/packages.toml | bin/tomlraider
# ./bin/tomlraider
# ./bin/tomlraider -h
# cat  installer/packages.toml | bin/tomlraider .name -j
# cat  installer/packages.toml | bin/tomlraider .packaging.packages.apt
# cat  installer/packages.toml | bin/tomlraider .packaging.packages.apt -j
# cat  installer/packages.toml | bin/tomlraider .packaging.name
# cat  installer/packages.toml | bin/tomlraider version
# cat  installer/packages.toml | bin/tomlraider test
# cat  installer/packages.toml | bin/tomlraider .
# cat  installer/packages.toml | bin/tomlraider .name
# cat  installer/packages.toml | bin/tomlraider .packaging
# cat  installer/packages.toml | bin/tomlraider .packaging.packages
# cat  installer/packages.toml | bin/tomlraider .packaging.packages.apt -q
# cat  installer/packages.toml | bin/tomlraider .source
# cat  installer/packages.toml | bin/tomlraider .source.aptz.g

version: str = tomlraider.__version__

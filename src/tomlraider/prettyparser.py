"""Argument parser module."""

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
#
# NOTE: https://github.com/kislyuk/argcomplete
#       https://github.com/hamdanal/rich-argparse

from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess as sp
import sys
from typing import IO, TYPE_CHECKING, Any


try:
    from gettext import gettext as _
    from gettext import ngettext  # type:ignore[reportAssignmentType]
except ImportError:

    def _(message: str) -> str:
        return message

    def ngettext(singular: Any, plural: Any, n: int) -> Any:  # noqa: D103
        return singular if n == 1 else plural


if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


def which_shell() -> str | None:
    """Identify in which shell the current process is running on.

    Currently supported shell: bash, fish, zsh, powershell, gitbash.
    """
    if not all((sys.__stderr__, sys.__stdout__)):
        return None


class PrettyHelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawDescriptionHelpFormatter,
):
    """HelpFormatter."""

    def __init__(
        self,
        prog: str,
        metavar_typed: bool = False,
        indent_increment: int = 2,
        max_help_position: int = 24,
        width: int | None = None,
    ) -> None:
        super().__init__(prog, indent_increment, max_help_position, width)
        self.metavar_typed = metavar_typed

    def _format_usage(
        self,
        usage: str | None,
        actions: Iterable[argparse.Action],
        groups: Iterable[argparse._MutuallyExclusiveGroup],  # type:ignore[reportPrivateUsage]
        prefix: str | None,
    ) -> str:
        _usage: str = super()._format_usage(usage, actions, groups, None)
        return f"{prefix}\n\n{_usage}"

    def _get_default_metavar_for_optional(self, action: argparse.Action) -> str:
        if self.metavar_typed and hasattr(action, "type") and action.type:
            return action.type.__name__  # type: ignore[reportAttributeAccessIssue]
        return super()._get_default_metavar_for_optional(action)

    def _get_default_metavar_for_positional(self, action: argparse.Action) -> str:
        if self.metavar_typed and hasattr(action, "type") and action.type:
            return action.type.__name__  # type: ignore[reportAttributeAccessIssue]
        return super()._get_default_metavar_for_positional(action)


class PrettyParser(argparse.ArgumentParser):
    """Class for parsing command line strings into Python objects.

    Overrides print_usage(), print_help(), and error() to allow for explicit
    control over the format of a calling utility's description and usage strings.

    However, the description and usage_str fields are required.
    """

    def __init__(  # noqa: PLR0917
        self,
        prog: str,
        version: str | None = None,
        description: str | None = None,
        usage: str | None = None,
        prefix: str | None = None,
        epilog: str | None = None,
        parents: Sequence[argparse.ArgumentParser] | None = None,
        formatter_class: argparse._FormatterClass = PrettyHelpFormatter,  # type:ignore[reportPrivateUsage]
        prefix_chars: str = "-",
        fromfile_prefix_chars: str | None = None,
        argument_default: Any = None,
        conflict_handler: str = "error",
        add_help: bool = True,
        allow_abbrev: bool = True,
        exit_on_error: bool = True,
        auto_complete: bool = False,
    ) -> None:
        if parents is None:
            parents = []

        super().__init__(
            prog=prog,
            usage=usage,
            description=description,
            epilog=epilog,
            parents=parents,
            formatter_class=formatter_class,
            prefix_chars=prefix_chars,
            fromfile_prefix_chars=fromfile_prefix_chars,
            argument_default=argument_default,
            conflict_handler=conflict_handler,
            add_help=add_help,
            allow_abbrev=allow_abbrev,
            exit_on_error=exit_on_error,
        )
        self.exit_on_error = exit_on_error
        self.auto_complete = auto_complete
        self.prefix: str = prefix or ""
        self.version: str = version or ""

        if self.version:
            self.add_argument(
                "-v",
                "--version",
                action="version",
                version=f"{self.prog} {self.version}",
                default=argparse.SUPPRESS,
                help="print version",
            )

    def autocomplete(self) -> None:
        """Activate support for shell completion.

        Adds support for shell completion via argcomplete
        if found on the path.
        """
        # TODO: handling other shell
        # TODO: what's on with windows?
        if importlib.util.find_spec(name="argcomplete"):
            argcomplete = importlib.import_module(name="argcomplete")
            argcomplete.autocomplete(self)
            register = shutil.which("register-python-argcomplete") or "register-python-argcomplete"
            shell = shutil.which("bash") or "bash"
            cp = sp.run(
                args=[register, "--no-defaults", "-s", "bash", self.prog],
                shell=False,
                capture_output=True,
                check=False,
            )
            sp.run(shell, input=cp.stdout, check=True, shell=False)  # noqa: S603

    def parse_args(  # type:ignore[reportIncompatibleMethodOverride]
        self, args: Sequence[str] | None = None, namespace: argparse.Namespace | None = None
    ) -> argparse.Namespace:
        """Parse command line arguments."""
        if self.auto_complete:
            self.autocomplete()
        return super().parse_args(args, namespace)

    def format_usage(self):
        """Ask HelpFormatter to format the usage string."""
        formatter = self._get_formatter()
        formatter.add_usage(
            usage=self.usage,
            actions=self._actions,
            groups=self._mutually_exclusive_groups,
            prefix=self.prefix,
        )
        return formatter.format_help()

    def format_help(self):
        """Ask HelpFormatter to format the help string."""
        formatter = self._get_formatter()

        # usage
        formatter.add_usage(
            usage=self.usage,
            actions=self._actions,
            groups=self._mutually_exclusive_groups,
            prefix=self.prefix,
        )

        # description
        formatter.add_text(self.description)

        # positionals, optionals and user-defined groups
        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_text(action_group.description)
            formatter.add_arguments(action_group._group_actions)  # noqa: SLF001
            formatter.end_section()

        # epilog
        formatter.add_text(self.epilog)

        # determine help from format above
        return formatter.format_help()

    def exit(  # type:ignore[reportIncompatibleMethodOverride]  # noqa: PLR6301
        self,
        status: int = 0,
        message: str | None = None,
    ) -> None:
        """Either raise an ArgumentError or a SystemExit exception."""
        if status:
            raise argparse.ArgumentError(None, message or "unknown error")
        raise SystemExit(message)

    def error(  # type:ignore[reportIncompatibleMethodOverride] # dead: disable
        self,
        message: str,
    ) -> None:
        """Prints a usage message.

        Prints a usage message incorporating the message to stderr
        and exits.If you override this in a subclass, it should
        not return -- it should either exit or raise an exception.
        """
        self.print_usage()

        if self.exit_on_error:
            args = {"message": message}
            self.exit(2, _("error: %(message)s\n") % args)

        raise argparse.ArgumentError(None, message)

    def print_usage(self, file: IO[str] | None = None) -> None:
        """Prints the usage message."""
        if file is None:
            file = sys.stderr
        self._print_message(self.format_usage(), file)

    def print_help(self, file: IO[str] | None = None) -> None:  # dead: disable
        """Prints the help message."""
        if file is None:
            file = sys.stderr
        self._print_message(self.format_help(), file)

    def _print_message(  # noqa: PLR6301
        self,
        message: str,
        file: IO[str] | None = None,
    ) -> None:
        if message:
            if file is None:
                file = sys.stderr
            file.write(message)

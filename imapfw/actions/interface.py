# The MIT License (MIT).
# Copyright (c) 2015, Nicolas Sebrecht & contributors.

from typing import Type

from imapfw.conf import Parser


class ActionInterface:

    honorHooks = True
    requireRascal = True

    def exception(self, e: Type[Exception]) -> None:
        """Called on unexpected errors."""

    def getExitCode(self) -> int:
        """Return exit code."""

    def init(self, parser: Parser) -> None:
        """Initialize action."""

    def run(self) -> None:
        """Run action."""

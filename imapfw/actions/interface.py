# The MIT License (MIT).
# Copyright (c) 2015, Nicolas Sebrecht & contributors.

from imapfw.conf import Parser

# Annotations.
from imapfw.annotation import ExceptionClass


class ActionInterface:

    honorHooks = True
    requireRascal = True

    def exception(self, e: ExceptionClass) -> None:
        """Called on unexpected errors."""

    def getExitCode(self) -> int:
        """Return exit code."""

    def init(self, parser: Parser) -> None:
        """Initialize action."""

    def run(self) -> None:
        """Run action."""

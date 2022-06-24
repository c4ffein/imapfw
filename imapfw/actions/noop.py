# The MIT License (MIT).
# Copyright (c) 2015, Nicolas Sebrecht & contributors.

from typing import Type

from imapfw.conf import Parser

from .interface import ActionInterface


class Noop(ActionInterface):
    """The noop action allows testing the loading of the rascal."""

    honorHooks = False
    requireRascal = False

    def exception(self, e: Type[Exception]) -> None:
        raise NotImplementedError

    def getExitCode(self) -> int:
        return 0

    def init(self, parser: Parser) -> None:
        pass

    def run(self) -> None:
        pass


Parser.addAction("noop", Noop, help="test if the rascal can be loaded")

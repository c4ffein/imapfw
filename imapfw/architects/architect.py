# The MIT License (MIT).
# Copyright (c) 2015-2016, Nicolas Sebrecht & contributors.

"""

The achitects are high level objects to support actions with dynamic process handling.

They are helpers for the actions/softwares. They handles workers and whatever required to enable other components.

This is the wrong place for anything about business logic.
Architects are not problem solving for the purpose of the actions/softwares.

"""

from imapfw import runtime

# Annotations.
from imapfw.annotation import Function


@debugArchitect
class Architect(object):
    def __init__(self, workerName: str):
        self.workerName = workerName

        self.name = self.__class__.__name__
        self.worker = None

    def kill(self) -> None:
        """Kill worker."""
        self.worker.kill()

    def start(self, runner: Function, runnerArgs: tuple) -> None:
        """Start worker."""
        self.worker = runtime.concurrency.createWorker(self.workerName, runner, runnerArgs)
        self.worker.start()

    def stop(self) -> None:
        """Stop worker."""
        self.worker.join()

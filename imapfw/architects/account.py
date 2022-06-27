# The MIT License (MIT).
# Copyright (c) 2015-2016, Nicolas Sebrecht & contributors.

"""

Working with accounts implies end-to-end connections. Each end is a driver to work with the data.
The engine holds the business logic and is "put in the middle".

# SCHEMATIC OVERVIEW

```
      {worker}                        {worker}                         {worker}
    +----------+      (drives)      +----------+      (drives)       +----------+
    |  driver  |<-------------------|  engine  +-------------------->|  driver  |
    +----------+                    +----------+                     +----------+
```
"""

from typing import Iterable

from imapfw import runtime
from imapfw.engines import SyncAccounts
from imapfw.runners import topRunner
from imapfw.edmp import newEmitterReceiver

from .engine import EngineArchitect
from .folder import SyncFoldersArchitect
from .debug import debugArchitect

# Annotations.
from imapfw.edmp import Queue
from imapfw.types import Folders


@debugArchitect
class SyncArchitect(object):
    """Architect designed to sync one account."""

    def __init__(self, workerName: str, accountTasks: Queue, accountEngineName: str, folderEngineName: str):
        self.workerName = workerName
        self.accountTasks = accountTasks
        self.accountEngineName = accountEngineName
        self.folderEngineName = folderEngineName

        self.engineArch = None
        self.foldersArch = None
        self.receiver = None
        self.engine = None
        self.exitCode = -1  # Let caller know we are busy.
        self.foldersExitCode = -1  # Max from all folders architects.
        self.syncFoldersDone = False

    def _on_accountEngineDone(self, exitCode: int) -> None:
        """React to `done` event for the account engine.

        This event is triggered when the sync engine has no more task to process. Stop worker and set exit code."""

        # Set exit code.
        self._setExitCode(exitCode)
        self._setExitCode(self.foldersExitCode)
        # Stop both drivers.
        self.engineArch.getLeftEmitter().stop()
        self.engineArch.getRightEmitter().stop()
        # Stop current engine.
        self.engineArch.stop()

    def _on_areSyncFoldersDone(self) -> bool:
        return self.syncFoldersDone

    def _on_syncFolders(self, accountName: str, maxFolderWorkers: int, folders: Folders) -> None:
        """Start syncing of folders in async mode."""

        self.syncFoldersDone = False
        self.foldersArch = SyncFoldersArchitect(self.workerName, accountName)
        # Let the foldersArchitect re-use our drivers.
        self.foldersArch.start(
            maxFolderWorkers, folders, self.engineArch.getLeftEmitter(), self.engineArch.getRightEmitter(),
        )

    def _setExitCode(self, exitCode: int) -> None:
        self.exitCode = max(exitCode, self.exitCode)

    def init(self) -> None:
        """Initialize the architect. Helps to compose components easily."""

        self.engineArch = EngineArchitect(self.workerName)
        self.engineArch.init()

        self.receiver, emitter = newEmitterReceiver(self.workerName)

        # Setup events handling.
        self.receiver.accept("areSyncFoldersDone", self._on_areSyncFoldersDone)
        self.receiver.accept("accountEngineDone", self._on_accountEngineDone)
        self.receiver.accept("syncFolders", self._on_syncFolders)

        self.engine = SyncAccounts(
            self.workerName, emitter, self.engineArch.getLeftEmitter(), self.engineArch.getRightEmitter(),
        )

    def getExitCode(self) -> int:
        """Caller must monitor the exit code to know when we are done.

        - negative: busy.
        - zero: finished without error.
        - positive: got error(s)."""

        try:
            self.receiver.react()
            if self.foldersArch is not None:
                exitCode = self.foldersArch.getExitCode()
                if exitCode >= 0:
                    # Folders are all done.
                    self.foldersArch = None
                    self.syncFoldersDone = True
                    self.foldersExitCode = max(exitCode, self.foldersExitCode)

        except Exception as e:
            # TODO: honor rascal.
            runtime.ui.critical("%s got unexpected error '%s'" % (self.workerName, e))
            runtime.ui.exception(e)
            # Stop here.
            self.engineArch.kill()
            if self.foldersArch is not None:
                self.foldersArch.kill()
            self._setExitCode(10)  # See manual.

        return self.exitCode

    def start(self) -> None:
        assert self.engineArch is not None

        self.engineArch.start(
            topRunner, (self.workerName, self.engine.run, self.accountTasks),
        )


class SyncAccountsArchitect(object):
    """Architect to sync multiple accounts.

    Handles a collection of SyncArchitect."""

    def __init__(self, accountList: Iterable[str]):
        self.accountList = accountList

        self.syncArchs = []  # List of SyncArchitect.
        self.exitCode = -1
        self.accountTasks = None

    def start(self, maxConcurrentAccounts: int) -> None:
        """Starts the concurrents architects (workers). They are all created now."""

        # The account names are the tasks for the account workers.
        accountTasks = runtime.concurrency.createQueue()
        for name in self.accountList:
            accountTasks.put(name)

        # Avoid race condition: an empty queue would let account workers to quit without processing the content.
        # We have to make sure the queue is not  empty before using them.
        # accountList can't be empty as defined by the argument parser.
        while accountTasks.empty():
            pass
        # Oops! This is still racy! This assumes that the NEXT task is available once the previous run is done.
        # This should be reasonable assumption, though...

        # Setup the architecture.
        for i in range(maxConcurrentAccounts):
            workerName = f"Account.{i}"

            syncArch = SyncArchitect(workerName, accountTasks, "SyncAccountEngine", "SyncFolderEngine")
            syncArch.init()
            syncArch.start()  # Async.
            self.syncArchs.append(syncArch)

    def run(self) -> int:
        # Monitor the architects.
        while len(self.syncArchs) > 0:
            for architect in self.syncArchs:
                exitCode = architect.getExitCode()
                if exitCode >= 0:
                    if exitCode > self.exitCode:
                        self.exitCode = exitCode
                    self.syncArchs.remove(architect)

        if self.exitCode < 0:
            return 99  # See manual.
        return self.exitCode

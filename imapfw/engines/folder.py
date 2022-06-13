# The MIT License (MIT).
# Copyright (c) 2015-2016, Nicolas Sebrecht & contributors.

"""

Engines to work with folders/maiboxes.

"""

from imapfw import runtime
from imapfw.edmp import Channel
from imapfw.types.account import loadAccount

from .engine import SyncEngine, EngineInterface, SyncEngineInterface

# Interfaces.
from imapfw.interface import implements, adapts, checkInterfaces

# Annotations.
from imapfw.edmp import Emitter
from imapfw.concurrency import Queue
from imapfw.types.folder import Folder


@checkInterfaces()
@adapts(SyncEngine)
@implements(EngineInterface)
class SyncFolders(SyncEngine):
    """The engine to sync a folder in a worker."""

    def __init__(self, workerName: str, referent: Emitter, left: Emitter, right: Emitter, accountName: str):

        super(SyncFolders, self).__init__(workerName)
        self.referent = referent
        self.left = left
        self.rght = right
        self.accountName = accountName

    def _infoL(self, level, msg):
        runtime.ui.infoL(level, "%s %s" % (self.workerName, msg))

    # Outlined.
    def _syncFolder(self, folder: Folder) -> int:
        """Sync one folder."""

        # account = loadAccount(self.accountName)
        # leftRepository = account.fw_getLeft()
        # rightRepository = account.fw_getRight()

        if self.left.isDriverBuilt_sync() is False:
            self.left.buildDriver(self.accountName, "left")
        if self.rght.isDriverBuilt_sync() is False:
            self.rght.buildDriver(self.accountName, "right")

        self.left.connect()
        self.rght.connect()

        self.left.select_sync(folder)
        self.rght.select_sync(folder)

        return 0

    def run(self, taskQueue: Queue) -> None:
        """Runner for the sync folder engine.

        Sequentially process the folders."""

        #
        # Loop over the available folder names.
        #
        for folder in Channel(taskQueue):
            self.processing(folder)

            # The engine will let explode errors it can't recover from.
            try:
                exitCode = self._syncFolder(folder)
                self.setExitCode(exitCode)

            except Exception as e:
                runtime.ui.error("could not sync folder %s" % folder)
                runtime.ui.exception(e)
                # TODO: honor hook!
                self.setExitCode(10)  # See manual.

        self.checkExitCode()
        self.referent.stop(self.getExitCode())

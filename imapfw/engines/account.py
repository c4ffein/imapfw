# The MIT License (MIT).
# Copyright (c) 2015-2016, Nicolas Sebrecht & contributors.

"""

Engines to work with accounts.

"""

from imapfw import runtime
from imapfw.edmp import Channel
from imapfw.types import Folders

from .engine import SyncEngine

# Annotations.
from imapfw.edmp import Emitter
from imapfw.concurrency import Queue
from imapfw.types.account import Account


def con_and_sync(emitter, emitter_name, account_name):
    emitter.buildDriver(account_name, emitter_name)
    emitter.connect()  # Connect the drivers.
    emitter.login()  # TODO : Added by c4ffein. Just check we need to login before sending loggin event?
    emitter.getFolders()
    return emitter.getFolders_sync()


class SyncAccounts(SyncEngine):
    """The sync account engine."""

    def __init__(self, workerName: str, referent: Emitter, left: Emitter, right: Emitter):
        super(SyncAccounts, self).__init__(workerName)

        self.referent = referent
        self.left = left
        self.rght = right

    # Outlined.
    def _syncAccount(self, account: Account):
        """Sync one account."""

        runtime.ui.infoL(3, f"merging folders for {account.name}")

        l_repo, r_repo = account.left, account.right  # Get the repo instances

        # Get the folders from both sides so we can feed the folder tasks.
        leftFolders = con_and_sync(self.left, "left", account.name)
        rightFolders = con_and_sync(self.rght, "right", account.name)

        # Merge the folder lists.
        mergedFolders = Folders()
        for sideFolders in [leftFolders, rightFolders]:
            for folder in sideFolders:
                if folder not in mergedFolders:
                    mergedFolders.append(folder)

        runtime.ui.infoL(3, f"{account.name} merged folders {mergedFolders}")

        rascalFolders = account.syncFolders(mergedFolders)  # Pass the list to the rascal.

        # The rascal might request for non-existing folders!
        syncFolders = Folders()
        ignoredFolders = Folders()
        for folder in rascalFolders:
            if folder in mergedFolders:
                syncFolders.append(folder)
            else:
                ignoredFolders.append(folder)

        if len(ignoredFolders) > 0:
            runtime.ui.warn(f"rascal asked to sync non-existing folders for '{account.name}': ignoredFolders")

        if len(syncFolders) < 1:
            runtime.ui.infoL(3, f"{account.name}: no folder to sync")
            return  # Nothing more to do.

        # TODO: make max_connections mandatory in rascal.
        maxFolderWorkers = min(len(syncFolders), r_repo.conf.get("max_connections"), l_repo.conf.get("max_connections"))

        runtime.ui.infoL(3, f"{account.name} syncing folders {syncFolders}")

        # Syncing folders is not the job of this engine. Use sync mode to ensure
        # the referent starts syncing of folders before this engine stops.
        self.referent.syncFolders_sync(account.name, maxFolderWorkers, syncFolders)

        # Wait for all the folders to be synced before processing the next account.
        while self.referent.areSyncFoldersDone_sync() is not True:
            pass

    def run(self, taskQueue: Queue) -> None:
        """Sequentially process the accounts."""

        # Loop over the available account names.
        for accountName in Channel(taskQueue):
            # The syncer let explode errors it can't recover from.
            try:
                self.processing(accountName)
                # Get the account instance from the rascal.
                account = runtime.rascal.getAccount(accountName)
                self._syncAccount(account)  # Wait until folders are done.
                self.setExitCode(0)
                # TODO: Here, we only keep max exit code. Would worth using the
                # rascal at the end of the process for each account.

            except Exception as e:
                runtime.ui.error(f"could not sync account {accountName}")
                runtime.ui.exception(e)
                # TODO: honor rascal!
                self.setExitCode(10)  # See manual.

        self.checkExitCode()  # Sanity check.
        self.referent.accountEngineDone(self.getExitCode())

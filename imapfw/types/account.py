# The MIT License (MIT).
# Copyright (c) 2015, Nicolas Sebrecht & contributors.

from typing import TypeVar, Union
from .folder import Folders

# Annotations.
from imapfw.types.repository import Repository


AccountClass = TypeVar("Account based class")


class Account():
    """The Account base class. The namespace `fw_` is reserved for the framework internals."""

    def __init__(self, name, left, right, conf) -> None:
        """Override this method to make initialization in the rascal."""
        self.name, self.left, self.right, self.conf = name, left, right, conf
        self.init()

    def init(self) -> None:
        """Override this method to make initialization in the rascal."""

    def syncFolders(self, folders: Folders) -> Folders:
        return folders

    # TODO : C4FFEIN : SANIT
    def sanit(self, rascal):
        self.left = rascal.getRepository(self.left) if isinstance(self.left, str) else self.left
        self.right = rascal.getRepository(self.right) if isinstance(self.right, str) else self.right

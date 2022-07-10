# The MIT License (MIT).
# Copyright (c) 2015, Nicolas Sebrecht & contributors.

import imp  # TODO: use library importlib instead of deprecated imp.

from imapfw.api import controllers, types, drivers, shell

# Annotations.
from typing import List, TypeVar


Function = TypeVar("Function")
Class = TypeVar("Class")


def fixin(nrascal, di):
    for k, v in di.items():
        if isinstance(v, str): di[k] = nrascal[v]
        if isinstance(v, dict): fixin(nrascal, v)


class Rascal(object):
    """The Rascal.

    Turn the rascal (the user Python file given at CLI) into a more concrete thing (a Python module).

    This is where the Inversion of Control happen: we give to the rascal the
    illusion he's living a real life while we keep full control of him."""

    def __init__(self):
        self._rascal = {}  # The module.
        self._nrascal = {}  # The curated module.
        # TODO : C4FFEIN : We need those 2 struct to put classes in here and not duplicate code.
        self.accounts = {}
        self.repositories = {}
        self.folders = {}
        # Cached literals.
        self._mainConf = None

    def _isDict(self, obj: object) -> bool:
        try:
            return type(obj) == dict
        except:
            raise TypeError("'{obj.__name__}' must be a dictionnary, got '{type(obj)}'")

    def _getHook(self, name: str) -> Function:
        try:
            return self.getFunction(name)
        except:
            return lambda hook, *args: hook.ended()

    def _getLiteral(self, name: str) -> type:
        return self._nrascal.get(name, None) or getattr(self._rascal, name)

    def get(self, name: str, expectedTypes: List[Class]):
        cls = self._getLiteral(name)

        for expectedType in expectedTypes:
            if issubclass(cls, expectedType):
                return cls

        raise TypeError(f"class '{name}' is not a sub-class of '{expectedTypes}' : it is a '{type(cls)}'")

    def getAccount(self, name: str):
        return self.accounts[name]

    def getRepository(self, name: str):
        return self.repositories[name]

    def getAll(self, targetTypes: List[Class]) -> List[Class]:
        classes = []
        for literal in dir(self._rascal):
            if literal.startswith("_") or getattr(self._rascal, literal) is dict:
                continue
            try:
                classes.append(self.get(literal, targetTypes))
            except TypeError:
                pass
        for name, value in self._nrascal.items():
            try:
                classes.append(self.get(literal, targetTypes))
            except TypeError:
                pass
        return classes

    def getExceptionHook(self) -> Function:
        return self._getHook("exceptionHook")

    def getFunction(self, name: str) -> Function:
        func = self._getLiteral(name)  # We probably don't care, we just want a func I hope
        if not callable(func):
            raise TypeError("function expected for '%s'" % name)
        return func

    def getMaxConnections(self, accountName: str) -> int:
        def getValue(repository):
            try:
                return int(repository.conf.get("max_connections"))
            except AttributeError:
                return 999

        account = self.get(accountName, [types.Account])
        max_sync = min(getValue(account.left), getValue(account.right))
        return max_sync

    def getMaxSyncAccounts(self) -> int:
        return int(self._mainConf.get("max_sync_accounts"))

    def getPostHook(self) -> Function:
        return self._getHook("postHook")

    def getPreHook(self) -> Function:
        return self._getHook("preHook")

    def getSettings(self, name: str) -> dict:
        #literal = getattr(self._rascal, name)
        literal = self._getLiteral(name)
        if not isinstance(literal, dict):
            raise TypeError(f"expected dict for '{name}', got '{type(literal)}'")
        return literal

    def load(self, path: str) -> None:
        # Create empty module.
        rascal_mod = imp.new_module("rascal")
        rascal_mod.__file__ = path

        with open(path) as rascal_file:
            exec(compile(rascal_file.read(), path, "exec"), rascal_mod.__dict__)
        self._rascal = rascal_mod

        for section_name, cls in (("DriveDrivers", shell.DriveDriver), ("Maildirs", types.Maildir), ("Imaps", types.Imap)):
            try:
                section = getattr(self._rascal, section_name)
            except Exception as e:
                print(e)
                continue
            for new_cls_name, new_dict in section.items():
                self.load_object_dict({"type": cls, "name": new_cls_name} | new_dict)
        for section_name, cls in (("Home", types.Account), ("Foundation", types.Account)):
            try:
                section = getattr(self._rascal, section_name)
            except Exception as e:
                print(e)
                continue
            fixin(self._nrascal, new_dict)
            self._nrascal[section_name] = type(section_name, (cls, *cls.__bases__), new_dict)

        self._mainConf = self.getSettings("MainConf")

        # Turn accounts definitions from MainConf into global of rascal literals.
        if "accounts" in self._mainConf:
            for accountDict in self._mainConf.get("accounts"):
                self.accounts[accountDict.get("name")] = self.load_object_dict(accountDict)

        # First pass ended. We now want all refs to be pointers, not strings or pointers.
        for account in self.accounts.values():
            account.sanit(self)

    def load_object_dict(self, d: dict):
        t = d.get("type")
        if issubclass(t, types.Repository):
            o = t(*map(lambda s: d.get(s), ["name", "driver", "conf"]))  # TODO : optional controllers ?
            self.repositories[o.name] = o
        elif issubclass(t, types.Folder):
            o = t(*map(lambda s: d.get(s), ["name"]))  # TODO : optional encoding
            self.folders[o.name] = o
        elif issubclass(t, types.Account):
            if isinstance(d["left"], dict):
                d["left"] = self.load_object_dict(d["left"])
            if isinstance(d["right"], dict):
                d["right"] = self.load_object_dict(d["right"])
            o = t(*map(lambda s: d.get(s), ["name", "left", "right", "conf"]))  # TODO : optional controllers ?
            self.accounts[o.name] = o
        else:
            raise Exception(f"Unhandled type {t} in config")
        return o

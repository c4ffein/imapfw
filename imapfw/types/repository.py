# The MIT License (MIT).
# Copyright (c) 2015, Nicolas Sebrecht & contributors.

from typing import TypeVar, Union

from imapfw.controllers.controller import loadController, ControllerClass
from imapfw.drivers.driver import loadDriver, Driver


RepositoryClass = TypeVar("Repository based class")


class Repository():
    """The repository base class.

    The `fw_` namespace is reserved to the framework internals. Any method of this namespace must be overriden."""

    conf = None
    driver = None
    isLocal = None
    controllers = []

    def __init__(self):
        # Turn the class attributes into instance attributes.
        self.conf = self.conf.copy()
        self.driver = self.driver
        self.controllers = self.controllers.copy()

    def fw_appendController(self, cls_controller: ControllerClass, conf: dict = None) -> None:

        self.fw_insertController(cls_controller, conf, -1)

    def fw_getDriver(self) -> Driver:
        """Get the "high-level" driver with the controllers

        Chain the controllers on top of the driver. Controllers are run in the
        driver worker."""

        driver = loadDriver(self.driver, self.getClassName(), self.conf)

        # Chain the controllers.
        # Keep the original attribute as-is.
        controllers = self.controllers.copy()
        # Nearest to end-driver is the last in this list.
        controllers.reverse()
        for obj in controllers:
            controller = loadController(obj, self.getClassName(), self.conf)

            controller.fw_drive(driver)  # Chain here.
            driver = controller  # The next controller will drive this.

        return driver

    def fw_insertController(self, cls_controller: ControllerClass, conf: dict = None, position: int = 0):

        setattr(cls_controller, "conf", conf)
        if position < 0:
            position = len(self.controllers)

        self.controllers.insert(position, cls_controller)

    def getClassName(self):
        return self.__class__.__name__

    def init(self):
        """Override this method to make initialization in the rascal."""

        pass


def loadRepository(obj: Union[RepositoryClass, dict]) -> Repository:

    print(obj, Repository)  # TODO
    try:
        if issubclass(obj, Repository):
            cls_repository = obj
        else:
            raise TypeError("got unsupported %s" % repr(obj))

    except TypeError:
        try:
            if not issubclass(obj, dict):
                raise TypeError()

            # The repository is defined in the dictionnary form in the rascal.
            # Build the class.
            cls_repository = type(obj.get("name"), obj.get("type"), {})

            # Attached attributes.
            for name, mandatory in {"conf": True, "driver": True, "controllers": []}:
                try:
                    setattr(cls_repository, name, obj.get(name))
                except KeyError:
                    if mandatory is True:
                        raise Exception(f"mandatory key '{name}' is not defined for '{cls_repository.__name__}'")
                    setattr(cls_repository, name, mandatory)

        except TypeError:
            raise TypeError(f"'{repr(obj)}' for a repository is not supported")

    repository = cls_repository()
    repository.init()

    return repository

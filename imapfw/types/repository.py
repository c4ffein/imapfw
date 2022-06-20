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
    isLocal = None

    def __init__(self, name, driver, conf, controllers=[]):
        self.name, self.driver, self.conf, self.controllers = name, driver, conf.copy(), controllers.copy()
        self.init()

    def fw_appendController(self, cls_controller: ControllerClass, conf: dict = None) -> None:
        self.fw_insertController(cls_controller, conf, -1)

    def fw_getDriver(self) -> Driver:
        """Get the "high-level" driver with the controllers, chain them (run in drive worker) on top of the driver."""
        driver = loadDriver(self.driver, self.name, self.conf)
        controllers = self.controllers.copy()  # Chain the controllers. Keep the original attribute as-is.
        # Nearest to end-driver is the last in this list.
        controllers.reverse()
        for obj in controllers:
            controller = loadController(obj, self.name, self.conf)
            controller.fw_drive(driver)  # Chain here.
            driver = controller  # The next controller will drive this.

        return driver

    def fw_insertController(self, cls_controller: ControllerClass, conf: dict = None, position: int = 0):
        setattr(cls_controller, "conf", conf)
        if position < 0:
            position = len(self.controllers)
        self.controllers.insert(position, cls_controller)

    def init(self):
        """Override this method to make initialization in the rascal."""

        pass

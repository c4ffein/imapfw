# The MIT License (MIT).
# Copyright (c) 2015, Nicolas Sebrecht & contributors.

"""

A controller is defined on a repository to control its end-driver.

Controllers have the same public interface as the drivers. Each responds like a driver, does its job and relays the
requests (and results) to (or from) the underlying driver.

Controllers can be chained to each others so that the flows pass through each.

They can either be passive or active. Passive controllers follow-up the requests as-is and returns the unchanged
results. Active controllers changes the flow to achieve their tasks. IOW, each controller can only view what the
underlying controller accepts to show. Hence, the order in the chain is important.

The controller base "Controller" is a passive controller (see code below).

The chain of controller is defined in the rascal.


SCHEMATIC OVERVIEW EXAMPLE (right side)
---------------------------------------

                 (filter)      (tracker)      (encoder)
+----------+   +----------+   +----------+   +----------+   +----------+
|          |-->|          |-->|          |-->|          |-->|          |
|  engine  |   |controller+   |controller|   |controller|   |  driver  |
|          |<--|          |<--|          |<--|          |<--|          |
+----------+   +----------+   +----------+   +----------+   +----------+
                 [active]       [passive]      [active]
                              notifications,  UTF-7/UTF-8
                                debugging


"""

from imapfw import runtime
from imapfw.constants import CTL

# Annotations.
from typing import Union, TypeVar


ControllerClass = TypeVar("Controller class and derivates")


class Controller():

    conf = {}

    def __init__(self, repositoryName: str, repositoryConf: dict, conf: dict):
        self.repositoryName = repositoryName
        # Merge the repository configuration with the controller configuration.
        self.conf = repositoryConf.copy()
        self.conf.update(conf.copy())

        self.driver = None

    def __getattr__(self, name):
        return getattr(self.driver, name)

    def fw_drive(self, driver):
        runtime.ui.debugC(
            CTL, f"chaining driver '{driver.__class__.__name__}' with controller '{self.__class__.__name__}'"
        )
        self.driver = driver

    def init(self):
        """Override this method to make initialization in the rascal."""

        pass


def loadController(obj: Union[ControllerClass, dict], repositoryName: str, repositoryConf: dict) -> Controller:

    if isinstance(obj, dict):
        cls_controller = obj.get("type")  # Must be the controller class.
        controllerConf = obj.get("conf")
    else:
        cls_controller = obj
        controllerConf = obj.conf

    if not issubclass(cls_controller, Controller):
        raise TypeError(
            f"controller {self.driver.conf} of {repositoryName} does not derivates from types.controllers.Controller"
        )

    controller = cls_controller(repositoryName, repositoryConf, controllerConf)
    controller.init()

    return controller

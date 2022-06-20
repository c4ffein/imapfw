# The MIT License (MIT).
# Copyright (c) 2015, Nicolas Sebrecht & contributors.

from imapfw.interface import Interface

from imapfw.annotation import DriverClass  # Annotations.



class Driver(Interface):
    """The Driver base class.

    This is the middleware for the drivers:
    - this is the base class to all drivers (e.g. Maildir, Driver, etc).
    - does not enable controllers machinery at this point.

    This interface is the API to anyone working with a driver (engines, shells, etc).
    """

    # While updating this interface think about updating the fake controller, too.

    conf = {}  # The configuration of the type has to be there.
    local = None


    def __init__(self, repositoryName: str, conf: dict):
        self.repositoryName = repositoryName
        self.conf = conf

    def getRepositoryName(self) -> str:
        """Return the repository name of this driver."""
        return self.repositoryName

    def init(self) -> None:
        """Override this method to make initialization in the rascal."""
        pass

    def isLocal(self) -> bool:
        """Return True of False whether drived data is local."""
        return self.local


def loadDriver(cls_driver: DriverClass, repositoryName: str, repositoryConf: dict) -> Driver:

    if not issubclass(cls_driver, Driver):  # Build the final end-driver.
        raise TypeError(f"driver {cls_driver.__name__} of {repositoryName} does not satisfy Driver")

    driver = cls_driver(repositoryName, repositoryConf)
    driver.init()

    return driver

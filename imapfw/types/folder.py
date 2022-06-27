# The MIT License (MIT)
#
# Copyright (c) 2015, Nicolas Sebrecht & contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from collections import UserList
from functools import total_ordering
from typing import Union


ENCODING = "UTF-8"


@total_ordering
class Folder(object):
    """Internal model representative of a folder.

    Used by any driver, controller or engine. Might be passed to the user via the rascal.
    Internal name is the folder name with the levels of hierarchy, type bytes.
    Each driver must use the same representation so we can compare folders from multiple drivers.
    """
    def __init__(self, name, encoding=None):
        self.setName(name, encoding)  # Must be bytes.
        self._hasChildren = None
        self._root = None

    def __bytes__(self):
        return self._name

    def __eq__(self, other):
        return self.getName() == other.getName()

    def __lt__(self, other):
        return self.getName() < other.getName()

    def __repr__(self):
        return repr(self._name.decode(ENCODING))

    def __str__(self):
        return self.getName()

    def getName(self, encoding: str = ENCODING) -> str:
        """Return folder base name."""
        return self._name.decode(encoding)

    def getRoot(self, encoding: str = ENCODING) -> str:
        """Return the path to the folder."""
        return self._root.decode(encoding)

    def hasChildren(self) -> bool:
        """Return True of False whether this folder has children."""
        return self._hasChildren

    def setName(self, name: Union[str, bytes], encoding: str = None) -> None:
        """Set the folder base name.

        :name: folder name with hierarchy seperated by '/' (e.g. 'a/folder'). # TODO : C4FEIN : SECURITY
        :encoding: encoding of the name. Expects bytes if not set.
        """
        self._name = name if type(name) == bytes else name.encode(encoding)

    def setHasChildren(self, hasChildren: bool) -> None:
        """Set if folder has children."""
        self._hasChildren = hasChildren

    def setRoot(self, root: str, encoding: str = ENCODING) -> None:
        """Set the path to the folder."""
        if type(root) == bytes:
            self._root = root
        else:
            self._root = root.encode(encoding)


class Folders(UserList):
    """A list of Folder instances."""

    def __init__(self, *args):
        super(Folders, self).__init__(list(args))

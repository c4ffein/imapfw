# The MIT License (MIT).
# Copyright (c) 2015, Nicolas Sebrecht & contributors.

"""

Introduction
============

The concurrency module defines a common interfaces to whatever backend is used
(multiprocessing, Python threading, etc).  "worker" is the generic term used to
define a thread (for Python threading) or a process (for multiprocessing).

Using the concurrency module
============================

The main entry point is the :func:`Concurrency` factory. The returned
backend satisfy the interface :class:`ConcurrencyInterface`.

The :func:`WorkerSafe` decorator allows to easily make any existing callable
concurrency-safe.

"""

import pickle

from imapfw import runtime
from imapfw.constants import WRK


SimpleLock = None
"""

SimpleLock is a function defined at runtime and exposed in the rascal to create
locks. The real function is set according to the command-line option.

"""


class WorkerInterface(object):
    def getName(self):
        raise NotImplementedError

    def join(self):
        raise NotImplementedError

    def kill(self):
        raise NotImplementedError

    def start(self):
        raise NotImplementedError


class QueueInterface(object):
    def empty(self):
        raise NotImplementedError

    def get(self):
        raise NotImplementedError

    def get_nowait(self):
        raise NotImplementedError

    def put(self):
        raise NotImplementedError


class LockInterface(object):
    def acquire(self):
        raise NotImplementedError

    def release(self):
        raise NotImplementedError


class ConcurrencyInterface(object):
    def createLock(self):
        raise NotImplementedError

    def createQueue(self):
        raise NotImplementedError

    def createWorker(self):
        raise NotImplementedError

    def getCurrentWorkerNameFunction(self):
        raise NotImplementedError


def WorkerSafe(lock) -> LockInterface:
    """Decorator for locking any callable.

    It is usefull to forbid concurrent access to non concurrency-safe data or libraries.
    The decorated callable has to end before the next concurrent call can start.
    It is required for the decorated callable to end or your program might deadlock."""

    def decorate(func):
        def safeFunc(*args, **kwargs):
            with lock:
                values = func(*args, **kwargs)
            return values

        return safeFunc

    return decorate


class LockBase(LockInterface):
    def __enter__(self):
        self.lock.acquire()

    def __exit__(self, t, v, tb):
        self.lock.release()

class Concurrency:
    """
    Handling signals with threading
    ===============================

    SIGTERM
    -------

    Main thread get KeyboardInterrupt. Only daemon childs gets killed.

    SIGKILL
    -------

    Kills everything (the process is killed, so the threads).
    """

    def createWorker(self, name, target, args):
        from threading import Thread

        class Worker(WorkerInterface):
            def __init__(self, name, target, args):
                self._name = name

                self._thread = Thread(name=name, target=target, args=args, daemon=True)

            def getName(self):
                return self._name

            def kill(self):
                """Kill a worker.

                This is only usefull for the workers working with a failed worker.
                In daemon mode: workers get's killed when the main thread gets killed."""

                runtime.ui.debugC(WRK, "%s killed" % self._name)

            def start(self):
                self._thread.start()
                runtime.ui.debugC(WRK, "%s started" % self._name)

            def join(self):
                runtime.ui.debugC(WRK, "%s join" % self._name)
                self._thread.join()  # Block until thread is done.
                runtime.ui.debugC(WRK, "%s joined" % self._name)

        return Worker(name, target, args)

    def createLock(self):
        from threading import Lock

        class TLock(LockBase):
            def __init__(self, lock):
                self.lock = lock

            def __enter__(self):
                self.lock.acquire()

            def __exit__(self, t, v, tb):
                self.lock.release()

            def acquire(self):
                self.lock.acquire()

            def release(self):
                self.lock.release()

        return TLock(Lock())

    def createQueue(self):
        from queue import Queue, Empty  # Thread-safe.

        class TQueue(QueueInterface):
            def __init__(self):
                self._queue = Queue()

            def empty(self):
                return self._queue.empty()

            def get(self):
                return self._queue.get()

            def get_nowait(self):
                try:
                    return self._queue.get_nowait()
                except Empty:
                    return None

            def put(self, data):
                # Fail now if data can't be pickled. Otherwise, error will be raised at random time.
                pickle.dumps(data)
                self._queue.put(data)

        return TQueue()

    def getCurrentWorkerNameFunction(self):
        from threading import current_thread

        def currentWorkerName():
            return current_thread().name

        return currentWorkerName


#ConcurrencyBackends = { "threading": ThreadingBackend }


#class Concurrency:
#
#    global SimpleLock
#    try:
#        concurrency = ConcurrencyBackends[backendName]()
#        if SimpleLock is None:
#            SimpleLock = concurrency.createLock
#        return concurrency
#    except KeyError:
#        raise Exception("unkown backend: %s" % backendName)

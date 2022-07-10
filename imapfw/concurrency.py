# The MIT License (MIT).
# Copyright (c) 2015, Nicolas Sebrecht & contributors.

"""

Introduction
============

The concurrency module defines an interface to the Python threads.
"worker" is the generic term used to define a thread.

Using the concurrency module
============================

Workers, Locks, and Queues are handled by the Concurrency class.
The :func:`WorkerSafe` decorator allows to easily make any existing callable concurrency-safe.

"""

from threading import Thread, Lock as TLock
from queue import Queue as QQueue, Empty

import pickle

from imapfw import runtime
from imapfw.constants import WRK


SimpleLock = None
"""
SimpleLock is a function defined at runtime and exposed in the rascal to create locks.
The real function is set according to the command-line option.
"""


class Worker:
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


class Queue:
    def __init__(self):
        self._queue = QQueue()

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


class Lock:
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


def WorkerSafe(lock) -> Lock:
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
        return Worker(name, target, args)

    def createLock(self):
        return Lock(TLock())

    def createQueue(self):
        return Queue()

    def getCurrentWorkerNameFunction(self):
        from threading import current_thread

        def currentWorkerName():
            return current_thread().name

        return currentWorkerName

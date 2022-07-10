# The MIT License (MIT).
# Copyright (c) 2015, Nicolas Sebrecht & contributors.

"""

Overview
========

This module allows event-driven communication between workers. "edmp" stands for "Event-Driven Message Passing".

This follows the "passing by message" design with improved events.
The emitter sends a message.
The message is passed to the attached receiver in another worker.
The receiver handles the message by calling the code assigned to this event.
The returned values are sent back to the emitter as a message when appropriate.

In order to interact with other workers, the `newEmitterReceiver` function returns:
    - one `Receiver` instance;
    - one `Emitter` instance.

The emitter sends events to the receiver with simple method calls.

:Example:

>>> emitter.doSomething(whatever, parameter=optional, to=send)

The code implementing the "doSomething" event is run by the receiver.

The receiver and the emitter support two kinds of communication:
    - asynchronous;
    - synchronous (actually pseudo-synchronous but you don't have to care).


The receiver
============

The receiver must define the callable to each supported event.

:Example:

>>> def on_printInfo(info):
>>>     print(info)
>>>
>>> receiver, emitter = emp.newEmitterReceiver('test')
>>> receiver.accept('printInfo', on_printInfo)
>>> emitter.printInfo('It works!')
>>> emitter.stopServing()
>>>
>>> while receiver.react():
>>>     pass
It works!
>>>

Here, the emitter is sending the event 'printInfo'. The receiver reacts by calling the function 'on_printInfo'.

The receiver has only two public methods:
    - accept: to define the available events.
    - react: to process the received events.

The `Receiver.react` method will process all the received events. This returns
True or False whether it should continue reacting or not.

:Example:

>>> while receiver.react():
>>>     pass

Each event reaction ends before the next is processed in the order they are sent by the emitter.
They are internally put in a queue. The processing is sequential. So, it's fine to use a receiver like that:

:Example:

>>> class EventHandler(object):
>>>     def __init__(self, receiver):
>>>         self._receiver = receiver
>>>
>>>         receiver.accept('longRequest', self._longRequest)
>>>         receiver.accept('getResult_longRequest', self._withResult_longRequest)
>>>
>>>         self._result = None
>>>
>>>     def _longRequest(self):
>>>         # Code taking a very long time; self._result gets True or
>>>         # False.
>>>         if condition:
>>>             self._result = False
>>>         self._result = True
>>>
>>>     def _withResultOfLongRequest_do(self):
>>>         if self._result is True: # Real value set by longRequest().
>>>             doSomething()
>>>
>>>     def serve(self):
>>>         while self._receiver.react():
>>>             pass

The emitter does not have to worry about the order of execution since it's
guaranted they are executed in the same order of the calls.

**However, if the emitter is used in more than one worker, the order of
execution for the methods is undefined accross the emitters.**


The emitter
===========

Sending asynchronous events
---------------------------

The easiest way to send events is to not worry about what is done. This is
achieved with a call to a method of the emitter. The name of the method is the
name of the event.

The result of this event is cached at the receiver side. To later process the
last result of an event, result can be retrieved by adding the "cached_" prefix
to the event name and calling it without argument.

:Example:

>>> result = emitter.cached_doSomething()


Sending synchronous events
--------------------------

If you need the result of the event, it's possible to get this by appending '_sync' to the event name.

:Example:

>>> result = emitter.doSomething_sync(whatever, parameter=optional, to=send)

Predefined events of emitters
-----------------------------

- 'stopServing': when used the react method of the receiver returns False allowing reacting loop to stop.
- 'help': print the docstrings of the accepted events. Usefull in shell sessions or for debugging.


Error handling
==============

Asynchronous mode
-----------------

The receiver won't raise any unhandled exception while reacting on events. The errors are logged-out.


Synchronous mode
----------------

In synchronous mode, any error is logged-out and then passed to the emitter.

Because queues can't pass exceptions, only the class and the reason are passed
to the emitter (without the stack trace which was logged-out). The emitter will
make its best to re-raise the exact same exception.

To get proper exception handling, you must import all unhandled exception classes before using the emitter.
Unkown exception classes will raise a RuntimeError.


Limitations
===========

Passed values
-------------

The main limitation is about the parameters and the returned values whose must
be accepted by the internal queues. Don't expect to pass your SO_WONDERFULL
objects. Take this limitation as a chance to write good code and objects with
simple APIs. :-)

However, if you really need to pass objects, consider implementing the
`emp.serializer.SerializerInterface` class.


Effectively using the receiver and emitters
-------------------------------------------

Because communication internally relies on queues and that queues must be used
in the workers, they must be created and passed to the worker when the latter is
created. This means that all workers have a pre-defined number of receivers.
Don't try to build and use emitters/receivers for a worker once running.


Receiver and emitter in the same worker
---------------------------------------

The emitter and receiver objects are usually aimed at being run in different
workers, one of them possibly being the main worker. However, it's possible to
use them to handle advanced communication between objects.

If you do this, don't ever use the synchronous mode. This will loop indefinitely and block (deadlock).


There are good demos at the end of the module. ,-)

"""

import time
from typing import TypeVar, Type

from imapfw import runtime
from imapfw.constants import EMT, SLEEP

from imapfw.concurrency import Queue


# TODO: expose
_SILENT_TIMES = 100


class TopicError(Exception):
    pass


# Outlined.
def _raiseError(cls_Exception: Type[Exception], reason: str):
    """Default callback for errors."""

    try:
        raise cls_Exception(reason)
    except NameError as e:
        runtime.ui.exception(e)
        raise RuntimeError("exception from receiver cannot be raised %s: %s" % (cls_Exception.__name__, reason))


class Channel(object):
    """Queue made iterable."""

    def __init__(self, queue: Queue):
        self._queue = queue

    def __iter__(self):
        return self

    def __next__(self):
        elem = self._queue.get_nowait()
        if elem is None:
            raise StopIteration
        return elem


class Emitter(object):
    """Send events."""

    def __init__(self, name: str, event: Queue, result: Queue, error: Queue):
        self._name = name
        self._eventQueue = event
        self._resultQueue = result
        self._errorQueue = error

        self._previousTopic = None
        self._previousTopicCount = 0

    def __getattr__(self, topic: str):
        """Dynamically create methods to send events."""

        def send_event(*args, **kwargs):
            request = (topic, args, kwargs)

            if self._previousTopic != topic:
                if self._previousTopicCount > 0:
                    runtime.ui.debugC(
                        EMT, "emitter [%s] sent %i times %s" % (self._name, _SILENT_TIMES, self._previousTopic)
                    )
                self._previousTopicCount = 0
                self._previousTopic = topic
                runtime.ui.debugC(EMT, "emitter [%s] sends %s" % (self._name, request))
            else:
                self._previousTopicCount += 1
                if self._previousTopicCount == 2:
                    runtime.ui.debugC(
                        EMT,
                        "emitter [%s] sends %s again,"
                        " further sends for this topic made silent" % (self._name, request),
                    )
                if self._previousTopicCount > (_SILENT_TIMES - 1):
                    runtime.ui.debugC(
                        EMT,
                        "emitter [%s] sends for the %ith time %s" % (self._name, _SILENT_TIMES, self._previousTopic),
                    )
                    self._previousTopicCount = 0
            self._eventQueue.put(request)

        def asyn(topic):
            return send_event

        def sync(topic):
            def sync_event(*args, **kwargs):
                send_event(*args, **kwargs)

                while True:
                    error = self._errorQueue.get_nowait()
                    if error is None:
                        result = self._resultQueue.get_nowait()
                        if result is None:
                            time.sleep(SLEEP)  # Don't eat all CPU.
                            continue
                        if len(result) > 1:
                            return result
                        return result[0]
                    else:
                        # Error occured.
                        cls_Exception, reason = error
                        _raiseError(cls_Exception, reason)

            return sync_event

        if topic.startswith("cached_") or topic.endswith("_sync"):
            setattr(self, topic, sync(topic))
        else:
            setattr(self, topic, asyn(topic))
        return getattr(self, topic)

    def help(self) -> None:
        print("Available events:")
        docstrings = self.str_help_sync()
        for name, docstring in sorted(docstrings.items()):
            print("- %s: %s" % (name, docstring))

    help_sync = help


class Receiver(object):
    """Honor events."""

    def __init__(self, name: str, event: Queue, result: Queue, error: Queue):
        self._name = name
        self._eventChan = Channel(event)
        self._resultQueue = result
        self._errorQueue = error

        self._reactMap = {}
        self._cache = {}  # Cached values.
        self._previousTopic = None
        self._previousTopicCount = 0

    def _debug(self, msg: str):
        runtime.ui.debugC(EMT, "receiver [%s] %s" % (self._name, msg))

    def _help(self, topic: str, args, kwargs):
        docstrings = {}
        for name, rargs in self._reactMap.items():
            func, rargs = self._reactMap[name]
            docstrings[func.__name__] = func.__doc__
        return docstrings

    def _react(self, topic: str, args, kwargs):
        func, rargs = self._reactMap[topic]
        args = rargs + args

        # Enable debug retention if too many messages.
        if self._previousTopic != topic:
            if self._previousTopicCount > 0:
                self._debug(f"reacted {self._previousTopicCount} times to '{self._previousTopic}'")
            self._previousTopicCount = 0
            self._previousTopic = topic
            self._debug(f"reacting to '{topic}' with '{func.__name__}', {args}, {kwargs}")

        else:
            self._previousTopicCount += 1
            if self._previousTopicCount == 2:
                self._debug(f"reacting to '{topic}' again, further messages made silent")
            if self._previousTopicCount > (_SILENT_TIMES - 1):
                self._debug(
                    f"reacting for the {_SILENT_TIMES}th time to '{topic}' with '{func.__name__}', {args}, {kwargs}"
                )
                self._previousTopicCount = 0

        return func(*args, **kwargs)

    def accept(self, event: str, func: callable, *args) -> None:
        self._reactMap[event] = (func, args)

    def react(self) -> bool:
        """Process events in order.

        The order of events is the order of the **available** events in the queue.
        This is relevant only when *sending* events concurrently (from different workers)."""

        for event in self._eventChan:
            topic, args, kwargs = event
            try:

                if topic == "stopServing":
                    self._debug("marked as stop serving")
                    return False

                # Async mode.
                if topic in self._reactMap:
                    self._cache[topic] = self._react(topic, args, kwargs)
                    return True

                # Sync modes.
                elif topic.startswith("cached_") or topic.endswith("_sync"):
                    try:
                        if topic.startswith("cached_"):
                            # TODO: warn if arguments.
                            realTopic = topic[7:]
                            if realTopic.endswith("_sync"):
                                realTopic = realTopic[:-5]

                            if realTopic in self._cache:
                                result = self._cache[realTopic]
                            else:
                                raise TopicError(f"{self._name}: '{topic}' is called while no cached value.")

                        else:
                            realTopic = topic[:-5]  # "_sync"

                            if realTopic in self._reactMap:
                                result = self._react(realTopic, args, kwargs)
                            elif realTopic == "str_help":
                                result = self._help(realTopic, args, kwargs)
                            else:
                                raise TopicError("%s got unkown event '%s'" % (self._name, topic))

                        # Send result back to emitter.
                        if type(result) != tuple:
                            result = (result,)
                        self._resultQueue.put(result)
                        return True

                    except TopicError as e:
                        runtime.ui.error(str(e))
                        self._errorQueue.put((AttributeError, str(e)))

                runtime.ui.error("receiver %s unhandled event %s" % (self._name, event))

            except KeyboardInterrupt:
                raise
            except Exception as e:
                runtime.ui.critical(
                    "%s unhandled error occurred while"
                    " reacting to event %s: %s: %s" % (self._name, event, e.__class__.__name__, e)
                )
                runtime.ui.exception(e)
                if topic.endswith("_sync"):
                    self._errorQueue.put((e.__class__, str(e)))

        time.sleep(SLEEP)  # Don't eat all CPU if caller is looping here.
        return True


class SyncEmitter(object):
    """Adaptater emitter to turn an emitter into sync mode only."""

    def __init__(self, emitter):
        self._emitter = emitter

    def __getattr__(self, name):
        return getattr(self._emitter, "%s_sync" % name)


def newEmitterReceiver(debugName: str) -> (Receiver, Emitter):
    eventQueue = runtime.concurrency.createQueue()
    resultQueue = runtime.concurrency.createQueue()
    errorQueue = runtime.concurrency.createQueue()

    emitter = Emitter(debugName, eventQueue, resultQueue, errorQueue)
    receiver = Receiver(debugName, eventQueue, resultQueue, errorQueue)
    return receiver, emitter


if __name__ == "__main__":
    # Run this demo like this (from the root directory):
    # python3 -m imapfw.edmp
    #
    # We catch exception since it's run as a test in travis.

    _DEBUG = True  # Set to True for more output and stack trace on error.

    import sys
    from imapfw.concurrency.concurrency import Concurrency
    from imapfw.ui.tty import TTY

    c = Concurrency()
    ui = TTY(c.createLock())
    ui.configure()
    if _DEBUG:
        ui.enableDebugCategories(["emitters"])
    ui.setCurrentWorkerNameFunction(c.getCurrentWorkerNameFunction())

    runtime.set_module("ui", ui)
    runtime.set_module("concurrency", c)

    def run_async():
        ui.info("******** running run_async()")

        __REMOTE__ = "http://imapfw.github.io"
        __CONNECTED__ = "would be connected"
        driverReceiver, driverEmitter = newEmitterReceiver("driver")

        def connect(remote, port):
            print("would connect to %s:%s" % (remote, port))
            assert remote == __REMOTE__
            assert port == 80
            return __CONNECTED__

        driverReceiver.accept("connect", connect)

        driverEmitter.connect(__REMOTE__, 80)
        driverEmitter.stopServing()

        # Blocking loop to react to all events.
        react = True
        while react:
            react = driverReceiver.react()
        print("driver stopped reacting")

    def run_sync():
        ui.info("******** running run_sync()")

        __REMOTE__ = "http://imapfw.offlineimap.org"
        __CONNECTED__ = "would be connected"

        def runner(receiver):
            def connect(remote, port):
                """docstring of connect"""
                print("would connect to %s:%s" % (remote, port))
                assert remote == __REMOTE__
                assert port == 80
                return __CONNECTED__

            receiver.accept("connect", connect)

            # Blocking loop to react to all events.
            react = True
            while react:
                react = driverReceiver.react()
            print("driver stopped reacting")

        driverReceiver, driverEmitter = newEmitterReceiver("driver")

        worker = c.createWorker("Worker", runner, (driverReceiver,))
        worker.start()

        try:
            driverEmitter.connect(__REMOTE__, 80)
            cached = driverEmitter.cached_connect()
            print("got from cached_connect: %s" % cached)
            assert cached == __CONNECTED__

            value = driverEmitter.connect_sync(__REMOTE__, 80)
            print("got from connect_sync: %s" % value)
            assert value == __CONNECTED__

            docstrings = driverEmitter.str_help_sync()
            print("displaying docstrings:")
            for name, doc in docstrings.items():
                print("- %s: %s" % (name, doc))

            driverEmitter.stopServing()
        except:
            worker.kill()
            raise
        worker.join()

    try:
        run_async()
        run_sync()
        sys.exit(0)
    except Exception as e:
        ui.exception(e)
        sys.exit(1)

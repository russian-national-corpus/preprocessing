#!/usr/bin/env python
# -*- Encoding: windows-1251 -*-

import os
import time
from functools import wraps
import string

__all__ = ['time_me', 'Registrator', 'getAllFiles', 'MemoryDataBuffer']

def str_time(period):
    data = ['%f sec.' % (period % 60.0)]
    period = int(period // 60.0)
    min = period % 60
    if min != 0:
        data.append('%d min.' % min)
    period //= 60
    hour = period
    if hour != 0:
        data.append('%d h.' % hour)
    return ' '.join(data[::-1])

def time_me(func):
    """The time_me decorator.
    Computes working time of a function call."""
    @wraps(func)
    def timed(*args, **kwargs):
        start = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            print "%s.%s: %s" % (func.__module__, func.__name__, str_time(time.time() - start))
    return timed

class Registrator:
    """Decorator class:
    allows register anything to a sequences of hashable objects (keys);
    the registered object can be retrieved by one of the keys."""
    def __init__(self):
        self.__reg = {}

    def __call__(self, *keys):
        """Register (function) with given keys."""
        def wrapper(func):
            for key in keys:
                self.__reg[key] = func
            return func
        return wrapper

    def get(self, key):
        """Retrieve the registered object by key."""
        return self.__reg.get(key)

def getAllFiles(indir):
    """Retrieves recursively all file names in given directory."""
    # functions shortcuts
    isdir = os.path.isdir
    isfile = os.path.isfile
    path_join = os.path.join

    subdirs = []
    files = []
    if isdir(indir):
        subdirs.append(indir)
    else:
        files.append(indir)

    while subdirs:
        indir = subdirs.pop(0)
        listdir = [path_join(indir, f) for f in os.listdir(indir)]
        subdirs.extend(f for f in listdir if isdir(f))
        files.extend(f for f in listdir if isfile(f))

    files.sort()
    return files

class MemoryDataBuffer:
    """ Allows to make sequential object store in memory.
    On objects storage, a handler (methods) name is needed.
    When data is flushed to handler, data is passed in FIFO manner;
    handlers attribute with mentioned name is needed.
    """
    def __init__(self):
        self.__buffer = []

    def Store(self, methodName, *args, **kwargs):
        self.__buffer.append((methodName, args, kwargs))

    def Flush(self, handler):
        for data in self.__buffer:
            method = getattr(handler, data[0])
            assert method is not None
            method(*data[1], **data[2])
        self.__buffer = []

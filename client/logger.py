#!/usr/bin/env python3

"""
Handle logging

All logging is done througt QT signal/slots, so they can be used from other threads.

Copyright (C) 2020 Anders Lowinger, anders@abundo.se

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import datetime
import threading
import logging

import PyQt5.QtCore as QtCore

from myglobals import *
from lib.log import *


_INFO = 0
_WARNING = 1
_ERROR = 2
_DEBUG = 3
_CONSOLE = 4

INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
DEBUG = logging.DEBUG

level_dict = {"nfo": logging.INFO,
              "warning": logging.WARNING,
              "error": logging.ERROR,
              "debug": logging.DEBUG}


# class QtLogHandler(logging.StreamHandler):
class QtLogHandler(logging.Handler):
    """
    Custom logging.Handler that outputs logging to a QT widget
    """
    def __init__(self):
        super().__init__(self)
        self.out = None
        self._lines = []    # temp buffer until we have an output device
        self._qtwidget = None

    def setQtwidget(self, qtwidget):
        self._qtwidget = qtwidget
        for line in self._lines:
            self._qtwidget.appendPlainText(line)
        self._lines = []

    def emit(self, record):
        log_entry = self.format(record)
        if self.out is not None:
            self.out.appendPlainText(log_entry)
        else:
            self._lines.append(log_entry)
            print(log_entry)


class Log(QtCore.QObject):
    """
    Log handler. Uses signals to be thread safe
    Modeled so stdout/stderr can be directed to this class
    """
    logTrigger = QtCore.pyqtSignal(int, str, str)

    def __init__(self):
        super().__init__()
        self.out = None
        self.levels = ["INFO", "WARNING", "ERROR", "DEBUG", "CONSOLE"]
        self.level = _CONSOLE
        self.logTrigger.connect(self.log)
        self._lines = []    # temp buffer until we have an output device

    def setOut(self, out):
        self.out = out
        for line in self._lines:
            self.out.appendPlainText(line)
        self._lines = []

    def setLevel(self, level):
        self.level = level

    def log(self, level, threadname, msg):
        if level <= self.level:
            now = datetime.datetime.now().strftime("%Y-%m-%db %H:%M:%S")
            line = "%s %s %s %s" % (now, threadname, self.levels[level], msg)
            if self.out is None:
                self._lines.append(line)
                print(line)
            else:
                self.out.appendPlainText(line)

    def info(self, msg):
        self.logTrigger.emit(_INFO, threading.current_thread().getName(), msg)

    def warning(self, msg):
        self.logTrigger.emit(_WARNING, threading.current_thread().getName(), msg)

    def error(self, msg):
        self.logTrigger.emit(_ERROR, threading.current_thread().getName(), msg)

    def debug(self, msg):
        self.logTrigger.emit(_DEBUG, threading.current_thread().getName(), msg)

    def debugf(self, mask, msg):
        """
        Show debug message, if debug for this type is enabled
        """
        if DEBUG_LEVEL & mask:
            self.logTrigger.emit(_DEBUG, threading.current_thread().getName(), msg)

    def write(self, msg):
        msg = msg.strip()
        if msg:
            self.logTrigger.emit(_CONSOLE, threading.current_thread().getName(), msg.strip())

    def flush(self):
        # this is defined so we can redirect stdout/stderr here without warnings
        pass


log = Log()


def setLevel(level):
    if isinstance(level, str):
        level = level_dict[level]
    logger.setLevel(level)


def info(msg):
    msg = str(msg).replace("\n", ", ")
    logger.info(msg)


def warning(msg):
    msg = str(msg).replace("\n", ", ")
    logger.warning(msg)


def error(msg):
    msg = str(msg).replace("\n", ", ")
    logger.error(msg)


def debug(msg):
    try:
        msg = str(msg).replace("\n", ", ")
    except UnicodeDecodeError:
        return
    logger.debug(msg)


formatstr = "%(asctime)s %(levelname)s %(message)s "
loglevel = logging.INFO
logger = logging.getLogger("ergotime")
logger.setLevel(loglevel)

# remove all handlers
for hdlr in logger.handlers:
    logger.removeHandler(hdlr)

consolehandler = logging.StreamHandler()

formatter = logging.Formatter(formatstr)
consolehandler.setFormatter(formatter)
logger.addHandler(consolehandler)

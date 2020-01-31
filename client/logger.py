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

import PyQt5.QtCore as QtCore
import PyQt5.QtWidgets as QtWidgets


class Log(QtCore.QObject):
    """
    Log handler. Uses signals to be thread safe
    Modeled so stdout/stderr can be directed to this class
    """

    # Possible debug subsystems
    DEBUG_FILES             = 1 << 0
    DEBUG_SETTINGS          = 1 << 1
    DEBUG_ACTIVITYMGR       = 1 << 3
    DEBUG_REPORTMGR         = 1 << 4
    DEBUG_MAINWIN           = 1 << 5
    DEBUG_OPTIONS           = 1 << 6
    DEBUG_SYSTRAY           = 1 << 7

    # Setup debug bitmask
    DEBUG_LEVEL = 0
    DEBUG_LEVEL |= DEBUG_FILES       * 0
    DEBUG_LEVEL |= DEBUG_SETTINGS    * 0
    DEBUG_LEVEL |= DEBUG_ACTIVITYMGR * 1
    DEBUG_LEVEL |= DEBUG_REPORTMGR   * 1
    DEBUG_LEVEL |= DEBUG_MAINWIN     * 1
    DEBUG_LEVEL |= DEBUG_OPTIONS     * 1
    DEBUG_LEVEL |= DEBUG_SYSTRAY     * 1

    logTrigger = QtCore.pyqtSignal(int, str, str)

    INFO = 0
    WARNING = 1
    ERROR = 2
    DEBUG = 3
    CONSOLE = 4

    # Map from string to log level
    level_dict = {
        "info": INFO,
        "warning": WARNING,
        "error": ERROR,
        "debug": DEBUG,
        "console": CONSOLE,
    }

    def __init__(self):
        super().__init__()
        self.out = None     # QT Widget for log output
        self.levels = ["INFO", "WARNING", "ERROR", "DEBUG", "CONSOLE"]
        self.level = self.CONSOLE
        self.logTrigger.connect(self.log)
        self._lines = []    # temp buffer until we have an output device

    def add_row(self, line):
        c = self.out.rowCount()
        self.out.setRowCount(c + 1)
        self.out.setItem(c, 0, QtWidgets.QTableWidgetItem(line[0]))
        self.out.setItem(c, 1, QtWidgets.QTableWidgetItem(line[1]))
        self.out.setItem(c, 2, QtWidgets.QTableWidgetItem(line[2]))
        self.out.setItem(c, 3, QtWidgets.QTableWidgetItem(line[3]))
        if c > 500:
            self.out.removeRow(0)
        self.out.resizeColumnsToContents()
        self.out.scrollToBottom()

    def setOut(self, out):
        self.out = out
        for line in self._lines:
            self.add_row(line)
        self._lines = []

    def setLevel(self, level):
        if isinstance(level, str):
            level = self.level_dict[level]
        self.level = level

    def log(self, level, threadname, msg):
        if level <= self.level:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            msg = str(msg).replace("\n", ", ")
            line = [now, threadname, self.levels[level], msg]
            if self.out is None:
                self._lines.append(line)
                print(" ".join(line))
            else:
                self.add_row(line)

    def info(self, msg):
        self.logTrigger.emit(self.INFO, threading.current_thread().getName(), msg)

    def warning(self, msg):
        self.logTrigger.emit(self.WARNING, threading.current_thread().getName(), msg)

    def error(self, msg):
        self.logTrigger.emit(self.ERROR, threading.current_thread().getName(), msg)

    def debug(self, msg):
        self.logTrigger.emit(self.DEBUG, threading.current_thread().getName(), msg)

    def debugf(self, mask, msg):
        """
        Show debug message, if debug for this type is enabled
        """
        if self.DEBUG_LEVEL & mask:
            self.logTrigger.emit(self.DEBUG, threading.current_thread().getName(), msg)

    def write(self, msg):
        msg = msg.strip()
        if msg:
            self.logTrigger.emit(self.CONSOLE, threading.current_thread().getName(), msg.strip())

    def flush(self):
        # this is defined so we can redirect stdout/stderr here without warnings
        pass


log = Log()

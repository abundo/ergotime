#!/usr/bin/env python3

"""
Manage settings and their persistence to disk

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

import os
import getpass
import inspect

import PyQt5.QtCore as QtCore
from PyQt5.Qt import QByteArray

from logger import log

NO_DEFAULT = QtCore.QObject()


class AttrTypDefault:
    def __init__(self, type, default=NO_DEFAULT):
        self.type = type
        self.default = default


class MySettings(QtCore.QObject):

    updated = QtCore.pyqtSignal()

    main_win_pos           = AttrTypDefault(QtCore.QPoint, QtCore.QPoint(100, 100))
    main_win_size          = AttrTypDefault(QtCore.QSize, QtCore.QSize(600, 400))
    main_win_splitter_1    = AttrTypDefault(QByteArray, NO_DEFAULT)

    fontName               = AttrTypDefault(str, "MS Shell Dlg 2")
    fontSize               = AttrTypDefault(str, "9")
    username               = AttrTypDefault(str, getpass.getuser())
    password               = AttrTypDefault(str, "")
    idle_timeout           = AttrTypDefault(int, 600)
    database_dir           = AttrTypDefault(str, "")
    loglevel               = AttrTypDefault(str, "INFO")

    activity_sync_interval = AttrTypDefault(int, 600)

    report_sync_interval   = AttrTypDefault(int, 600)

    server_url             = AttrTypDefault(str, "http://ergotime.int.abundo.se")
    networkTimeout         = AttrTypDefault(int, 60)

    userdir                = AttrTypDefault(str, os.path.expanduser("~") + os.sep + ".ergotime")
    userconffile           = AttrTypDefault(str, "")
    localDatabaseName      = AttrTypDefault(str, "ergotime.db")

    def _attriter(self):
        """
        Iterate through all settings
        """
        for var in vars(self):
            tmp = getattr(self, var)
            print(var, type(tmp))

    def __init__(self):
        super().__init__()
        self._settings = {}

        # Create datadir in the users home directory
        if not os.path.exists(self.userdir.default):
            os.mkdir(self.userdir.default)
        userconffile = self.userdir.default + os.sep + "ergotime.ini"

        if log.DEBUG_LEVEL & log.DEBUG_FILES:
            self.localDatabaseName.default = "ergotime-devel.db"
        self.localDatabaseName.default = self.userdir.default + os.sep + self.localDatabaseName.default

        self.qsettings = QtCore.QSettings(userconffile, QtCore.QSettings.IniFormat)
        self.qsettings.setFallbacksEnabled(False)
        log.debugf(log.DEBUG_SETTINGS, "Settings stored in file %s" % self.qsettings.fileName())

        # Go through all supperted settings and load them
        # This creates instance variables overriding the class variables
        for name, value in inspect.getmembers(self):
            if isinstance(value, AttrTypDefault):
                self._settings[name] = value

        for attr, atd in self._settings.items():
            if atd.default != NO_DEFAULT:
                value = self.qsettings.value(attr, atd.default, type=atd.type)
            else:
                value = self.qsettings.value(attr, type=atd.type)
            log.debugf(log.DEBUG_SETTINGS, "Loaded setting %s = %s" % (attr, value))
            object.__setattr__(self, attr, value)

        self.runFromIde = "runFromIde" in os.environ     # todo find out automatically if we are running from the IDE

    def __setattr__(self, attr, value):
        try:
            atd = self._settings[attr]
            log.debugf(log.DEBUG_SETTINGS, "Storing setting %s,%s = %s" % (attr, str(atd.type), value))
            if value != atd.default or value != getattr(self, attr):    # only write non-default values
                self.qsettings.setValue(attr, value)
                object.__setattr__(self, attr, value)
                return
        except (ValueError, AttributeError, KeyError):
            object.__setattr__(self, attr, value)

    def contains(self, attr):
        if attr in self._settings:
            value = hasattr(self, attr)
            return value != NO_DEFAULT
        return False

    def sync(self):
        self.qsettings.sync()
        self.updated.emit()


sett = MySettings()

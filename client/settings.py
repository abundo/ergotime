#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Manage settings and their persistence to disk
'''

'''
Copyright (c) 2013, Anders Lowinger, Abundo AB
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
   * Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.
   * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.
   * Neither the name of the <organization> nor the
     names of its contributors may be used to endorse or promote products
     derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

import getpass
import inspect

import PyQt5.QtCore as QtCore
from PyQt5.Qt import QByteArray

from myglobals import *
from logger import log

NO_DEFAULT = QtCore.QObject()

class AttrTypDefault:
    def __init__(self, type, default=NO_DEFAULT):
        self.type = type
        self.default = default


class MySettings(QtCore.QObject):

    updated = QtCore.pyqtSignal()
    
    main_win_pos           = AttrTypDefault(QtCore.QPoint, QtCore.QPoint(100,100))
    main_win_size          = AttrTypDefault(QtCore.QSize, QtCore.QSize(600,400))
    main_win_splitter_1    = AttrTypDefault(QByteArray, NO_DEFAULT)
    
    fontName               = AttrTypDefault(str, "MS Shell Dlg 2")
    fontSize               = AttrTypDefault(str, "9")
    username               = AttrTypDefault(str, getpass.getuser())
    password               = AttrTypDefault(str, "")
    idle_timeout           = AttrTypDefault(int, 600)
    database_dir           = AttrTypDefault(str, "")      # todo userdir + ".ergotime"
    loglevel               = AttrTypDefault(str, "INFO")
    
    activity_sync_interval = AttrTypDefault(int, 600)
    
    report_sync_interval   = AttrTypDefault(int, 600)
    
    server_url             = AttrTypDefault(str, "http://ergotime.int.abundo.se")
    networkTimeout         = AttrTypDefault(int, 60)

    localDatabaseName      = localDatabaseName

    def _attriter(self):
        """
        Iterate through all settings
        """
        for var in vars(self):
            tmp = getattr(self, var)
            print(var, type(tmp))
            #if inspect.isclass(tmp, AttrTypDefault):
            #    yield var, tmp

    def __init__(self):
        super().__init__()
        self._settings = {}
        self.qsettings = QtCore.QSettings(userconffile, QtCore.QSettings.IniFormat)
        self.qsettings.setFallbacksEnabled(False)
        log.debugf(DEBUG_SETTINGS, "Settings stored in file %s" % self.qsettings.fileName())
        
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
            log.debugf(DEBUG_SETTINGS, "Loaded setting %s = %s" % (attr, value))
            object.__setattr__(self, attr, value)

    def __setattr__(self, attr, value):
        try:
            atd = self._settings[attr]
            log.debugf(DEBUG_SETTINGS, "Storing setting %s,%s = %s" % (attr, str(atd.type), value))
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

'''
Created on 13 nov 2013

@author: anders
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


class MySettings:
    
    main_win_pos           = AttrTypDefault(QtCore.QPoint, QtCore.QPoint(100,100))
    main_win_size          = AttrTypDefault(QtCore.QSize, QtCore.QSize(600,400))
    main_win_splitter_1    = AttrTypDefault(QByteArray, NO_DEFAULT)
    main_win_splitter_2    = AttrTypDefault(QByteArray, NO_DEFAULT)
    
    #font
    username               = AttrTypDefault(str, getpass.getuser())
    password               = AttrTypDefault(str, "")
    idle_timeout           = AttrTypDefault(int, 600)
    database_dir           = AttrTypDefault(str, "")      # todo userdir + ".ergotime"
    loglevel               = AttrTypDefault(str, "INFO")
    
    activity_sync_interval = AttrTypDefault(int, 600)
    
    report_sync_interval   = AttrTypDefault(int, 600)
    
    server_url             = AttrTypDefault(str, "http://ergotime.int.abundo.se:8000/")
    networkTimeout         = AttrTypDefault(int, 60)


    def _attriter(self):
        """Iterate through all settings"""
        
        for var in vars(self):
            tmp = getattr(self, var)
            print(var, type(tmp))
            #if inspect.isclass(tmp, AttrTypDefault):
            #    yield var, tmp

    def __init__(self):
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
            atd = self._setting[attr]
            log.debugf(DEBUG_SETTINGS, "Storing setting %s,%s = %s" % (attr, str(atd.type), value))
            if value != atd.default or value != getattr(self, attr):    # only write non-default values
                self.qsettings.setValue(attr, value)
                object.__setattr__(self, attr, value)
                return
        except (ValueError, AttributeError):
            object.__setattr__(self, attr, value)

    def contains(self, attr):
        if attr in self._settings:
            value = hasattr(self, attr)
            return value != NO_DEFAULT
        return False
    
    def sync(self):
        self.qsettings.sync()

sett = MySettings()


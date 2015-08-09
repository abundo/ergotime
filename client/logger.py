#!/usr/bin/env python
# -*- coding: utf-8 -*-

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


import datetime
import threading

import PyQt5.QtCore as QtCore

from myglobals import *

_INFO=0
_WARNING=1
_ERROR=2
_DEBUG=3
_CONSOLE=4

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
        self.level = _CONSOLE    # todo, from settings
        self.logTrigger.connect(self.log)
        self._lines = [] # temp buffer until we have an output device

    def setOut(self, out):
        self.out = out
        for line in self._lines:
            self.out.appendPlainText(line)
        self._lines = []
    
    def setLevel(self, level):
        self.level = level

    def log(self, level, threadname, msg):
        if level <= self.level:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            line = "%s %s %s %s" % (now, threadname, self.levels[level], msg)
            if self.out != None:
                self.out.appendPlainText(line)
            else:
                self._lines.append(line)
                print(line)

    def info(self, msg):
        self.logTrigger.emit(_INFO, threading.current_thread().getName(), msg)
        
    def warning(self, msg):
        self.logTrigger.emit(_WARNING, threading.current_thread().getName(), msg)
        
    def error(self, msg):
        self.logTrigger.emit(_ERROR, threading.current_thread().getName(), msg)
    
    def debug(self, msg):
        self.logTrigger.emit(_DEBUG, threading.current_thread().getName(), msg)

    def debugf(self, mask, msg):
        if DEBUG & mask:
            self.logTrigger.emit(_DEBUG, threading.current_thread().getName(), msg)

    def write(self, msg):
        msg = msg.strip()
        if msg:
            self.logTrigger.emit(_CONSOLE, threading.current_thread().getName(), msg.strip())
    
    def flush(self):
        # this is defined so we can redirect stdout/stderr here without warnings
        pass

log = Log()

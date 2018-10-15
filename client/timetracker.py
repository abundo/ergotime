#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Manage tracking of time, timereports
'''

'''
Copyright (c) 2014, Anders Lowinger, Abundo AB
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

import PyQt5.QtCore as QtCore

from myglobals import *
from logger import log
from settings import sett

import idle_dectect


class Status:
    '''Send status info when state=stateActive'''
    def __init__(self):
        self.idle = 0
        self.length = None


class Timetracker(QtCore.QObject):
    '''
    Handle everything related to time tracking
    
    current state
    change state
    sends signals when things change, so GUI can update
    
    when state is active, a _timer periodically checks if user has been idle
    '''
    
    stateStartup  = 1   # Only used during program startup
    stateInactive = 2
    stateActive   = 3
    stateIdle     = 4   # idle state detected (user has been inactive), transitive state goes to inactive when handled

    stateSignal = QtCore.pyqtSignal(int)
    activeUpdated =  QtCore.pyqtSignal(Status)   # signals update to the active state, for GUI to track
    
    def __init__(self, parent=None, activitymgr=None, reportmgr=None):
        super().__init__()
        self.parent = parent
        self.activitymgr = activitymgr
        self.reportmgr = reportmgr

        self.report = parent._getNewReport()
        self._timer = None
        
        self.idleStartTime = None
        self.currentReport = None
        
        self.state = self.stateStartup
        self._status = Status()
    
    def init(self):
        self.setStateInactive()
    
    def setStateInactive(self):
        '''User clicked Stop'''
        
        if self.state == self.stateStartup:
            self.state = self.stateInactive
            self.stateSignal.emit(self.stateInactive)

        elif self.state == self.stateInactive:
            log.error('Incorrect state change, inactive->inactive')

        elif self.state == self.stateActive:
            self._timer.stop()
            self._timer = None
            self._saveReport()
            
            self.state = self.stateInactive
            self.stateSignal.emit(self.stateInactive)

        elif self.state == self.stateIdle:
            log.error('Incorrect state change, inactive->idle')
        else:
            log.error('Incorrect state %s' % self.state)
    
    def setStateActive(self, report=None):
        '''User clicked Start'''
        if self.state == self.stateInactive:
            self.report = report
            self._timer = QtCore.QTimer()
            self._timer.timeout.connect(self._update)
            self._update()
            self._timer.start(1000)
            
            self.state = self.stateActive
            self.stateSignal.emit(self.stateActive)

        elif self.state == self.stateActive:
            log.error('Incorrect state change, active->active')
        
        elif self.state == self.stateIdle:
            log.error('Incorrect state change, active->idle')
        else:
            log.error('Incorrect state %s' % self.state)

    def setStateIdle(self):
        '''
        Idle detected, save current report and go to Inactive
        This is an internal state, external GUI only knows about Inactive/Active
        Subtract the idle period before going to inactive
        '''
        if self.state == self.stateInactive:
            log.error('Incorrect state change, inactive->idle')
            
        elif self.state == self.stateActive:
            self._timer.stop()
            self._timer = None
            self._saveReport(subtract_seconds=sett.idle_timeout)
            self.state = self.stateInactive
            self.stateSignal.emit(self.stateInactive)

        elif self.state == self.stateIdle:
            log.error('Incorrect state change, idle->idle')
            return
        else:
            log.error('Incorrect state %s' % self.state)

    def _saveReport(self, subtract_seconds=0):
        log.debug('Saving report %s' % self.report)
        self.report.stop = datetime.datetime.now().replace(microsecond=0) - datetime.timedelta(seconds=subtract_seconds)
        self.reportmgr.store(self.report)

    def _seconds_to_time(self, seconds):
        hour, remainder = seconds // 3600, seconds % 3600
        minute, second = remainder // 60, remainder % 60   
        return datetime.time(hour, minute, second)
                    
    def _update(self):
        '''
        Called every second when state == stateActive
        Check if idle
        '''
        self.report.stop = datetime.datetime.now().replace(microsecond=0)
        td = self.report.stop - self.report.start
        self._status.length = self._seconds_to_time(td.seconds)

        idle_seconds = idle_dectect.getIdle()
        self._status.idle = self._seconds_to_time(idle_seconds)      
        if idle_seconds > sett.idle_timeout:
            log.info('Idle timeout detected')
            self.setStateIdle()
            return

        self.activeUpdated.emit(self._status)
        
    def options_changed(self):
        '''Called when user changes options'''
        pass

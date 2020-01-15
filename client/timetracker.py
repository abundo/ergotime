#!/usr/bin/env python3

"""
Manage tracking of time, timereports

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

import PyQt5.QtCore as QtCore

from myglobals import *
from logger import log
from settings import sett

import idle_dectect


class Status:
    """
    Send status info when state=stateActive
    """
    def __init__(self):
        self.idle = 0
        self.length = None


class Timetracker(QtCore.QObject):
    """
    Handle everything related to time tracking

    current state
    change state
    sends signals when things change, so GUI can update

    when state is active, a _timer periodically checks if user has been idle
    """

    stateStartup  = 1   # Only used during program startup
    stateInactive = 2
    stateActive   = 3
    stateIdle     = 4   # idle state detected (user has been inactive), transitive state goes to inactive when handled

    stateSignal = QtCore.pyqtSignal(int)
    activeUpdated = QtCore.pyqtSignal(Status)   # signals update to the active state, for GUI to track

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
        """
        User clicked Stop
        """

        if self.state == self.stateStartup:
            self.state = self.stateInactive
            self.stateSignal.emit(self.stateInactive)

        elif self.state == self.stateInactive:
            log.error("Incorrect state change, inactive->inactive")

        elif self.state == self.stateActive:
            self._timer.stop()
            self._timer = None
            self._saveReport()

            self.state = self.stateInactive
            self.stateSignal.emit(self.stateInactive)

        elif self.state == self.stateIdle:
            log.error("Incorrect state change, inactive->idle")
        else:
            log.error("Incorrect state %s" % self.state)

    def setStateActive(self, report=None):
        """
        User clicked Start
        """
        if self.state == self.stateInactive:
            self.report = report
            self._timer = QtCore.QTimer()
            self._timer.timeout.connect(self._update)
            self._update()
            self._timer.start(1000)

            self.state = self.stateActive
            self.stateSignal.emit(self.stateActive)

        elif self.state == self.stateActive:
            log.error("Incorrect state change, active->active")

        elif self.state == self.stateIdle:
            log.error("Incorrect state change, active->idle")
        else:
            log.error("Incorrect state %s" % self.state)

    def setStateIdle(self):
        """
        Idle detected, save current report and go to Inactive
        This is an internal state, external GUI only knows about Inactive/Active
        Subtract the idle period before going to inactive
        """
        if self.state == self.stateInactive:
            log.error("Incorrect state change, inactive->idle")

        elif self.state == self.stateActive:
            self._timer.stop()
            self._timer = None
            self._saveReport(subtract_seconds=sett.idle_timeout)
            self.state = self.stateInactive
            self.stateSignal.emit(self.stateInactive)

        elif self.state == self.stateIdle:
            log.error("Incorrect state change, idle->idle")
        else:
            log.error("Incorrect state %s" % self.state)

    def _saveReport(self, subtract_seconds=0):
        log.debug("Saving report %s" % self.report)
        self.report.stop = datetime.datetime.now().replace(microsecond=0) - datetime.timedelta(seconds=subtract_seconds)
        self.reportmgr.store(self.report)

    def _seconds_to_time(self, seconds):
        hour, remainder = int(seconds // 3600), int(seconds % 3600)
        minute, second = int(remainder // 60), int(remainder % 60)
        return datetime.time(hour, minute, second)

    def _update(self):
        """
        Called every second when state == stateActive
        Check if idle
        """
        self.report.stop = datetime.datetime.now().replace(microsecond=0)
        td = self.report.stop - self.report.start
        self._status.length = self._seconds_to_time(td.seconds)

        idle_seconds = idle_dectect.get_idle()
        self._status.idle = self._seconds_to_time(idle_seconds)
        if idle_seconds > sett.idle_timeout:
            log.info("Idle timeout detected")
            self.setStateIdle()
            return

        self.activeUpdated.emit(self._status)

    def options_changed(self):
        """
        Called when user changes options
        """
        pass

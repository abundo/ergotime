#!/usr/bin/env python3

"""
GUI systray

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

import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets

from myglobals import *
from logger import log


class Systray(QtWidgets.QWidget):

    def __init__(self, timetracker=None, activitymgr=None):
        super().__init__()

        self.timetracker = timetracker
        self.activitymgr = activitymgr

        self.trayicon = QtWidgets.QSystemTrayIcon()
        self.icon = QtGui.QIcon(":/resource/tray-inactive.png")
        self.trayicon.setIcon(self.icon)

        self.noaction = QtWidgets.QAction(self)
        self.noaction.setText("No activity")
        self.noaction.setCheckable(True)
        self.noaction.setData(-1)

        self.timetracker.stateSignal.connect(self.stateChanged)

        self.activitymgr.sig.connect(self.activityListUpdated)
        self.activityListUpdated()

    def activityListUpdated(self):
        """
        Called when the list of activities has been updated, usually after sync with server
        """
        trayiconmenu = QtWidgets.QMenu()

        for activity in self.activitymgr.getList():
            if activity.active:
                action = QtWidgets.QAction(self)
                action.setText(activity.name)
                action.setData(activity._id)
                action.setCheckable(True)
                # connect
                action.triggered.connect(self.setAction)
                trayiconmenu.addAction(action)

        trayiconmenu.addSeparator()
        trayiconmenu.addAction(self.noaction)
        trayiconmenu.addSeparator()
        action = QtWidgets.QAction(self)
        action.setText("Exit")
        trayiconmenu.addAction(action)

        self.trayicon.setContextMenu(trayiconmenu)

        self.trayicon.show()

    def setAction(self):
        log.debugf(DEBUG_SYSTRAY, "setAction()")

    def setNoAction(self):
        log.debugf(DEBUG_SYSTRAY, "setNoAction")

    def updateCheckedAction(self):
        currentactivityid = -1
        menu = self.trayicon.contextMenu()
        for action in menu.actions:
            if action.data() == currentactivityid:
                action.setChecked(True)
            else:
                action.setChecked(False)
        self.noaction.setChecked(currentactivityid < 0)

    def stateChanged(self, state):
        """
        Called when state changes
        """
        if state == self.timetracker.stateInactive:
            pass
        elif state == self.timetracker.stateActive:
            pass

    def updateTooltip(self):
        pass

    def updateStatusActivity(self):
        pass

    def updateStatusReport(self):
        pass

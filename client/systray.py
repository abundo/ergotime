#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
GUI systray
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

#import PyQt5.QtCore as QtCore
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
        self.icon = QtGui.QIcon("resource/tray-inactive.png")
        self.trayicon.setIcon(self.icon)
        
        self.noaction = QtWidgets.QAction(self)
        self.noaction.setText("No activity")
        self.noaction.setCheckable(True)
        self.noaction.setData(-1)

        self.timetracker.stateSignal.connect( self.stateChanged )
        
        self.activitymgr.sig.connect(self.activityListUpdated)
        self.activityListUpdated()


    def activityListUpdated(self):
        """Called when the list of activities has been updated, usually after sync with server"""
        trayiconmenu = QtWidgets.QMenu()
        
        for activity in self.activitymgr.getList():
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
        self.noaction.setChecked( currentactivityid < 0)
    
    def stateChanged(self, state):
        """Called when state changes"""
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


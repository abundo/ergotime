#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
GUI edit options
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

import datetime

import PyQt5.QtCore as QtCore
import PyQt5.QtWidgets as QtWidgets
from PyQt5.Qt import QFont

import report_win

from myglobals import *
from logger import log
from settings import sett

from common.report import Report
#import activitymgr
#import reportmgr

class Report_Win(QtWidgets.QDialog, report_win.Ui_Report):
    
    def __init__(self, parent=None, activityMgr=None, reportMgr=None, report=None, default_date=None):
        super().__init__(parent)
        self.setupUi(self)
        self.activityMgr = activityMgr
        self.reportMgr = reportMgr
        self.default_date = default_date
        if report is not None:
            self.report = report
        else:
            self.report = Report()
            self.report.server_id = -1
            self.report.user_id = 1      # todo, should be updated by server
            self.report.seq = 0
            self.report.deleted = False
            self.report.updated = False
            self.report.modified = datetime.datetime(1990,1,1)
            now = datetime.datetime.now().replace(second=0, microsecond=0).time()
            self.report.start = datetime.datetime.combine(default_date, now)
            self.report.stop = self.report.start + datetime.timedelta(seconds=30*60)

        # toolbar
        self.btnSave.clicked.connect(self.save)
        self.btnDelete.clicked.connect(self.delete)
        self.btnCancel.clicked.connect(self.cancel)
                
        # fields in grid
        self.comboActivity.currentIndexChanged.connect(self._reportDetailsChangedEvent)
        self.comboProject.currentIndexChanged.connect(self._reportDetailsChangedEvent)
        self.dtStart.dateTimeChanged.connect(self._reportDetailsChangedEvent)
        self.dtStop.dateTimeChanged.connect(self._reportDetailsChangedEvent)
        self.timeLen.dateChanged.connect(self._reportDetailsChangedEvent)
        self.txtComment.textChanged.connect(self._reportDetailsChangedEvent)

        self.dtStart.dateTimeChanged.connect(self._reportDetailsUpdateLength)
        self.dtStop.dateTimeChanged.connect(self._reportDetailsUpdateLength)

        self.btnStartHourPlus.clicked.connect(self._reportDetailsModifyStart)
        self.btnStartHourMinus.clicked.connect(self._reportDetailsModifyStart)
        self.btnStartMinutePlus.clicked.connect(self._reportDetailsModifyStart)
        self.btnStartMinuteMinus.clicked.connect(self._reportDetailsModifyStart)
        
        self.btnStopHourPlus.clicked.connect(self._reportDetailsModifyStop)
        self.btnStopHourMinus.clicked.connect(self._reportDetailsModifyStop)
        self.btnStopMinutePlus.clicked.connect(self._reportDetailsModifyStop)
        self.btnStopMinuteMinus.clicked.connect(self._reportDetailsModifyStop)

        # setup gui activity/project combos
        if self.activityMgr:
            alist = self.activityMgr.getList()
            self.comboActivity.clear()
            for a in alist:
                self.comboActivity.addItem(a.name, a.server_id)

        # Copy report->gui
        s = ""
        if self.report.server_id >= 0:
            s +="on server(%s) " % self.report.server_id
        if self.report.updated:
            s +="locally updated "
        if self.report.deleted:
            s +="to be deleted "
        self.lblSyncState.setText(s)
        if self.report.activityid >= 0:
            self.comboActivity.setCurrentIndex(self.comboActivity.findData(self.report.activityid))
        self.dtStart.setDateTime(self.report.start)
        self.dtStop.setDateTime(self.report.stop)
        self.txtComment.setText(self.report.comment)

        if self.report._id >= 0:
            self.btnDelete.setDisabled(False)
            self.btnSave.setDisabled(False)
        else:
            self.btnDelete.setDisabled(True)
            self.btnSave.setDisabled(True)

        self._changed = False

    def _reportDetailsChangedEvent(self):
        """
        Called when user edits any details of a report
        Save is enabled, delete is disabled
        """
        self._changed = True
        self.btnSave.setDisabled(False)
        self.btnDelete.setDisabled(True)

    def _reportDetailsModifyStart(self):
        """
        Handle the start +H -H +S -S buttons
        """
        sender=self.sender()
        if isinstance(sender, QtWidgets.QToolButton):
            action = sender.text()
            dtstart = self.dtStart.dateTime()
            dtstop = self.dtStop.dateTime()
            if action == "+H":
                sec = 3600
            elif action == "-H":
                sec = -3600
            elif action == "+M":
                sec = 60
            elif action == "-M":
                sec = -60
            self.dtStart.setDateTime(dtstart.addSecs(sec))
            self.dtStop.setDateTime(dtstop.addSecs(sec))

    def _reportDetailsModifyStop(self):
        """
        Handle the stop +H -H +S -S buttons
        """
        sender=self.sender()
        if isinstance(sender, QtWidgets.QToolButton):
            action = sender.text()
            dtstop = self.dtStop.dateTime()
            if action == "+H":
                sec = 3600
            elif action == "-H":
                sec = -3600
            elif action == "+M":
                sec = 60
            elif action == "-M":
                sec = -60
            self.dtStop.setDateTime(dtstop.addSecs(sec))

    def _reportDetailsUpdateLength(self):
        """
        Called when start or stop datetime changed
        """
        start = self.dtStart.dateTime().toPyDateTime()
        stop = self.dtStop.dateTime().toPyDateTime()
        if stop < start:
            # stop can't be before start
            self.dtStop.setDateTime(self.dtStart.dateTime())
        l = (stop - start).total_seconds() / 60
        self.timeLen.setTime(QtCore.QTime(l // 60, l % 60))

    def save(self):
        if self.report._id >= 0:
            self.report.updated = True

        # update report object from GUI
        activityid = self.comboActivity.itemData(self.comboActivity.currentIndex())
        if not activityid or activityid < 1:
            log.warning("Cannot save report, no activity selected")
            return
        self.report.activityid = activityid
        # todo project
        self.report.start = self.dtStart.dateTime().toPyDateTime().replace(microsecond=0)
        self.report.stop = self.dtStop.dateTime().toPyDateTime().replace(microsecond=0)
        self.report.comment = self.txtComment.toPlainText()

        if not self.reportMgr.store(self.report):
            msgBox = QtWidgets.QMessageBox(parent=self)
            msgBox.setText("Error saving report")
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
            response = msgBox.exec_()
            return
        
        self.accept()

    def delete(self):
        msgBox = QtWidgets.QMessageBox(parent=self)
        msgBox.setText("Do you want to delete the report?")
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
        response = msgBox.exec_()

        if response == QtWidgets.QMessageBox.Yes:
            if self.reportMgr.remove(self.report):
                self.accept()
    
    def cancel(self):
        if self._changed:
            msgBox = QtWidgets.QMessageBox(parent=self)
            msgBox.setText("Do you want to cancel your changes?")
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
            response = msgBox.exec_()

            if response != QtWidgets.QMessageBox.Yes:
                return

        self.reject()


if __name__ == '__main__':
    """
    Module test
    """
    app = createQApplication()

    tmp_default_date = datetime.datetime.now().date()
    win = Report_Win(default_date=tmp_default_date)
    win.exec_()

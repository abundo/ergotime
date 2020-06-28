#!/usr/bin/env python3

"""
GUI Window, edit report

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
import PyQt5.QtWidgets as QtWidgets

import report_win

import util
from logger import log

from common.report import Report


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
            self.report.user_id = 1
            self.report.seq = 0
            self.report.deleted = False
            self.report.updated = False
            self.report.modified = datetime.datetime(1990, 1, 1)
            now = datetime.datetime.now().replace(second=0, microsecond=0).time()
            self.report.start = datetime.datetime.combine(default_date, now)
            self.report.stop = self.report.start + datetime.timedelta(seconds=30 * 60)

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
            s += f"on server({self.report.server_id}) "
        if self.report.updated:
            s += "locally updated "
        if self.report.deleted:
            s += "to be deleted "
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
        sender = self.sender()
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
        sender = self.sender()
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
        length = (stop - start).total_seconds() / 60
        self.timeLen.setTime(QtCore.QTime(length // 60, length % 60))

    def save(self):
        if self.report._id >= 0:
            self.report.updated = True

        # update report object from GUI
        activityid = self.comboActivity.itemData(self.comboActivity.currentIndex())
        if not activityid or activityid < 1:
            log.warning("Cannot save report, no activity selected")
            return
        self.report.activityid = activityid
        
        self.report.start = self.dtStart.dateTime().toPyDateTime().replace(microsecond=0)
        self.report.stop = self.dtStop.dateTime().toPyDateTime().replace(microsecond=0)
        self.report.comment = self.txtComment.toPlainText()

        if not self.reportMgr.store(self.report):
            msgbox = QtWidgets.QMessageBox(parent=self)
            msgbox.setText("Error saving report")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.setDefaultButton(QtWidgets.QMessageBox.No)
            msgbox.exec_()
            return

        self.accept()

    def delete(self):
        msgbox = QtWidgets.QMessageBox(parent=self)
        msgbox.setText("Do you want to delete the report?")
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgbox.setDefaultButton(QtWidgets.QMessageBox.No)
        response = msgbox.exec_()

        if response == QtWidgets.QMessageBox.Yes:
            if self.reportMgr.remove(self.report):
                self.accept()

    def cancel(self):
        if self._changed:
            msgbox = QtWidgets.QMessageBox(parent=self)
            msgbox.setText("Do you want to cancel your changes?")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            msgbox.setDefaultButton(QtWidgets.QMessageBox.No)
            response = msgbox.exec_()

            if response != QtWidgets.QMessageBox.Yes:
                return

        self.reject()


if __name__ == "__main__":
    # Module test
    app = util.createQApplication()

    tmp_default_date = datetime.datetime.now().date()
    win = Report_Win(default_date=tmp_default_date)
    win.exec_()

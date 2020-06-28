#!/usr/bin/env python3

"""
GUI Main window

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

import sys
import datetime

import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
from PyQt5.Qt import QFont, QGuiApplication

import util
import options

from logger import log
from settings import sett
from activitymgr import ActivityMgr
from reportmgr import ReportMgr

from common.report import Report

import timetracker
import main_win
import report_main
import systray


class MyStatusBar:
    def __init__(self, ui):
        self.lblStatusIdle = QtWidgets.QLabel()
        ui.statusBar().addWidget(self.lblStatusIdle)

    @property
    def idle(self):
        return self.lblStatusIdle.text()

    @idle.setter
    def idle(self, value):
        self.lblStatusIdle.setText(value)


class MainWin(QtWidgets.QMainWindow, main_win.Ui_Main):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self._restoreWindowPosition()

        self.timetracker = None
        self.activitymgr = None
        self.reportmgr = None

        self.settingsUpdated()

        self._myStatusBar = MyStatusBar(self)

        log.setOut(self.log_table)
        log.info("Log started")
        sys.stdout = log
        sys.stderr = log
        print("STDOUT/STDERR Redirected to log")

        self.color_white = self.dtCurrentStart.palette()
        self.color_white.setColor(QtGui.QPalette.All, QtGui.QPalette.Base, QtGui.QColor(QtCore.Qt.white))

        self.color_yellow = self.dtCurrentStart.palette()
        self.color_yellow.setColor(QtGui.QPalette.All, QtGui.QPalette.Base, QtGui.QColor(QtCore.Qt.yellow))
        self.color_yellow.setColor(QtGui.QPalette.Text, QtCore.Qt.black)

        QtCore.QTimer.singleShot(10, self.delayInit)   # make sure GUI is drawn before we do anything more

    # ########################################################################
    #
    # Misc stuff
    #
    # ########################################################################

    def delayInit(self):
        """
        This is called from event loop, when GUI is fully initialized
        """

        self.localdb = util.openLocalDatabase2()

        self.activitymgr = ActivityMgr(localdb=self.localdb)
        self.reportmgr = ReportMgr(localdb=self.localdb)

        self.activitymgr.init()
        self.reportmgr.init()
        self.timetracker = timetracker.Timetracker(parent=self, activitymgr=self.activitymgr, reportmgr=self.reportmgr)
        self.systray = systray.Systray(timetracker=self.timetracker, activitymgr=self.activitymgr)

        self._initMenu()
        self._initLog()
        self._initActivity()
        self._initCurrentReport()
        self._initReports()
        self.init_report_window()

        self.timetracker.init()

        self._ReportsSetSelectedDateToday()

        self.actionSave_windows_position.triggered.connect(self._saveWindowPosition)
        sett.updated.connect(self.settingsUpdated)

    def settingsDialog(self):
        options1 = options.OptionsWin(self)
        options1.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        options1.exec_()

    def about(self):
        import about
        about = about.AboutWin(self)
        about.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        about.exec_()

    def closeEvent(self, event):
        if self._closeHandler():
            event.accept()
        else:
            event.ignore()

    def _closeHandler(self):
        msgBox = QtWidgets.QMessageBox(parent=self)

        # is there an current activity? it needs to be stopped and saved
        if self.timetracker.state == self.timetracker.stateActive:
            msgBox.setText("There is an activity running, do you want to save this as a report?")
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
            response = msgBox.exec_()
            if response != QtWidgets.QMessageBox.Yes:
                self.timetracker.setStateInactive()

        if not sett.runFromIde:
            # do we have unsyncronised local changes?
            count = self.reportmgr.getUnsyncronisedCount()
            if count > 0:
                msgBox.setText(f"There are {count} reports in local database that needs to be syncronized with the server. Do you want to do this now?")
                msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
                response = msgBox.exec_()
                if response != QtWidgets.QMessageBox.Yes:
                    self.reportmgr.sync()
                    # todo, wait for sync done

        self._saveWindowPosition()
        self.activitymgr.stop()
        self.reportmgr.stop()

        sett.sync()
        QtWidgets.QApplication.exit(0)

    def _saveWindowPosition(self):
        """
        save the current windows position & size in settings
        """
        log.debugf(log.DEBUG_MAINWIN, "Save main window position and size")
        sett.main_win_pos = self.pos()
        sett.main_win_size = self.size()
        sett.main_win_splitter_1 = self.splitter_1.saveState()

    def _restoreWindowPosition(self):
        """
        restore the windows current position & size from settings
        """
        log.debugf(log.DEBUG_MAINWIN, "Restore main window position and size")
        self.move(sett.main_win_pos)
        self.resize(sett.main_win_size)
        self.splitter_1.restoreState(sett.main_win_splitter_1)

    def _setColor(self, widget, yellow):
        if yellow:
            widget.setPalette(self.color_yellow)
        else:
            widget.setPalette(self.color_white)

    def settingsUpdated(self):
        log.debugf(log.DEBUG_MAINWIN, "settingsUpdated")
        font = QFont(sett.fontName, int(sett.fontSize))
        self.setFont(font)
        QGuiApplication.setFont(font)

    # ########################################################################
    #
    #   Menu
    #
    # ########################################################################

    def _initMenu(self):
        # File, Exit
        self.actionExit.triggered.connect(self._closeHandler)

        # Edit, Settings
        self.actionSettings.triggered.connect(self.settingsDialog)

        # Activity, Sync
        self.actionActivitySync.triggered.connect(self.activitymgr.sync)

        # Report, Sync
        self.actionReportSync.triggered.connect(self.reportmgr.sync)

        # Help, about
        self.actionAbout.triggered.connect(self.about)

    # ########################################################################
    #
    #   Log
    #
    # ########################################################################

    def _initLog(self):
        self.log_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.log_table.customContextMenuRequested.connect(self.handleLogMenu)
        self.log_table.clear()
        self.log_table.setColumnCount(4)
        self.log_table.setRowCount(0)
        self.log_table.setHorizontalHeaderLabels(["When", "Thread", "Level", "Message"])

    def handleLogMenu(self, pos):
        menu = QtWidgets.QMenu(self)
        clearAction = menu.addAction("Clear")
        action = menu.exec_(QtGui.QCursor.pos())
        if action == clearAction:
            self.log_table.clearContents()
            self.log_table.setRowCount(0)
            log.debugf(log.DEBUG_MAINWIN, "Log cleared()")

    # ########################################################################
    #
    #   Activity
    #
    # ########################################################################

    def _initActivity(self):
        self.activitymgr.sig.connect(self.activityListUpdated)
        self.activityListUpdated()

    def activityListUpdated(self):
        """
        Called when the list of activities has changed during sync with the server
        """
        log.debugf(log.DEBUG_MAINWIN, "main/activityListUpdated()")
        alist = self.activitymgr.getList()
        self.comboCurrentActivity.clear()
        for activity in alist:
            self.comboCurrentActivity.addItem(activity.name, activity.server_id)
        self._reportsTableUpdated()

    # ########################################################################
    #
    #   Current report
    #
    # ########################################################################

    def _initCurrentReport(self):
        self.report = None
        self._currentReportStateChanged(self.timetracker.stateInactive)

        self._currentReportGuiChanged()
        self.comboCurrentActivity.currentIndexChanged.connect(self._currentReportGuiChanged)
        self.comboCurrentProject.currentIndexChanged.connect(self._currentReportGuiChanged)
        self.dtCurrentStart.dateTimeChanged.connect(self._currentReportGuiChanged)
        self.timeCurrentLen.timeChanged.connect(self._currentReportGuiChanged)
        self.txtCurrentComment.textChanged.connect(self._currentReportGuiChanged)

        self.btnCurrentStart.clicked.connect(self._currentReportStart)
        self.btnCurrentStop.clicked.connect(self._currentReportStop)
        self.timetracker.stateSignal.connect(self._currentReportStateChanged)
        self.timetracker.activeUpdated.connect(self._currentReportUpdated)

    def _currentReportStart(self):
        self.report = self._getNewReport()
        self.report.start = datetime.datetime.now().replace(second=0, microsecond=0)
        self.report.stop = self.report.start

        self.timetracker.setStateActive(report=self.report)
        self._currentReportGuiChanged()

    def _currentReportStop(self):
        self.timetracker.setStateInactive()

    def _currentReportUpdated(self, status):
        """
        Called periodically by timetracker so GUI can be updated
        """
        self.timeCurrentLen.setTime(status.length)
        self._myStatusBar.idle = f"Idle {status.idle}"

    def _currentReportStateChanged(self, state):
        """
        Called when timetracker state changes
        """
        icon = "tray-inactive.png"
        widgets = [self.dtCurrentStart, self.timeCurrentLen, self.txtCurrentComment]
        if state == self.timetracker.stateActive:
            self.dtCurrentStart.setDateTime(QtCore.QDateTime.currentDateTime())
            icon = "tray-active.png"
            for widget in widgets:
                widget.setEnabled(True)
                self._setColor(widget, True)
        else:
            self.dtCurrentStart.findChild(QtWidgets.QLineEdit).setText("")
            self.timeCurrentLen.findChild(QtWidgets.QLineEdit).setText("")
            self.txtCurrentComment.clear()
            for widget in widgets:
                self._setColor(widget, False)
                widget.setEnabled(False)

        self.btnCurrentStart.setEnabled(state == self.timetracker.stateInactive)
        self.btnCurrentStop.setEnabled(state != self.timetracker.stateInactive)

        self.setWindowIcon(QtGui.QIcon(f":/resource/{icon}"))

    def _currentReportGuiChanged(self):
        """
        Copy GUI to self.report
        """

        if self.report:
            tmpid = self.comboCurrentActivity.itemData(self.comboCurrentActivity.currentIndex())
            if tmpid is not None and tmpid > 0:
                self.report.activityid = tmpid

            tmpid = self.comboCurrentProject.itemData(self.comboCurrentProject.currentIndex())
            if tmpid is not None and tmpid > 0:
                self.report.projectid = tmpid

            self.report.start = self.dtCurrentStart.dateTime().toPyDateTime().replace(microsecond=0)

            # calculate new start, end is always now()
            # t = self.timeCurrentLen.time()
            # seconds = t.hour() * 3600 + t.minute() * 60 + t.second()
            # start = datetime.datetime.now() - datetime.timedelta(seconds=seconds)

            self.report.comment = self.txtCurrentComment.toPlainText()

            self.timetracker.report = self.report

    # ########################################################################
    #
    #   Reports, toolbar and table
    #
    # ########################################################################

    def _initReports(self):
        # Toolbar
        self.btnReportSync.clicked.connect(self.reportmgr.sync)
        self.chkReportSyncAuto.stateChanged.connect(self.reportmgr.setAutosync)

        self.btnSetSelectedDatePrev.clicked.connect(self._ReportsSetSelectedDatePrev)
        self.btnSetSelectedDateToday.clicked.connect(self._ReportsSetSelectedDateToday)
        self.btnSetSelectedDateNext.clicked.connect(self._ReportsSetSelectedDateNext)

        self.selectedDate.dateChanged.connect(self._ReportsUpdateWeekday)

        # Table
        t = self.tableReports   # less typing
        t.clearSelection()
        t.setColumnCount(7)
        t.setRowCount(1)
        t.setHorizontalHeaderLabels(("Activity", "Project", "Start", "Stop", "Len", "Flags", "Comment"))
        t.verticalHeader().setVisible(False)
        t.clicked.connect(self.report_edit)

        self.reportmgr.sig.connect(self._reportsTableUpdated)

    def _reportsTableSet(self, table, row, col, value, userdata=None):
        table_item = QtWidgets.QTableWidgetItem(value)
        if userdata is not None:
            table_item.setData(QtCore.Qt.UserRole, userdata)
        table.setItem(row, col, table_item)

    def _reportsTableUpdated(self):
        """
        Load the reports into the list, for the selected date
        """
        if not self.reportmgr:
            return  # not initialized yet
        d = self.selectedDate.date().toPyDate()
        self.rlist = self.reportmgr.getList(d)
        t = self.tableReports   # less typing
        t.clearSelection()
        t.setRowCount(len(self.rlist) + 1)
        row = 0
        totalLen = 0
        for r in self.rlist:
            col = 0

            a = self.activitymgr.get(r.activityid)
            if a is not None:
                self._reportsTableSet(t, row, col, a.name, r._id)
            else:
                self._reportsTableSet(t, row, col, "Unknown", r._id)
            col += 1

            # self._reportsTableSet(t, row, col, p.name, p._id)
            self._reportsTableSet(t, row, col, "?")
            col += 1

            try:
                tmp = r.start.strftime("%H:%M")
            except AttributeError:
                tmp = "None"
            self._reportsTableSet(t, row, col, tmp)
            col += 1

            try:
                tmp = r.stop.strftime("%H:%M")
            except AttributeError:
                tmp = "None"
            self._reportsTableSet(t, row, col, tmp)
            col += 1

            if r.start is not None and r.stop is not None:
                l = (r.stop - r.start).total_seconds() / 60
                totalLen += l
                tmp = f"{l//60:.0f}:{l%60:02.0f}"
            else:
                tmp = "None"
            self._reportsTableSet(t, row, col, tmp)
            col += 1

            s = ""
            if r.server_id is not None and r.server_id > -1:
                s += f"on server({r.server_id})"
            if r.updated:
                s += " updated"
            if r.deleted:
                s += " remove"
            self._reportsTableSet(t, row, col, s)
            col += 1

            self._reportsTableSet(t, row, col, r.comment)
            col += 1

            row += 1

        col = 0

        self._reportsTableSet(t, row, col, "Total")
        col += 1

        self._reportsTableSet(t, row, col, "")
        col += 1

        self._reportsTableSet(t, row, col, "")
        col += 1

        self._reportsTableSet(t, row, col, "")
        col += 1

        self._reportsTableSet(t, row, col, f"{totalLen // 60:.0f}:{totalLen % 60:02.0f}")
        col += 1

        self._reportsTableSet(t, row, col, "")
        col += 1

        self._reportsTableSet(t, row, col, "")
        col += 1

        t.resizeColumnsToContents()

    def _ReportsSetCurrentDate(self, d):
        """
        Helper fiunction to update date
        """
        self.selectedDate.setDate(d)

    def _ReportsSetSelectedDateToday(self):
        self._ReportsSetCurrentDate(datetime.datetime.now())

    def _ReportsSetSelectedDatePrev(self):
        d = self.selectedDate.date().addDays(-1)
        self._ReportsSetCurrentDate(d)

    def _ReportsSetSelectedDateNext(self):
        d = self.selectedDate.date().addDays(1)
        self._ReportsSetCurrentDate(d)

    def _ReportsUpdateWeekday(self, qd):
        """
        Called by signal, so it is always updated
        """
        dayname = QtCore.QDate.longDayName(qd.dayOfWeek())
        self.reportsWeekday.setText(dayname)
        self.tableReports.clearSelection()
        self._reportsTableUpdated()

    def _ReportsGetSelectedReportId(self):
        row = self.tableReports.currentRow()
        if row:
            _id = self.tableReports.item(row, 0).data(QtCore.Qt.UserRole)
            return _id
        return None

    def _getNewReport(self):
        report = Report()
        report.server_id = -1
        report.user_id = 1
        report.seq = 0
        report.deleted = False
        report.updated = False
        report.modified = datetime.datetime(1990, 1, 1)
        return report

    # ########################################################################
    #
    #   Report details
    #
    # ########################################################################

    def init_report_window(self):
        self.btn_report_create.clicked.connect(self.report_create)
        self.btn_report_edit.clicked.connect(self.report_edit)

    def report_create(self):
        """
        Open the report detail window, with default values for creating a new report
        """
        d = self.selectedDate.date().toPyDate()
        a = report_main.Report_Win(self,
                                   activityMgr=self.activitymgr,
                                   reportMgr=self.reportmgr,
                                   default_date=d)
        a.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        a.exec_()

    def report_edit(self):
        """
        Open the report detail window, for editing an existing report
        Called from double-click in table, or edit button
        """
        row = self.tableReports.currentRow()
        row = self.tableReports.item(row, 0)
        if row:
            _id = row.data(QtCore.Qt.UserRole)
            if _id is not None and _id >= 0:
                report = self.reportmgr.get(_id)
                if report:
                    a = report_main.Report_Win(self,
                                               activityMgr=self.activitymgr,
                                               reportMgr=self.reportmgr,
                                               report=report)
                    a.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
                    a.exec_()
                    return
                log.error(f"Can't find report {_id} in local database")

    def report_delete(self):
        """
        Open the report detail window, for deleting an existing report
        """

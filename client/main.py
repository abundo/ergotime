#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
GUI Main window
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

import sys
import datetime
import enum

import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
from PyQt5.Qt import QFont, QGuiApplication

from common.activity import Activity
from common.report import Report
from common.users import Users

import util
import options

from myglobals import *
from logger import log
from settings import sett
from activitymgr import ActivityMgr
from reportmgr import ReportMgr

import timetracker
import main_win
import systray

from idlelib.textView import view_file      # make cz_freeze stop complaining

debug = False
#global = True    # during development

StateRD = enum.Enum("StateRD", "none view edit new")


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

        log.setOut(self.txtLog)
        log.info("Log started")
        sys.stdout = log
        sys.stderr = log
        print("STDOUT/STDERR Redirected to log")

        self.color_white = self.dtCurrentStart.palette()
        self.color_white.setColor(QtGui.QPalette.All, QtGui.QPalette.Base, QtGui.QColor(QtCore.Qt.white))
        
        self.color_yellow = self.dtCurrentStart.palette()
        self.color_yellow.setColor(QtGui.QPalette.All, QtGui.QPalette.Base, QtGui.QColor(QtCore.Qt.yellow))
        self.color_yellow.setColor(QtGui.QPalette.Text, QtCore.Qt.black)

        QtCore.QTimer.singleShot(10, self.delayInit) # make sure GUI is drawn before we do anything more


    # ########################################################################
    #
    # Misc stuff
    #
    # ########################################################################

    def delayInit(self):
        """This is called from event loop, so GUI is fully initialized"""

        self.stateRD = StateRD.none
        self.dbconf, self.basium = util.openLocalDatabase()

        self.activitymgr = ActivityMgr(main_db=self.basium)
        self.reportmgr = ReportMgr(main_db=self.basium)

        self.activitymgr.init()
        self.reportmgr.init()
        self.timetracker = timetracker.Timetracker(parent=self, activitymgr=self.activitymgr, reportmgr=self.reportmgr)
        self.systray = systray.Systray(timetracker=self.timetracker, activitymgr=self.activitymgr)

        self._initMenu()
        self._initLog()
        self._initActivity()
        self._initCurrentReport()
        self._initReports()
        self._initReportDetails()

        self.timetracker.activeUpdated.connect(self.updateStatus)
        self.timetracker.stateSignal.connect(self._stateChanged)
        
        tmpid = self.comboCurrentActivity.itemData(self.comboCurrentActivity.currentIndex())
        if tmpid and tmpid >= 0:
            self.timetracker.updateReport(activityid=tmpid)

        self._ReportsSetSelectedDateToday()
        
        self.actionSave_windows_position.triggered.connect(self._saveWindowPosition)
        sett.updated.connect(self.settingsUpdated)

    def settingsDialog(self):
        o = options.OptionsWin(self)
        o.exec_()
        
    def about(self):
        import about
        a = about.AboutWin(self)
        a.exec_()
        
    def closeEvent(self, event):
        if self._closeHandler():
            event.accept()
        else:
            event.ignore()
        
    def _closeHandler(self):
        msgBox = QtWidgets.QMessageBox(parent=self)

        if not debug:
            # is there an current activity? it needs to be stopped and saved
            if self.timetracker.state == self.timetracker.stateActive:
                msgBox.setText("There is an active activity, do you want to save this as a report?")
                msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
                response = msgBox.exec_()
                if response != QtWidgets.QMessageBox.Yes:
                    self.timetracker.setStateInactive()
                
            # do we have unsyncronised local changes?
            count = self.reportmgr.getUnsyncronisedCount()
            if count > 0:
                msgBox.setText("There are %s reports in local database that needs to be syncronized with the server. Do you want to do this now?")
                msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
                response = msgBox.exec_()
                if response != QtWidgets.QMessageBox.Yes:
                    self.reportmgr.sync()
            
            msgBox.setText("Do you want to exit the application?")
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
            response = msgBox.exec_()
            if response != QtWidgets.QMessageBox.Yes:
                return False
            
        self._saveWindowPosition();
        self.activitymgr.stop()
        self.reportmgr.stop()
        
        sett.sync()
        QtWidgets.QApplication.exit(0)
    
    # save the current windows position & size in settings
    def _saveWindowPosition(self):
        log.debugf(DEBUG_MAINWIN, "Save main window position and size")
        sett.main_win_pos = self.pos()
        sett.main_win_size = self.size()
        sett.main_win_splitter_1 = self.splitter_1.saveState()
        sett.main_win_splitter_2 = self.splitter_2.saveState()

    # restore the windows current position & size from settings
    def _restoreWindowPosition(self):
        log.debugf(DEBUG_MAINWIN, "Restore main window position and size")
        self.move(sett.main_win_pos)
        self.resize(sett.main_win_size)
        if sett.contains("main_win_splitter_1"):
            self.splitter_1.restoreState(sett.main_win_splitter_1)
        if sett.contains("main_win_splitter_2"):
            self.splitter_2.restoreState(sett.main_win_splitter_2)

    def _setColor(self, widget, yellow):
        if yellow:
            widget.setPalette(self.color_yellow)
        else:
            widget.setPalette(self.color_white)
        
    def _stateChanged(self, state):
        """Called when timetracker state changes"""
        widgets = [self.dtCurrentStart, self.timeCurrentLen, self.txtCurrentComment]
        if state == self.timetracker.stateInactive:
            self.setWindowIcon(QtGui.QIcon("resource/tray-inactive.png"))
            for widget in widgets:
                self._setColor(widget, False)
            self.timeCurrentLen.clear()
            self.txtCurrentComment.clear()
            
        elif state == self.timetracker.stateActive:
            self.setWindowIcon(QtGui.QIcon("resource/tray-active.png"))
            for widget in widgets:
                self._setColor(widget, True)
            
    def updateStatus(self, status):
        """Called periodically by timetracker so GUI can be updated"""
        self.timeCurrentLen.setTime(status.length)
        self._myStatusBar.idle = "Idle %s" % status.idle


    def settingsUpdated(self):
        log.debugf(DEBUG_MAINWIN, "settingsUpdated")
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
        self.txtLog.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.txtLog.customContextMenuRequested.connect(self.handleLogMenu)
        
    def handleLogMenu(self, pos):
        menu = QtWidgets.QMenu(self)
        clearAction = menu.addAction("Clear")
        action = menu.exec_(QtGui.QCursor.pos())
        if action == clearAction:
            self.txtLog.clear()
            log.debugf(DEBUG_MAINWIN, "Log cleared()")


    # ########################################################################
    #
    #   Activity
    #
    # ########################################################################

    def _initActivity(self):
        self.activitymgr.sig.connect(self.activityListUpdated)
        self.activityListUpdated()

    def activityListUpdated(self):
        """Called when the list of activities has changed during sync with the server"""
        log.debugf(DEBUG_MAINWIN, "main/activityListUpdated()")
        alist = self.activitymgr.getList()
        self.comboReportActivity.clear()
        self.comboCurrentActivity.clear()
        for a in alist:
            self.comboReportActivity.addItem(a.name, a.server_id)
            self.comboCurrentActivity.addItem(a.name, a.server_id)
        self._reportsTableUpdated()

    
    # ########################################################################
    #
    #   Current report
    #
    # ########################################################################

    def _initCurrentReport(self):
        self.comboCurrentActivity.currentIndexChanged.connect( self._currentReportGuiChanged )
        self.dtCurrentStart.dateTimeChanged.connect( self._currentReportGuiChanged )
        self.txtCurrentComment.textChanged.connect( self._currentReportGuiChanged )
        self.txtCurrentComment.textChanged.connect( self._currentReportGuiChanged )

        self.btnCurrentStart.clicked.connect(self._currentReportStart)
        self.btnCurrentStop.clicked.connect(self.timetracker.setStateInactive)

    def _currentReportStart(self):
        self.dtCurrentStart.setDateTime( datetime.datetime.now() )
        self.timetracker.setStateActive()
    
    def _currentReportGuiChanged(self):
        """Handle changes to the current report, updating the timetracker shadowed data"""
        sender = self.sender()
        if sender == self.comboCurrentActivity:
            tmpid = self.comboCurrentActivity.itemData(self.comboCurrentActivity.currentIndex())
            if tmpid != None and tmpid > 0:
                self.timetracker.updateReport(activityid = tmpid)
        if sender == self.dtCurrentStart:
            self.timetracker.updateReport(start = self.dtCurrentStart.dateTime().toPyDateTime().replace(microsecond=0))
        if sender == self.timeCurrentLen:
            # calculate new start
            start = datetime.datetime.now() - self.timeCurrentLen.time().toPyTime()
            self.timetracker.updateReport(start=start)
        if sender == self.txtCurrentComment:
            self.timetracker.updateReport(comment=self.txtCurrentComment.toPlainText())


    # ########################################################################
    #
    #   Reports, toolbar and table
    #
    # ########################################################################

    def _initReports(self):
        # Reports
        self._reportDetailsUpdate(None)
        
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
        t.clicked.connect(self._reportsTableRowClicked)
        
        self.reportmgr.sig.connect(self._reportsTableUpdated)

    def _reportsTableSet(self, table, row, col, value, userdata=None):
        table_item = QtWidgets.QTableWidgetItem(value)
        if userdata != None:
            table_item.setData(QtCore.Qt.UserRole, userdata)
        table.setItem(row, col, table_item)

    def _reportsTableUpdated(self):
        """Load the reports into the list, for the selected date"""
        self._reportDetailsUpdate(None)
        if not self.reportmgr:
            return  # not initialized yet
        d = self.selectedDate.date().toPyDate()
        self.rlist = self.reportmgr.getList( d )
        t = self.tableReports   # less typing
        t.clearSelection()
        t.setRowCount(len(self.rlist) + 1)
        row = 0
        totalLen = 0
        for r in self.rlist:
            col = 0
            
            a = self.activitymgr.get(r.activityid)
            if a != None:
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

            if r.start != None and r.stop != None:
                l = (r.stop - r.start).total_seconds() / 60
                totalLen += l
                tmp = "%02d:%02d" % (l // 60, l % 60)
            else:
                tmp = "None"
            self._reportsTableSet(t, row, col, tmp)
            col += 1

            s = ""
            if r.server_id != None and r.server_id > -1: 
                s += "on server(%s)" % r.server_id
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
        
        self._reportsTableSet(t, row, col, "%02d:%02d" % (totalLen // 60, totalLen % 60))
        col += 1
        
        self._reportsTableSet(t, row, col, "")
        col += 1
        
        self._reportsTableSet(t, row, col, "")
        col += 1

        t.resizeColumnsToContents()
            
    def _ReportsSetCurrentDate(self, d):
        """Helper fiunction to update date"""
        self.selectedDate.setDate( d )
 
    def _ReportsSetSelectedDateToday(self):
        self._ReportsSetCurrentDate( datetime.datetime.now() )

    def _ReportsSetSelectedDatePrev(self):
        d = self.selectedDate.date().addDays(-1)
        self._ReportsSetCurrentDate( d )
        
    def _ReportsSetSelectedDateNext(self):
        d = self.selectedDate.date().addDays(1)
        self._ReportsSetCurrentDate( d )
        
    def _ReportsUpdateWeekday(self, qd):
        """Called by signal, so it is always updated"""    
        dayname = QtCore.QDate.longDayName(qd.dayOfWeek())
        self.reportsWeekday.setText( dayname )
        self.tableReports.clearSelection()
        self._reportsTableUpdated()
        self._reportDetailsUpdate(None)

    def _reportsTableRowClicked(self, modelindex):
        if self.stateRD == StateRD.edit or self.stateRD == StateRD.new:
            self.tableReports.clearSelection()
            log.info("Please save/cancel report before selecting a new one")
            return
        row = self.tableReports.currentRow()
        row = self.tableReports.item(row, 0)
        if row:
            _id = row.data(QtCore.Qt.UserRole)
            if _id != None and _id >= 0:
                report = self.reportmgr.get(_id)
                if report:
                    self._reportDetail = report
                    self.stateRD = StateRD.none
                    self._reportDetailsUpdate(self._reportDetail)
                    self.stateRD = StateRD.view
                    return
                log.error("Can't find report %s in local database" % _id)
        
        self._reportDetailsUpdate(None)
        
    def _ReportsGetSelectedReportId(self):
        row = self.tableReports.currentRow()
        if row != None:
            _id = self.tableReports.item(row, 0).data(QtCore.Qt.UserRole)
            return _id
        return None
        

    # ########################################################################
    #
    #   Report details
    #
    # ########################################################################

    def _initReportDetails(self):
        
        self._reportDetail = self._getNewReport()
        
        # toolbar
        self.btnReportSave.clicked.connect(self._reportDetailsSave)
        self.btnReportNew.clicked.connect(self._reportDetailsNew)
        self.btnReportDelete.clicked.connect(self._reportDetailsRemove)
        self.btnReportCancel.clicked.connect(self._reportDetailsCancelChange)
        
        # fields in grid
        self.comboReportActivity.currentIndexChanged.connect(self._reportDetailsChangedEvent)
        self.comboReportProject.currentIndexChanged.connect(self._reportDetailsChangedEvent)
        self.dtReportStart.dateTimeChanged.connect(self._reportDetailsChangedEvent)
        self.dtReportStop.dateTimeChanged.connect(self._reportDetailsChangedEvent)
        self.timeReportLen.dateChanged.connect(self._reportDetailsChangedEvent)
        self.txtReportComment.textChanged.connect(self._reportDetailsChangedEvent)

        self.dtReportStart.dateTimeChanged.connect(self._reportDetailsUpdateLength)
        self.dtReportStop.dateTimeChanged.connect(self._reportDetailsUpdateLength)

        self.btnStartHourPlus.clicked.connect(self._reportDetailsModifyStart)
        self.btnStartHourMinus.clicked.connect(self._reportDetailsModifyStart)
        self.btnStartMinutePlus.clicked.connect(self._reportDetailsModifyStart)
        self.btnStartMinuteMinus.clicked.connect(self._reportDetailsModifyStart)
        
        self.btnStopHourPlus.clicked.connect(self._reportDetailsModifyStop)
        self.btnStopHourMinus.clicked.connect(self._reportDetailsModifyStop)
        self.btnStopMinutePlus.clicked.connect(self._reportDetailsModifyStop)
        self.btnStopMinuteMinus.clicked.connect(self._reportDetailsModifyStop)

    def _getNewReport(self):
        report = Report()
        report.server_id = -1
        report.user_id = 1      # todo, should be updated by server
        report.seq = 0
        report.deleted = False
        report.updated = False
        return report
    
    @property
    def stateRD(self):
        return self._stateRD

    @stateRD.setter
    def stateRD(self, state):
        s = state == StateRD.none or state == StateRD.view
        
        widgets1 = [self.btnReportSync, self.chkReportSyncAuto, self.btnSetSelectedDatePrev, 
                    self.btnSetSelectedDateToday, self.btnSetSelectedDateNext, self.selectedDate,
                    self.tableReports]
        for widget in widgets1:
            widget.setEnabled(s)

        widgets2 = [self.lblReportSyncState, self.comboReportActivity, self.comboReportProject, 
                    self.dtReportStart, self.dtReportStop, self.txtReportComment, 
                    self.timeReportLen]
        yellow = state == StateRD.edit or state == StateRD.new
        for widget in widgets2:
            widget.setDisabled(state == StateRD.none)
            self._setColor(widget, yellow)

        self._stateRD = state

    def _reportDetailsUpdateLength(self):
        """Called when start or stop datetime changed"""
        start = self.dtReportStart.dateTime().toPyDateTime()
        stop = self.dtReportStop.dateTime().toPyDateTime()
        if stop < start:
            # stop can't be before start
            self.dtReportStop.setDateTime(self.dtReportStart.dateTime())
        l = (stop - start).total_seconds() / 60
        self.timeReportLen.setTime(QtCore.QTime(l // 60, l % 60))

    def _reportDetailsUpdate(self, report):
        """Called when a report is selected/not selected"""
        if report:
            s = ""
            if report.server_id != None and report.server_id >= 0:
                s +="on server(%s) " % report.server_id
            if report.updated:
                s +="locally updated "
            if report.deleted:
                s +="to be removed "
            self.lblReportSyncState.setText(s)
            if report.activityid:
                self.comboReportActivity.setCurrentIndex(self.comboReportActivity.findData(report.activityid))
                # self.comboReportProject.setCurrentIndex()
            if report.start != None:
                self.dtReportStart.setDateTime(report.start)
            else:
                self.dtReportStart.clear()
            if report.stop != None:
                self.dtReportStop.setDateTime(report.stop)
            else:
                self.dtReportStop.clear()
            
            self.txtReportComment.setText(report.comment)
        else:
            self._reportDetail = self._getNewReport()
            self.stateRD = StateRD.none
            self.lblReportSyncState.clear()
            # d = QtCore.QDateTime.fromMSecsSinceEpoch(0)
            d = datetime.datetime.now()
            self.dtReportStart.setDateTime(d)
            self.dtReportStop.setDateTime(d)
            self.timeReportLen.clear()
            self.txtReportComment.clear()
            
    def _reportDetailsSave(self):
        """User clicked Save, save new or existing report"""
        if self.stateRD == StateRD.edit:
            self._reportDetail.updated = True
        elif self.stateRD == StateRD.new:
            pass
        else:
            log.info("Save aborted, no change or not editing a new report")
            return

        # update report object from GUI
        activityid = self.comboReportActivity.itemData(self.comboReportActivity.currentIndex())
        if not activityid or activityid < 1:
            log.warning("Save failed, no activity selected")
            return
        self._reportDetail.activityid = activityid
        # todo project
        self._reportDetail.start = self.dtReportStart.dateTime().toPyDateTime().replace(microsecond=0)
        self._reportDetail.stop = self.dtReportStop.dateTime().toPyDateTime().replace(microsecond=0)
        self._reportDetail.comment = self.txtReportComment.toPlainText()
        if self._reportDetail.comment == None:
            self._reportDetail.comment = ""
        if self.reportmgr.store(self._reportDetail):
            self._reportDetailsUpdate(self._reportDetail)
    
    def _reportDetailsNew(self):
        """User clicked New"""
        if self.stateRD in [StateRD.edit, StateRD.new]:
            log.warning("Please save/cancel changes before creating new report")
            return
        self.tableReports.clearSelection()
        d = self.selectedDate.date().toPyDate()
        self._reportDetail = self._getNewReport()
        self._reportDetail.start = datetime.datetime.combine(d, datetime.datetime.now().time())
        self._reportDetail.stop = self._reportDetail.start + datetime.timedelta(seconds=30*60)
        self._reportDetailsUpdate(self._reportDetail)
        self.stateRD = StateRD.new

    def _reportDetailsRemove(self):
        """User clicked Remove"""
        if self.stateRD == StateRD.edit:
            log.warning("Please Save/Cancel changes to selected report before removing it")
            return
#        if self.stateRD != StateRD.view or self.stateRD == StateRD.new:
        if self.stateRD in [StateRD.view, StateRD.new]:
            log.warning("Please select a report to remove")
            return
        msgBox = QtWidgets.QMessageBox(parent=self)
        msgBox.setText("Do you want to remove the report?")
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
        response = msgBox.exec_()
        if response == QtWidgets.QMessageBox.Yes:
#            _id = self._ReportsGetSelectedReportId()
#            self.reportmgr.remove(Report(_id))   # will trigger update of Reports Table
            self.reportmgr.remove(self._reportDetail)   # will trigger update of Reports Table
    
    def _reportDetailsCancelChange(self):
        self.tableReports.clearSelection()
        self._reportDetailsUpdate(None)
    
    def _reportDetailsChangedEvent(self):
        """Called when user edits any details of a report"""
        if self.stateRD == StateRD.view:
            self.stateRD = StateRD.edit
#             for widget in [self.comboReportActivity, self.dtReportStart, self.dtReportStop, self.txtReportComment, self.timeReportLen]:
#                 self._setColor(widget, True)

    def _reportDetailsModifyStart(self):
        """Handle the start +H -H +S -S buttons"""
        sender=self.sender()
        if isinstance(sender, QtWidgets.QToolButton):
            action = sender.text()
            dtstart = self.dtReportStart.dateTime()
            dtstop = self.dtReportStop.dateTime()
            if action == "+H":
                sec = 3600
            elif action == "-H":
                sec = -3600
            elif action == "+M":
                sec = 60
            elif action == "-M":
                sec = -60
            self.dtReportStart.setDateTime(dtstart.addSecs(sec))
            self.dtReportStop.setDateTime(dtstop.addSecs(sec))

    def _reportDetailsModifyStop(self):
        """Handle the stop +H -H +S -S buttons"""
        sender=self.sender()
        if isinstance(sender, QtWidgets.QToolButton):
            action = sender.text()
            dtstop = self.dtReportStop.dateTime()
            if action == "+H":
                sec = 3600
            elif action == "-H":
                sec = -3600
            elif action == "+M":
                sec = 60
            elif action == "-M":
                sec = -60
            self.dtReportStop.setDateTime(dtstop.addSecs(sec))

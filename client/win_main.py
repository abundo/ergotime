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

from PySide import QtCore, QtGui

import basium
from activity import Activity
from report import Report
from users import Users

import settings
import idle_win32
from activitymgr import ActivityMgr
from reportmgr import ReportMgr

import ui_main

debug = False

INFO=0
WARNING=1
ERROR=2
DEBUG=3

class Log(QtCore.QObject):
    """Log handler. Always uses signals to be thread safe"""
    class Communicate(QtCore.QObject):
        log = QtCore.Signal(int, str)
    
    def __init__(self):
        self.out = None
        self.level = DEBUG
        self.c = self.Communicate()
        self.c.log.connect(self.log)
        self.levels = ["INFO", "WARNING", "ERROR", "DEBUG"]

    def setOut(self, out):
        self.out = out
    
    def setLevel(self, level):
        self.level = level

    @QtCore.Slot(int, str)
    def log(self, level, msg):
        if level <= self.level:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if self.out != None:
                self.out.appendPlainText("%s %s %s" % (now, self.levels[level], msg))
            else:
                print("%s %s %s" % (now, self.levels[level], msg))

    def info(self, msg):
        self.c.log.emit(INFO, msg)
        
    def warning(self, msg):
        self.c.log.emit(WARNING, msg)
        
    def error(self, msg):
        self.c.log.emit(ERROR, msg)
    
    def debug(self, msg):
        self.c.log.emit(DEBUG, msg)


class CurrentReport(QtCore.QObject):
    idleDetected = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent

        self._timer = None
        self.report = None
        self.stop()

    def stop(self):
        if self._timer:
            self._timer.cancel()
            self._timer = None
        if self.report:
            self.report.comment = self.parent.txtCurrentComment.toPlainText()
        self.state = None
        self._update()
        self._setColor(False)

    def start(self):
        self.state = "active"
        now = QtCore.QDateTime.currentDateTime()
        self.parent.dtCurrentStart.setDateTime(now)
        self.parent.dtCurrentStart.setDisabled(False)
        self.parent.timeCurrentLen.setDisabled(False)

        self.report = Report()
        self.report.server_id = -1
        self.report.user_id = 1
        self.report.seq = 0
        self.report.start = now.toPython().replace(microsecond=0)

        self._update()
        self._setColor(True)
    
    def _setColor(self, yellow):
        p = self.parent.dtCurrentStart.palette()
        if yellow:
            p.setColor(QtGui.QPalette.All, QtGui.QPalette.Base, QtGui.QColor(QtCore.Qt.yellow))
            p.setColor(QtGui.QPalette.Text, QtCore.Qt.black)
        else:
            p.setColor(QtGui.QPalette.All, QtGui.QPalette.Base, QtGui.QColor(QtCore.Qt.white))
        self.parent.dtCurrentStart.setPalette(p)
        self.parent.timeCurrentLen.setPalette(p)
        self.parent.txtCurrentComment.setPalette(p)

    def _update(self):
        """When active, called periodically to update length and GUI"""
        if self.state:
            self.report.stop = datetime.datetime.now().replace(microsecond=0)
            l = (self.report.stop - self.report.start).total_seconds()
            self.parent.timeCurrentLen.setTime(QtCore.QTime().addSecs(l))
            idle = idle_win32.getIdle()
            self.parent.lblStatusIdle.setText("<b>Idle</b> %0d seconds" % idle)
            if idle > settings.idleTimeout:  # todo idle time from settings
                self.parent.log.debug("Idle detected %s seconds" % idle)
                # remove the idle timeout from the report
                self.report.stop -= datetime.timedelta(seconds=settings.idleTimeout)
                self.idleDetected.emit()
                return
            self._timer = threading.Timer(1,self._update)
            self._timer.start()
        else:
            d = QtCore.QDateTime.fromMSecsSinceEpoch(0)
            self.parent.dtCurrentStart.setDateTime(d)
            self.parent.dtCurrentStart.setDisabled(True)
            self.parent.timeCurrentLen.setTime(QtCore.QTime(0,0))
            self.parent.timeCurrentLen.setDisabled(True)
            self.parent.txtCurrentComment.clear()


class SelectedReport:
    """
    Tracks gui state
    state can be None, edit, new
    modified can be true/false
    """
    def __init__(self, parent=None):
        self.parent = parent
        self.setStateNone()

    def setStateNone(self):
        """No report is selected"""
        self.state = None
        self.report = None
        self.changed = False
        self._updateGui()
    
    def setStateEdit(self, report=None):
        """User selected one report to edit"""
        self.state = "edit"
        self.changed = False
        if report:
            self.report = report
        self._updateGui()
        
    def setStateNew(self, report=None):
        """User is creating a new report"""
        self.state = "new"
        self.changed = True
        if report:
            self.report = report
        self._updateGui()

    def _updateGui(self):
        line = ""
        if self.changed:
            line += "Changed"
            self.parent.tableReports.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        else:
            self.parent.tableReports.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.parent.lblReportState.setText(line)
        

class Win_Main(QtGui.QMainWindow, ui_main.Ui_Main):
    def __init__(self, parent=None):
        super(Win_Main, self).__init__(parent)
        self.setupUi(self)

        self.lblStatusIdle = QtGui.QLabel()
        self.statusBar().addWidget(self.lblStatusIdle)

        self.settings = QtCore.QSettings()

        self.log = Log()
        self.log.setOut(self.txtLog)
        self.log.info("Start")
        
        self.reportmgr = None
        
        self.selectedReport = SelectedReport(parent=self)
        self.currentReport = CurrentReport(parent=self)
        self.currentReport.idleDetected.connect(self.currentReportStop)

        # Menu, file
        self.actionExit.triggered.connect(self.confirmExit)
        
        # Menu, help
        self.actionAbout.triggered.connect(self.about)
        
        # current report
        self.btnCurrentStart.clicked.connect(self.currentReportStart)
        self.btnCurrentStop.clicked.connect(self.currentReportStop)

        # Settings
        self.actionSettings.triggered.connect(self.settingsDialog)
        
        # Reports
        self._updateGuiReport(None)
        self.tableReports.clicked.connect(self.reportClicked)

        self.btnSetSelectedDateToday.clicked.connect(self.setSelectedDateToday)
        self.btnSetSelectedDatePrev.clicked.connect(self.setSelectedDateTodayPrev)
        self.btnSetSelectedDateNext.clicked.connect(self.setSelectedDateTodayNext)
        
        self.btnReportSave.clicked.connect(self.reportSave)
        self.btnReportNew.clicked.connect(self.reportNew)
        self.btnReportRemove.clicked.connect(self.reportRemove)
        self.btnReportCancel.clicked.connect(self.reportCancelChange)

        self.selectedDate.dateChanged.connect(self.updateReportWeekday)

        # current report
        self.comboReportActivity.currentIndexChanged.connect(self.reportChangedEvent)
        self.dtReportStart.dateTimeChanged.connect(self.reportChangedEvent)
        self.dtReportStop.dateTimeChanged.connect(self.reportChangedEvent)
        self.timeReportLen.dateChanged.connect(self.reportChangedEvent)
        self.txtReportComment.textChanged.connect(self.reportChangedEvent)

        self.dtReportStart.dateTimeChanged.connect(self._updateLength)
        self.dtReportStop.dateTimeChanged.connect(self._updateLength)

        self.btnStartHourPlus.clicked.connect(self.reportModifyStart)
        self.btnStartHourMinus.clicked.connect(self.reportModifyStart)
        self.btnStartMinutePlus.clicked.connect(self.reportModifyStart)
        self.btnStartMinuteMinus.clicked.connect(self.reportModifyStart)
        
        self.btnStopHourPlus.clicked.connect(self.reportModifyStop)
        self.btnStopHourMinus.clicked.connect(self.reportModifyStop)
        self.btnStopMinutePlus.clicked.connect(self.reportModifyStop)
        self.btnStopMinuteMinus.clicked.connect(self.reportModifyStop)

        self.setSelectedDateToday()

        QtCore.QTimer.singleShot(1, self.delayInit) # make sure GUI is drawn before we do anything more


    def delayInit(self):
        """This is called from event loop, so gui is fully initialized"""

        # Connect to local database
        self.dbconf = basium.DbConf(database="d:/temp/ergotime/ergotime.db", log=self.log)
        self.log.debug("Opening local database %s" % self.dbconf.database)
        self.basium = basium.Basium(driver="sqlite", checkTables=True, dbconf=self.dbconf)
        self.basium.addClass(Activity)
        self.basium.addClass(Report)
        self.basium.addClass(Users)
        if not self.basium.start():
            self.log.error("Cannot open local database, very limited functionality")

        self.activitymgr = ActivityMgr(log=self.log, basium=self.basium)
        # ----- to activitymgr
        self.actionActivitySync.triggered.connect(self.activitymgr.sync)
        # ----- from activitymgr
        self.activitymgr.sig.updated.connect(self.activityListUpdated)

        self.reportmgr = ReportMgr(log=self.log, basium=self.basium)
        # to reportmgr
        self.btnReportSync.clicked.connect(self.syncReport)
        self.actionReportSync.triggered.connect(self.syncReport)
        # from reportmgr
        self.reportmgr.sig.updated.connect(self.reportListUpdated)

        self.activitymgr.init()
        self.reportmgr.init()    # when loaded, sends signal

    def confirmExit(self):
        msgBox = QtGui.QMessageBox()
   
        if not debug:
            msgBox.setText("Do you want to exit the application?")
            msgBox.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            msgBox.setDefaultButton(QtGui.QMessageBox.No)
#            response = msgBox.exec()
            response = msgBox.exec_()
            if response != QtGui.QMessageBox.Yes:
                return
#         if (timetrack->getState() == Timetrack::stateActive) {
#             msgBox.setText("You have an current activity, do you want to save this as a report?");
#             msgBox.setDefaultButton(QMessageBox::Yes);
#             response = msgBox.exec();
#             if (response == QMessageBox::Yes)  {
#                 timetrack->setStateInactive();
#             }
#         }
        self.activitymgr.stop()
        self.reportmgr.stop()
        self.saveWindowPosition();
        
        self.close()
#        QtGui.QApplication.exit(0)
    
    # save the current windows position & size in settings
    def saveWindowPosition(self):
        s = self.settings
        s.beginGroup("win_mainwin")
        s.setValue("pos", self.pos())
        s.setValue("size", self.size())
        s.setValue("splitter", self.splitter.saveState())
        s.setValue("splitter_2", self.splitter_2.saveState())
        s.endGroup()

    # restore the windows current position & size from settings
    def restoreWindowPosition(self):
        s = self.settings
        s.beginGroup("win_main")
        pos = s.value("pos", QtCore.QPoint(100,100))
        size = s.value("size", QtCore.QSize(600,400))
        self.resize(size)
        self.move(pos)
        if s.contains("splitter"):
            self.splitter.restoreState(s.value("splitter"))
        if s.contains("splitter_2"):
            self.splitter_2.restoreState(s.value("splitter_2"))
        s.endGroup()


    def updateStatus(self):
        pass


    def activityListUpdated(self):
        self.log.debug("activityListUpdated()")
        alist = self.activitymgr.getList()
        self.comboReportActivity.clear()
        self.comboCurrentActivity.clear()
#        self.comboReportActivity.addItem("<none>", -1)
        for a in alist:
            self.comboReportActivity.addItem(a.name, a.server_id)
            self.comboCurrentActivity.addItem(a.name, a.server_id)
        self.reportListUpdated()
    
    # -----------------------------------------------------------------------
    # Handle current report
    # -----------------------------------------------------------------------

    def currentReportStart(self):
        if not self.currentReport.state:
            self.currentReport.start()
    
    def currentReportStop(self):
        if self.currentReport.state:
            self.currentReport.stop()
            report = self.currentReport.report
            activityid = self.comboCurrentActivity.itemData(self.comboCurrentActivity.currentIndex())
            if activityid > 0:
                report.activityid = activityid
            self.reportmgr.store(report)

    
    # -----------------------------------------------------------------------
    # Handle buttons and list of reports
    # -----------------------------------------------------------------------
    
    def syncReport(self):
        self.reportmgr.sync()

    # load the reports into the list, for the selected date
    def reportListUpdated(self):
        self._updateGuiReport(None)
        if not self.reportmgr:
            return  # not initialized yet
        d = self.selectedDate.date().toPython()
        self.rlist = self.reportmgr.getList( d )
        t = self.tableReports
        t.setColumnCount(6)
        t.setRowCount(len(self.rlist) + 1)
        t.setHorizontalHeaderLabels(("Activity", "Start", "Stop", "Len", "Flags", "Comment"))
        t.verticalHeader().setVisible(False)
        t.clearSelection()
        row = 0
        totalLen = 0
        for r in self.rlist:
            col = 0
            
            a = self.activitymgr.get(r.activityid)
            if a != None:
                table_item = QtGui.QTableWidgetItem(a.name)
            else:
                table_item = QtGui.QTableWidgetItem("Unknown")
            t.setItem(row, col, table_item)
            table_item.setData(QtCore.Qt.UserRole, r._id)
            col += 1
            
            table_item = QtGui.QTableWidgetItem( r.start.strftime("%H:%M") )
            t.setItem(row, col, table_item)
            col += 1
            
            table_item = QtGui.QTableWidgetItem( r.stop.strftime("%H:%M") )
            t.setItem(row, col, table_item)
            col += 1

            l = (r.stop - r.start).total_seconds() / 60
            totalLen += l
            table_item = QtGui.QTableWidgetItem("%02d:%02d" % (l // 60, l % 60))
            t.setItem(row, col, table_item)
            col += 1

            s = ""
            if r.server_id and r.server_id > -1: 
                s += "on server(%s)" % r.server_id
            if r.updated:
                s += " modified"
            if r.deleted:
                s += " delete"
            table_item = QtGui.QTableWidgetItem(s)
            t.setItem(row, col, table_item)
            col += 1

            table_item = QtGui.QTableWidgetItem(r.comment)
            t.setItem(row, col, table_item)
            col += 1

            row += 1

       
        col = 0
        table_item = QtGui.QTableWidgetItem("Total")
        table_item.setData(QtCore.Qt.UserRole, -1)
        t.setItem(row, col, table_item)
        col += 1
        
        table_item = QtGui.QTableWidgetItem("")
        t.setItem(row, col, table_item)
        col += 1
        
        table_item = QtGui.QTableWidgetItem("")
        t.setItem(row, col, table_item)
        col += 1
        
        table_item = QtGui.QTableWidgetItem("%02d:%02d" % (totalLen // 60, totalLen % 60))
        t.setItem(row, col, table_item)
        col += 1
        
        table_item = QtGui.QTableWidgetItem("")
        t.setItem(row, col, table_item)
        col += 1
        
        table_item = QtGui.QTableWidgetItem("")
        t.setItem(row, col, table_item)
        col += 1
        

        t.resizeColumnsToContents()
            

    def about(self):
        QtGui.QMessageBox.about(self, "About ErgoTime, Platform etc",
                """<b>Platform Details</b>"""
                )
        
    def setSelectedDateToday(self):
        self.setCurrentDate( datetime.datetime.now() )

    def setSelectedDateTodayPrev(self):
        d = self.selectedDate.date().addDays(-1)
        self.setCurrentDate( d )
        
    def setSelectedDateTodayNext(self):
        d = self.selectedDate.date().addDays(1)
        self.setCurrentDate( d )
        
    def setCurrentDate(self, d):
        self.selectedDate.setDate( d )
        self._reportAutoSync()

    # called by signal, so it is always updated    
    def updateReportWeekday(self, qd):
        dayname = QtCore.QDate.longDayName(qd.dayOfWeek())
        self.reportsWeekday.setText( dayname )
        self.tableReports.clearSelection()
        self.reportListUpdated()
        self._updateGuiReport(None)

    def reportClicked(self, modelindex):
        if self.selectedReport.changed:
            self.log.info("Report changed, can't select new one. Please save or cancel first")
            return
        row = self.tableReports.currentRow()
        _id = self.tableReports.item(row, 0).data(QtCore.Qt.UserRole)
        if _id < 0:
            return
        report = self.reportmgr.get(_id)
        if not report:
            self.log.warning("Can't find report %s in local database" % _id)
            return
        self._updateGuiReport(report)
        
        
    # -----------------------------------------------------------------------
    # Handling of buttons and report details
    # -----------------------------------------------------------------------

    def _updateLength(self):
        """Called when start or stop datetime changed"""
        start = self.dtReportStart.dateTime().toPython()
        stop = self.dtReportStop.dateTime().toPython()
        if stop < start:
            # stop can't be before start
            self.dtReportStop.setDateTime(self.dtReportStart.dateTime())
        l = (stop - start).total_seconds() / 60
        self.timeReportLen.setTime(QtCore.QTime(l // 60, l % 60))

    def _updateGuiReport(self, report):
        if report:
            s = ""
            if report.server_id >= 0:
                s +="on server(%s) " % report.server_id
            if report.updated:
                s +="locally modified "
            if report.deleted:
                s +="to be deleted "
            self.lblReportSyncState.setText(s)
            self.comboReportActivity.setCurrentIndex(self.comboReportActivity.findData(report.activityid))
            self.dtReportStart.setDateTime(report.start)
            self.dtReportStop.setDateTime(report.stop)
            
            self.txtReportComment.setText(report.comment)
            self.selectedReport.setStateEdit(report)
        else:
            self.lblReportSyncState.clear()
            self.comboReportActivity.setCurrentIndex(-1)
            d = QtCore.QDateTime.fromMSecsSinceEpoch(0)
            self.dtReportStart.setDateTime(d)
            self.dtReportStop.setDateTime(d)
            self.timeReportLen.clear()
            self.txtReportComment.clear()
            self.selectedReport.setStateNone()

    def _reportAutoSync(self):
        if self.chkReportSyncAuto.checkState():
            if self.reportmgr:
                self.reportmgr.sync()
        

    def reportSave(self):
        """Save existing report, or new report"""
        if not self.selectedReport.changed:
            self.log.info("Report not changed, nothing to do")
            return
        if self.selectedReport.state == "edit":
            report = self.selectedReport.report
        elif self.selectedReport.state == "new":
            report = Report()
            report.server_id = -1
            report.user_id = 1
            report.seq = 0

        # update report object from GUI
        activityid = self.comboReportActivity.itemData(self.comboReportActivity.currentIndex())
        if not activityid or activityid < 1:
            self.log.error("No activity selected, can't save")
            return
        report.activityid = activityid
        report.start = self.dtReportStart.dateTime().toPython()
        report.stop = self.dtReportStop.dateTime().toPython()
        report.comment = self.txtReportComment.toPlainText()
        if self.reportmgr.store(report):
            self._updateGuiReport(report)
            self._reportAutoSync()

    
    def reportNew(self):
        if self.selectedReport.changed:
            self.log.warning("Current report changed, please save/cancel first")
        else:
            self._updateGuiReport(None)
            self.selectedReport.setStateNew()
            d = QtCore.QDateTime.currentDateTime()
            d = d.addMSecs(0 - d.time().msec())
            d.setDate(self.selectedDate.date())
            self.dtReportStart.setDateTime(d)
            self.dtReportStop.setDateTime(d)
    
    def reportRemove(self):
        if self.selectedReport.changed:
            self.log.info("Please cancel all changes before removing a report")
            return
        if self.selectedReport.report:
            msgBox = QtGui.QMessageBox()
            msgBox.setText("Do you want to delete the report?")
            msgBox.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            msgBox.setDefaultButton(QtGui.QMessageBox.No)
#            response = msgBox.exec()
            response = msgBox.exec_()
            if response == QtGui.QMessageBox.Yes:
                if self.reportmgr.remove(self.selectedReport.report):
                    # we only sync if the report was marked for deletion
                    self._reportAutoSync()
                    if self.chkReportSyncAuto.checkState():
                        self.reportmgr.sync()
    
    def reportCancelChange(self):
        if self.selectedReport.changed:
            self._updateGuiReport(None)
    
    def reportChangedEvent(self):
        """Called when user edits any details of a report"""
        if self.selectedReport.state:
            self.selectedReport.changed = True


    def reportModifyStart(self):
        sender=self.sender()
        if isinstance(sender, QtGui.QToolButton):
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


    def reportModifyStop(self):
        sender=self.sender()
        if isinstance(sender, QtGui.QToolButton):
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

    # -----------------------------------------------------------------------
    # Handling of options
    # -----------------------------------------------------------------------

    def settingsDialog(self):
        import win_options
        
        o = win_options.Win_Options(self)
        a = o.exec_()

        self.log.debug("a=%s" % a)

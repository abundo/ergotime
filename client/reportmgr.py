#!/usr/bin/env python3

"""
Manage reports

Copyright (C) 2020 Anders Lowinger, anders@abundo.se

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
x
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import datetime
import queue
import threading
import random
import requests
from orderedattrdict import AttrDict

import PyQt5.QtCore as QtCore

from logger import log
from settings import sett

import util
import lib.db as db


class ReportMgr(QtCore.QObject):
    sig = QtCore.pyqtSignal()

    def __init__(self, localdb=None):
        super().__init__()
        self.localdb = localdb

        self.periodicsync_timer = None
        self._autosync = False
        self.reports = []   # local cache for todays reports
        self.toThreadQ = queue.Queue()
        self.t = threading.Thread(target=self.runThread)
        self.t.setName("ReportMgr")
        self.t.daemon = True
        self.t.start()

        sett.updated.connect(self.handle_settings)
        self.handle_settings()

    def handle_settings(self):
        """
        Handle changes in settings
        """
        if sett.report_sync_interval:
            if self.periodicsync_timer:
                # has the interval changed?
                if self.periodicsync_timer.interval != sett.report_sync_interval:
                    self.periodicsync_timer.cancel()
                    self.periodicsync_timer = None
            if self.periodicsync_timer is None:
                log.debug(f"ReportMgr starting autosync timer, interval {sett.report_sync_interval}")
                self._start_periodicsync_timer()
        else:
            if self.periodicsync_timer:
                log.debug("ReportMgr stopping autosync timer")
                self.periodicsync_timer.cancel()
            self.periodicsync_timer = None

    def _start_periodicsync_timer(self):
        jitter = sett.report_sync_interval // 10    # 10% jitter
        if jitter < 1:
            jitter = 1
        interval = sett.report_sync_interval + random.randint(-jitter, jitter)
        log.debug(f"ReportMgr interval {interval} jitter {jitter}")
        self.periodicsync_timer = threading.Timer(interval, self.periodic_sync)
        self.periodicsync_timer.setName("ReportMgr.Timer")
        self.periodicsync_timer.daemon = True
        self.periodicsync_timer.start()

    def periodic_sync(self):
        log.debug("ReportMgr.periodic_sync triggered")
        self.sync()
        self._start_periodicsync_timer()

    def init(self):
        """
        Load the list of reports from local db
        """
        self.sig.emit()

    def get(self, _id):
        for report in self.reports:
            if report._id == _id:
                return report
        try:
            sql = "SELECT * FROM report WHERE _id=?"
            report = self.localdb.select_one(sql, (_id,))
        except db.DbException as err:
            log.error(f"Cant load report with _id {_id} from local database {err}")
            return None
        return report

    def getList(self, start=None):
        stop = start + datetime.timedelta(days=1)
        try:
            sql = "SELECT * FROM report WHERE start >= ? AND start < ? ORDER BY start"
            reports = self.localdb.select_all(sql, (start, stop))
            self.reports.clear()
            for r in reports:
                self.reports.append(r)
        except db.DbException as err:
            log.error(f"Cannot load list of reports from local database {err}")

        return self.reports

    def getUnsyncronisedCount(self):
        """
        Count number of reports in local database that is not syncronised with server
        """
        sql = "SELECT count(*) FROM report WHERE server_id < 0"
        unsync_reports_count = self.localdb.count(sql)
        return unsync_reports_count

    def store(self, report):
        try:
            if report._id < 0:
                self.localdb.insert("report", d=report, primary_key="_id")
            else:
                self.localdb.update("report", d=report, primary_key="_id")
        except db.DbException as err:
            log.error(f"Cannot store report in local database {err}")
            return False
        self.sig.emit()
        if self._autosync:
            self.sync()
        return True

    def remove(self, report):
        """
        Returns True if report deleted successfully
        """
        ret = False
        try:
            if report.server_id is not None and report.server_id >= 0:
                # Report exist on server, mark for removal - next sync will remove the row
                report.deleted = 1
                self.localdb.update("report", d=report, primary_key="_id")
            else:
                # Report does not exist on server, can be removed directly
                sql = "DELETE FROM report WHERE _id=?"
                self.localdb.delete(sql, (report._id,))
            ret = True
            self.sig.emit()
            if self._autosync:
                self.sync()
        except db.DbException as err:
            log.error(f"Can't update local database when deleting report {err}")
        return ret

    def setAutosync(self, value):
        self._autosync = value
        if self._autosync:
            self.sync()

    def sync(self):
        """
        Sync the local database with the one on the server
        """
        self.toThreadQ.put(["sync"])

    def stop(self):
        if self.periodicsync_timer and self.periodicsync_timer.is_alive():
            self.periodicsync_timer.cancel()
        self.toThreadQ.put(["quit"])

##############################################################################
#
# Everything below is running in a different thread
#
##############################################################################

    def _do_sync(self):
        """
Sync the database on the server and local database, for a specific date

psql has a trigger, if a report is inserted or updated the column "seq" is
updated from a sequence. It is then easy to find out what has changed
after last sync

the trigger is configured like this
    create sequence report_seq;

    create or replace function update_modified_seq()
    returns trigger as $$
    begin
       new.seq = nextval("report_seq");
       return new;
    end;
    $$ language "plpgsql";

    update report set seq = 0 where seq is null;
    create trigger insert_customer_seq before insert on report for each row execute procedure update_modified_seq();
    create trigger update_customer_seq before update on report for each row execute procedure update_modified_seq();


 No reports can be locked when sync starts, and no locking is allowed during sync

 1. Send delete request to server for reports being marked for deletion
    if failure -> stop, otherwise delete flag will be lost further down by the sync

 2. Send new reports to server
    if failure -> stop, otherwise the entries will be removed further down by the sync

 3. Send updated reports to server
    if failure -> stop, otherwise changes will be lost further down by the sync

 Note: 1-3 could potentially be done in one step
 5. Request from server all reports with seq > max_seq and modified > first sync date
 6. For each received report
      if report in local database:
         if report is marked deleted
            remove from local database
         else
            update report in local database
      else
         insert report in local database

"""
        reportapi = f"{sett.server_url}/api/report"
        log.debugf(log.DEBUG_REPORTMGR, "Sync() Send deleted reports to server")
        try:
            sql = "SELECT * FROM report WHERE deleted=1"
            data = self.thread_db.select_all(sql)
        except db.DbException as err:
            log.error(f"  Can't load reports marked for deletion from local database {err}")
            return
        for report in data:
            log.debugf(log.DEBUG_REPORTMGR, f"  Delete report on server {report}")

            report._id = report.server_id   # use server _id
            report.updated = 0
            try:
                url = f"{reportapi}/{report._id}"
                r = requests.put(url, data=report)
            except requests.exceptions.RequestException as err:
                log.error(f"  Can't update report on server {err}")
                return

        log.debugf(log.DEBUG_REPORTMGR, "Sync() Send new reports to server")
        try:
            sql = "SELECT * FROM report WHERE server_id < 0"
            data = self.thread_db.select_all(sql)
        except db.DbException as err:
            log.error(f"  Can't load new reports from local database {err}")
            return
        for local_report in data:
            log.debugf(log.DEBUG_REPORTMGR, f"  Sending new report to server {local_report}")
            _id = local_report._id
            local_report._id = -1
            try:
                url = reportapi
                r = requests.post(url, data=local_report)
                srv_data = r.json()
                print("srv_data", srv_data)
                srv_data = AttrDict(srv_data)
            except requests.exceptions.RequestException as err:
                log.error(f"  Can't send new report to server {err}")
                return
            local_report.server_id = srv_data._id
            local_report._id = _id
            try:
                self.thread_db.update("report", d=local_report, primary_key="_id")
            except db.DbException as err:
                log.error(f"  Can't update report in local database {err}")
                return

        # todo: load report from server to see if it is changed first

        log.debugf(log.DEBUG_REPORTMGR, "Sync() Send updated reports To server")
        try:
            sql = "SELECT * FROM report WHERE updated != 0 AND updated IS NOT NULL"
            local_reports = self.thread_db.select_all(sql)
        except db.DbException as err:
            log.error(f"  Cannot load updated reports from local database, {err}")
            return
        for local_report in local_reports:
            log.debugf(log.DEBUG_REPORTMGR, f"  Updating report on server {local_report}")
            local_report._id = local_report.server_id
            local_report.updated = 0
            try:
                r = requests.put(url=f"{reportapi}/{local_report._id}", data=local_report)
            except requests.exceptions.RequestException as err:
                log.error(f"  Cannot send new report to server, {err}")
                return
            try:
                self.thread_db.update("report", d=local_report, primary_key="_id")
            except db.DbException as err:
                log.error(f"  Error storing updated report in local database {err}")
                return

        log.debugf(log.DEBUG_REPORTMGR, "Sync() Get new/updated reports from server")

        # first, get highest seq number from local database, anything higher than this
        # we don't have locally
        try:
            sql = "SELECT MAX(seq) FROM report"
            local_data = self.thread_db.select_one(sql)
        except db.DbException as err:
            log.error(f"  Error getting highest seq from local database {err}")
            return
        if local_data and local_data["MAX(seq)"] is not None:
            local_max_seq = local_data["MAX(seq)"]
        else:
            local_max_seq = 0

        step = 10   # number of reports in each loop
        offset = 0
        setMaxLocalSeq = local_max_seq  # if we delete local reports, we may loose highest seq
        self.reports.clear()            # clear cache, we may get new data from server
        error = False
        while True and not error:
            try:
                url = f"{reportapi}/sync/{local_max_seq}"
                params = {"limit": step, "offset": offset, "maxage": 180}
                r = requests.get(url, params=params)
                srv_reports = r.json()
                srv_reports = srv_reports["data"]
            except requests.exceptions.RequestException as err:
                log.error(f"  Can't get new/updated reports from server, {err}")
                break

            if len(srv_reports) < 1:
                break   # no more data

            log.debugf(log.DEBUG_REPORTMGR, f"------------------------------- offset {offset}")
            for srv_report in srv_reports:
                srv_report = AttrDict(srv_report)
                # check if we have the report locally
                try:
                    sql = "SELECT * FROM report WHERE server_id=?"
                    local_data = self.thread_db.select_one(sql, (srv_report._id,))
                except db.DbException as err:
                    log.error(f"  Can't load report from local database {err}")
                    error = True
                    break
                if srv_report.seq > setMaxLocalSeq:
                    setMaxLocalSeq = srv_report.seq
                if local_data:
                    # we already have report in local database
                    local_report = local_data

                    if srv_report.deleted:
                        # report is marked as deleted on server, remove locally
                        log.debugf(log.DEBUG_REPORTMGR, f"  From server, report with _id {srv_report._id} is deleted")
                        try:
                            sql = "DELETE FROM report WHERE _id=?"
                            deleted_count = self.thread_db.delete(sql, (local_report._id,))
                        except db.DbException as err:
                            log.error(f"  Can't delete report from local database {err}")
                            error = True
                            break
                        if deleted_count < 1:
                            log.error("  Can't delete report from local database")

                    else:
                        # report is updated on server, replace local copy with server report
                        log.debugf(log.DEBUG_REPORTMGR, f"  From server, report with _id {srv_report._id} is updated")
                        srv_report.server_id = srv_report._id
                        srv_report._id = local_report._id
                        try:
                            self.thread_db.update("report", d=srv_report)
                        except db.DbException as err:
                            log.error(f"  Can't replace report in local database with one from server {err}")
                            error = True
                            break
                else:
                    # we don't have the report locally, store the one from the server as a new one
                    if srv_report.deleted:
                        # TODO maxseqnr
                        continue    # Ignore the report, it is deleted and we dont have it locally
                    log.debugf(log.DEBUG_REPORTMGR, f"  From server, report with _id {srv_report._id} is new")
                    srv_report.server_id = srv_report._id
                    srv_report._id = -1
                    srv_report.updated = 0
                    try:
                        self.thread_db.insert("report", d=srv_report)
                    except db.DbException as err:
                        log.error(f"  Can't store new server report in local database {err}")
                        error = True
                        break

            offset += step

        if setMaxLocalSeq > local_max_seq:
            # just get any report from local database, and set seq
            try:
                sql = "SELECT * FROM report ORDER BY seq desc LIMIT 1"
                local_report = self.thread_db.select_one(sql)
            except db.DbException as err:
                log.error(f"  Can't get highest seq from local database {err}")
                return
            if local_report:
                if local_report.seq < setMaxLocalSeq:
                    local_report.seq = setMaxLocalSeq
                    try:
                        self.thread_db.update("report", d=local_report)
                    except db.DbException as err:
                        log.error(f"  Can't update highest seq in local database {err}")

        self.sig.emit()

    def runThread(self):
        log.debugf(log.DEBUG_REPORTMGR, "Starting reportmgr thread")

        # connect to local database, we have a separate connection in this thread
        # to simplify database operations
        log.debugf(log.DEBUG_REPORTMGR, "Opening local database")
        self.thread_db = util.openLocalDatabase2()

        while True:
            req = self.toThreadQ.get()
            log.debugf(log.DEBUG_REPORTMGR, f"reportmgr, request={req}")
            if req[0] == "quit":
                log.debugf(log.DEBUG_REPORTMGR, "reportmgr thread stopping")
                return

            elif req[0] == "sync":
                log.info("Sync reports with server started")
                self._do_sync()
                log.info("Sync reports with server finished")
            else:
                log.error(log.DEBUG_REPORTMGR, f"reportmgr thread, unknown command {req[0]}")


if __name__ == "__main__":
    # Module test
    import time
    import logging
    from PyQt5.Qt import QApplication

    log.setLevel(logging.DEBUG)
    app = util.createQApplication()

    localdb = util.openLocalDatabase2(":memory:")

    reportMgr = ReportMgr(localdb=localdb)
    reportMgr.init()
    reportMgr.sync()
    reportMgr.stop()

    while not reportMgr.toThreadQ.empty():
        QApplication.processEvents()
        time.sleep(0.5)

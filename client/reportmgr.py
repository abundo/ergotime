#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Manage reports

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
import queue
import threading

import PyQt5.QtCore as QtCore

from myglobals import *
from logger import log
from settings import sett

import util

import basium
from model.report import Report


class ReportMgr(QtCore.QObject):
    sig = QtCore.pyqtSignal()
    
    def __init__(self, main_db=None):
        super().__init__()
        self.main_db = main_db

        self._autosync = False
        self.reports = []   # local cache for todays reports
        self.toThreadQ = queue.Queue()
        self.t = threading.Thread(target=self.runThread)
        self.t.setName("ReportMgr")
        self.t.daemon = True
        self.t.start()

    # Load the list of reports from local db
    def init(self):
        self.sig.emit()

    def get(self, _id):
        for report in self.reports:
            if report._id == _id:
                return report
        report = Report(_id)
        try:
            data = self.main_db.load(report)
        except basium.Error as err: 
            log.error("Cant load report with _id %s from local database %s" % (_id, err))
            return None
        if len(data) > 0:
            return data[0]
        return None

    def getList(self, start=None):
        r = Report()
        query = self.main_db.query(r)
        stop = start + datetime.timedelta(days=1)
        query.filter(r.q.start, ">=", start).filter(r.q.start, "<", stop).order(r.q.start)
        try:
            data = self.main_db.load(query)
            self.reports.clear()
            for r in data:
                self.reports.append(r)
        except basium.Error as err:
            log.error("Cannot load list of reports from local database %s" % err)

        return self.reports

    def getUnsyncronisedCount(self):
        """Count number of reports in local database that is not syncronised with server"""
        return 0
        report = Report()
        query = self.local_db.query().filter(report.q.server_id, "<", 0)
        count = self.main_db.count(query)
        return count
    
    def store(self, report):
        try:
            self.local_db.store(report)
        except basium.Error as err:
            log.error("Cannot store report in local database %s" % err)
            return False
        self.sig.emit()
        if self._autosync:
            self.sync()
        return True

    def remove(self, report):
        ret = False
        try:
            if report.server_id != None and report.server_id >= 0:
                report.deleted = True   # Actual removal will be done during next sync
                self.main_db.store(report)
                ret = True
            else:
                self.main_db.delete(report)
            self.sig.emit()
            if self._autosync:
                self.sync()
        except basium.Error as err:
            log.error("Can't update local database when deleting report %s" % err)
        return ret

    def setAutosync(self, value):
        self._autosync = value
        if self._autosync:
            self.sync()

    # Sync the local database with the one on the server
    def sync(self):
        self.toThreadQ.put( ["sync"] )

    def stop(self):
        self.toThreadQ.put( ["quit"] )


##############################################################################
#
# Everything below is running in a different thread
#
##############################################################################


    def _do_sync(self):
        """
Sync the database on the server and local database, for a specific date

psql has a trigger, if a report is inserted or updated the column 'seq' is
updated from a sequence. It is then easy to find out what has changed
after last sync

the trigger is configured like this
    create sequence report_seq;

    create or replace function update_modified_seq()
    returns trigger as $$
    begin
       new.seq = nextval('report_seq');
       return new;
    end;
    $$ language 'plpgsql';

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
        now = datetime.datetime.now().replace(microsecond=0)
        
        log.debugf(DEBUG_REPORTMGR, "Sync() Send deleted reports to server")
        r = Report()
        query = self.local_db.query().filter(r.q.deleted, "=", True)
        try:
            data = self.local_db.load(query)
        except basium.Error as err:
            log.error("  Can't load reports marked for deletion from local database %s" % err)
            return
        for report in data:
            log.debugf(DEBUG_REPORTMGR, "  Delete report on server %s" % report)
            report._id = report.server_id
            try:
                self.srv_db.store(report)
            except basium.Error as err:
                log.error("  Can't update report on server %s" % err)
                return

        log.debugf(DEBUG_REPORTMGR, "Sync() Send new reports to server")
        r = Report()
        query = self.local_db.query().filter(r.q.server_id, "<", 0)
        try:
            data = self.local_db.load(query)
        except basium.Error as err:
            log.error("  Can't load new reports from local database %s" % err)
            return
        for local_report in data:
            log.debugf(DEBUG_REPORTMGR, "  Sending new report to server _id=%s" % local_report._id)
            log.debugf(DEBUG_REPORTMGR, "  Sending new report to server %s" % local_report)
            _id = local_report._id
            local_report._id = -1
            try:
                self.srv_db.store(local_report)
            except basium.Error as err:
                log.error("  Can't send new report to server %s" % err)
                return
            local_report.server_id = local_report._id
            local_report._id = _id
            try:
                self.local_db.store(local_report)
            except basium.Error as err:
                log.error("  Error saving server_id in local database %s" % err)
                return
            
        # todo: load report from server to see if it is changed first
        log.debugf(DEBUG_REPORTMGR, "Sync() Send updated reports To server")
        r = Report()
        query = self.local_db.query().filter(r.q.updated, "=", True).filter(r.q.server_id, "!=", None)
        try:
            local_data = self.local_db.load(query)
        except basium.Error as err:
            log.error("  Error loading local updated reports %s" % err)
            return
        for local_report in local_data:
            log.debugf(DEBUG_REPORTMGR, "  Updating report on server %s" % local_report)
            local_report._id = local_report.server_id
            try:
                self.srv_db.store(local_report)
            except basium.Error as err:
                log.error("  Error sending new report to server %s" % err)
                return
            local_report.updated = False
            try:
                self.local_db.store(local_report)
            except basium.Error as err:
                log.error("  Error storing updated report in local database %s" % err)
                return


        log.debugf(DEBUG_REPORTMGR, "Sync() Get new/updated reports from server")

        # first, get highest modified seq number from local database
        query = self.local_db.query()
        query.order(r.q.seq, desc=True).limit(rowcount=1)
        try:
            local_data = self.local_db.load(query)
        except basium.Error as err:
            log.error("  Error getting highest seq from local database %s" % err)
            return
        if len(local_data) > 0:
            local_max_seq = local_data[0].seq
            modified = None
        else:
            local_max_seq = 0
            modified = now - datetime.timedelta(days=90)     # todo, settings for how long back we want to sync

        step = 10   # number of reports in each loop
        offset = 0
        setMaxLocalSeq = local_max_seq  # if we delete local reports, we may loose highest seq
        self.reports.clear()
        error = False
        while True and not error:
            srv_query = self.srv_db.query()
            srv_query.filter(r.q.seq, ">", local_max_seq)
            if modified:
                srv_query.filter(r.q.modified, ">", modified)
            srv_query.order(r.q._id)
            srv_query.limit(offset=offset, rowcount=step)
            log.debugf(DEBUG_REPORTMGR, "query " + srv_query.encode())
            try:
                srv_data = self.srv_db.load(srv_query)
            except basium.Error as err:
                log.error("  Can't get Error getting modified timestamp %s" % err)
                break

            if len(srv_data) < 1:
                break   # no more data

            if len(srv_data):
                log.debugf(DEBUG_REPORTMGR, "------------------------------- offset %d" % offset)
            for srv_report in srv_data:
                local_query = self.local_db.query()
                local_query.filter(r.q.server_id, "=", srv_report._id)
                try:
                    local_data = self.local_db.load(local_query)
                except basium.Error as err:
                    log.error("  Can't load report from local database %s" % err)
                    error = True
                    break
                if len(local_data) > 0:
                    # we have report in local database
                    local_report = local_data[0]
                    
                    if srv_report.deleted:
                        # report is marked as deleted on server, remove locally
                        log.debugf(DEBUG_REPORTMGR, "  From server, report with _id %s is deleted" % srv_report._id)
                        if srv_report.seq > setMaxLocalSeq:
                            setMaxLocalSeq = srv_report.seq
                        try:
                            deleted_count = self.local_db.delete(local_report)
                        except basium.Error as err:
                            log.error("  Can't delete report from local database %s" % err)
                            error = True
                            break
                        if deleted_count == 0:
                            log.error("  Can't delete report from local database")
                            
                    else:
                        # report is updated on server, replace local copy with server report
                        log.debugf(DEBUG_REPORTMGR, "  From server, report with _id %s is updated" % srv_report._id)
                        srv_report.server_id = srv_report._id
                        srv_report._id = local_report._id
                        try:
                            self.local_db.store(srv_report)
                        except basium.Error as err:
                            log.error("  Can't replace report in local database with one from server %s" % err)
                            error = True
                            break
                else:
                    # we don't have the report locally, store the one from the server as a new one
                    log.debugf(DEBUG_REPORTMGR, "  From server, report with _id %s is new" % srv_report._id)
                    srv_report.server_id = srv_report._id
                    srv_report._id = -1
                    try:
                        self.local_db.store(srv_report)
                    except basium.Error as err:
                        log.error("  Can't store new server report in local database %s" % err)
                        error = True
                        break

            offset += step                
            # check if we have the record locally

        if setMaxLocalSeq > local_max_seq:
            # just get any report from local database, and set seq
            query = self.local_db.query()
            query.order(r.q.seq, desc=True).limit(rowcount=1)
            try:
                local_data = self.local_db.load(query)
            except basium.Error as err:
                log.error("  Can't get highest seq from local database %s" % err)
                return
            if len(local_data) > 0:
                local_report = local_data[0]
                if local_report.seq < setMaxLocalSeq:
                    local_report.seq = setMaxLocalSeq
                    try:
                        self.local_db.store(local_report)
                    except basium.Error as err:
                        log.error("  Can't update highest seq in local database %s" % err)

        log.debugf(DEBUG_REPORTMGR, "Sync() done")
        self.sig.emit()


    def runThread(self):
        log.debugf(DEBUG_REPORTMGR, "Starting reportmgr thread")

        # connect to local database, we have a separate connection in this thread to 
        # simplify database operations
        log.debugf(DEBUG_REPORTMGR, "Opening local database")
        self.local_dbconf, self.local_db = util.openLocalDatabase()
        
        while True:
            req = self.toThreadQ.get()
            log.debugf(DEBUG_REPORTMGR, "reportmgr, request=%s" % req)
            if req[0] == "quit":
                log.debugf(DEBUG_REPORTMGR, "reportmgr thread stopping")
                return

            elif req[0] == "sync":
                self.remote_dbconf, self.srv_db = util.openRemoteDatabase()
                self._do_sync()
                
#                self.srv_db.close()
#                self.local_db.close()
                
            else:
                log.error(DEBUG_REPORTMGR, "reportmgr thread, unknown command %s" % req[0])

    ##########################################################################
    #
    # Everything below is running in a different thread
    #
    ##########################################################################

    def runProcess(self):
        pass

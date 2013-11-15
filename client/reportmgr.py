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
import multiprocessing

import PySide.QtCore as QtCore

import basium
from report import Report

ergotimeserver="http://ergotime.int.abundo.se:8000"
debug = False

class Communicate(QtCore.QObject):
    updated = QtCore.Signal()

class ReportMgr(QtCore.QObject):
    def __init__(self, log=None, basium=None):
        self.log = log

        self.main_basium = basium
        self.reports = []   # local cache for todays reports
        self.toThreadQ = queue.Queue()
        self.t = threading.Thread(target=self.runThread)
        self.t.daemon = True
        self.t.start()
        
        self.sig = Communicate()


    # Load the list of reports from local db
    def init(self):
        self.sig.updated.emit()

    def get(self, _id):
        for report in self.reports:
            if report._id == _id:
                return report
        report = Report()
        report._id = _id
        data, status = self.main_basium.load(report)
        if status.isError():
            self.log.error("Cant load report with _id %s from local database %s" % (_id, status.getError()))
            return None
        if len(data) > 0:
            return data[0]
        return None

    def getList(self, start=None):
        r = Report()
        query = self.main_basium.query(r)
        stop = start + datetime.timedelta(days=1)
        query.filter(r.q.start, ">=", start).filter(r.q.start, "<", stop).order(r.q.start)
        data, status = self.main_basium.load(query)
        self.reports.clear()
        if status.isError():
            self.log.error("Cannot load list of reports from local database %s" % status.getError())
        else:
            for r in data:
                self.reports.append(r)
        
        return self.reports

    def store(self, report):
        report.updated = True
        self.log.debug(str(report))
        response = self.local_db.store(report)
        if response.isError():
            self.log.error("Cannot store report in local database %s" % response.isError)
            return False
        self.sig.updated.emit()
        return True

    def remove(self, report):
        ret = False
        if report.server_id >= 0:
            # Actual removal will be done during next sync
            report.deleted = True
            self.main_basium.store(report)
            ret = True
        else:
            self.main_basium.delete(report)
        self.sig.updated.emit()
        return ret

    # Sync the local database with the one on the server
    def sync(self):
        self.toThreadQ.put( ["sync"] )

    def stop(self):
        self.toThreadQ.put( ["quit"] )


    ##########################################################################
    #
    # Everything below is running in a different thread
    #
    ##########################################################################


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
        # 
        self.log.debug("Send reports marked for deletion in local database, to server")
        r = Report()
        query = self.local_db.query().filter(r.q.deleted, "=", True)
        data, status = self.local_db.load(query)
        if status.isError():
            self.log.error("Can't load reports marked for deletion from local database %s" % status.getError())
            return
        for report in data:
            self.log.debug("Marking report on server as deleted %s" % report)
            report._id = report.server_id
            response = self.srv_db.store(report)
            if response.isError():
                self.log.error("Can't update report on server %s" % response.getError())
                return

        #
        self.log.debug("Send new reports in local database, to server")
        r = Report()
        query = self.local_db.query().filter(r.q.server_id, "<", 0)
        data, status = self.local_db.load(query)
        if status.isError():
            self.log.error("Can't load new reports from local database %s" % status.getError())
            return
        for local_report in data:
            self.log.debug("Sending new report to server %s" % local_report)
            _id = local_report._id
            local_report._id = -1
            response = self.srv_db.store(local_report)
            if response.isError():
                self.log.error("Can't send new report to server %s" % response.getError())
                return
            local_report.server_id = local_report._id
            local_report._id = _id
            response = self.local_db.store(local_report)
            if response.isError():
                self.log.error("Error saving server_id in local database %s" % response.getError())
                return
            
        # todo: load report from server to see if it is changed first
        self.log.debug("Send updated reports in local database, to server")
        r = Report()
        query = self.local_db.query().filter(r.q.updated, "=", True).filter(r.q.server_id, "!=", None)
        local_data, local_status = self.local_db.load(query)
        if local_status.isError():
            self.log.error("Error loading local updated reports %s" % local_status.getError())
            return
        for local_report in local_data:
            self.log.debug("Updating report on server %s" % local_report)
            local_report._id = local_report.server_id
            srv_response = self.srv_db.store(local_report)
            if srv_response.isError():
                self.log.error("Error sending new report to server %s" % srv_response.getError())
                return
            local_report.modified = False
            local_response2 = self.local_db.store(local_report)
            if local_response2.isError():
                self.log.error("Error storing updated report in local database %s" % local_response2.getError())
                return


        self.log.debug("Get new/updated reports from server")

        # first, get highest modified seq number from local database
        query = self.local_db.query()
        query.order(r.q.seq, desc=True).limit(rowcount=1)
        local_data, local_status = self.local_db.load(query)
        if local_status.isError():
            self.log.error("Error getting highest seq from local database %s" % local_status.getError())
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
            self.log.debug("query " + srv_query.encode())
            srv_data, srv_status = self.srv_db.load(srv_query)
            if srv_status.isError():
                self.log.error("Can't get Error getting modified timestamp %s" % srv_status.getError())
                break

            if len(srv_data) < 1:
                break   # no more data


            self.log.debug("------------------------------- offset %d" % offset)
            for srv_report in srv_data:
                self.log.debug("From server, report with _id %s" % srv_report._id)
                local_query = self.local_db.query()
                local_query.filter(r.q.server_id, "=", srv_report._id)
                local_data, local_status = self.local_db.load(local_query)
                if local_status.isError():
                    self.log.error("Can't load report from local database %s" % local_status.getError())
                    error = True
                    break
                if len(local_data) > 0:
                    # we have report in local database
                    local_report = local_data[0]
                    
                    if srv_report.deleted:
                        # report is marked as deleted on server, remove locally
                        if srv_report.seq > setMaxLocalSeq:
                            setMaxLocalSeq = srv_report.seq
                        local_response2 = self.local_db.delete(local_report)
                        if local_response2.isError():
                            self.log.error("Can't delete report from local database %s" % local_response2.getError())
                            error = True
                            break
                    else:
                        # report is updated on server, replace local copy with server report
                        srv_report.server_id = srv_report._id
                        srv_report._id = local_report._id
                        local_response2 = self.local_db.store(srv_report)
                        if local_response2.isError():
                            self.log.error("Can't replace report in local database with one from server %s" % local_response2.getError())
                            error = True
                            break
                else:
                    # we don't have the report locally, store the one from the server as a new one
                    srv_report.server_id = srv_report._id
                    srv_report._id = -1
                    local_response2 = self.local_db.store(srv_report)
                    if local_response2.isError():
                        self.log.error("Can't store new server report in local database %s" % local_response2.getError())
                        error = True
                        break

            offset += step                
            # check if we have the record locally

        if setMaxLocalSeq > local_max_seq:
            # just get any report from local database, and set seq
            query = self.local_db.query()
            query.order(r.q.seq, desc=True).limit(rowcount=1)
            local_data, local_status = self.local_db.load(query)
            if local_status.isError():
                self.log.error("Can't get highest seq from local database %s" % local_status.getError())
                return
            if len(local_data) > 0:
                local_report = local_data[0]
                if local_report.seq < setMaxLocalSeq:
                    local_report.seq = setMaxLocalSeq
                    local_response2 = self.local_db.store(local_report)
                    if local_response2.isError():
                        self.log.error("Can't update highest seq in local database %s" % local_response2.getError())

        self.log.debug("reportmgr sync done")
        self.sig.updated.emit()


    def runThread(self):
        self.log.debug("Starting reportmgr thread")

        # connect to database, we have a separate connection in this thread to 
        # simplify database operations
        self.local_dbconf = basium.DbConf(database="d:/temp/ergotime/ergotime.db", log=self.log, debugSQL=True)
        self.log.debug("ReportMgr thread, Opening local database %s" % self.local_dbconf.database)
        self.local_db = basium.Basium(driver="sqlite", checkTables=False, dbconf=self.local_dbconf)
        if not self.local_db.start():
            self.log.error("ReportMgr thread, Cannot open local database, very limited functionality")

        self.remote_dbconf = basium.DbConf(host=ergotimeserver, database="ergotime", log=self.log) # username="", password=""
        self.srv_db = basium.Basium(driver="json", checkTables=False, dbconf=self.remote_dbconf)
        if not self.srv_db.start():
            self.log.error("ReportMgr thread, Cannot start basium to remote server")

        while True:
            req = self.toThreadQ.get()
            self.log.debug("reportmgr, request=%s" % req)
            if req[0] == "quit":
                self.log.debug("reportmgr thread stopping")
                return

            elif req[0] == "sync":
                self._do_sync()
            else:
                self.log.error("reportmgr thread, unknown command %s" % req[0])

    ##########################################################################
    #
    # Everything below is running in a different thread
    #
    ##########################################################################

    def runProcess(self):
        pass

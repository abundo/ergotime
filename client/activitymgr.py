#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Manage activities

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

import queue
import threading

import PySide.QtCore as QtCore

import basium
from activity import Activity

ergotimeserver="http://ergotime.int.abundo.se:8000"
debug = False

class Communicate(QtCore.QObject):
    updated = QtCore.Signal()

class ActivityMgr(QtCore.QObject):
    def __init__(self, log=None, basium=None):
        self.log = log
        self.main_basium = basium
        self.activities = []
        self.toThreadQ = queue.Queue()
        self.t = threading.Thread(target=self.run)
        self.t.daemon = True
        self.t.start()
        
        self.sig = Communicate()

    # Load the list of activities from local db
    def init(self):
        self._loadList()
        self.sig.updated.emit()

    def get(self, activityid):
        for a in self.activities:
            if a.server_id == activityid:
                return a
        return None

    def _loadList(self):
        activity = Activity()
        dbquery = self.main_basium.query().order(activity.q.name)
        response = self.main_basium.load(dbquery)
        if response.isError():
            self.log.error("Cannot load activitylist from local database, %s" % response.getError())
            return
        self.activities.clear()
        for activity in response.data:
            self.activities.append(activity)

    def getList(self):
        return self.activities
   
    # Sync the local database with the one on the server
    def sync(self):
        self.toThreadQ.put("sync")

    def save(self):
        self.log.debug("Saving activities")
        for a in self.activities:
            self.log.debug("Storing activity %s" % a.name)
            resp = self.basium.store(a)
            self.log.debug("  %s" % resp.getError())
        

    def stop(self):
        self.toThreadQ.put("quit")

    def _do_sync(self):
        a = Activity()
        query = self.remote_basium.query(a)
        response = self.remote_basium.load(query)
        if response.isError():
            self.log.error("Cannot load list of activities from server")
        
        for srv_activity in response.data:
            query = self.basium.query().filter(a.q.server_id, "=", srv_activity._id)
            response = self.basium.load(query)
            if response.isError():
                self.log.error("Can't load local activity %s" % response.getError())
                return
            if len(response.data) > 0:
                # we have the report locally, check if changed
                local_activity = response.data[0]
                if local_activity.name != srv_activity.name or local_activity.active != srv_activity.active:
                    srv_activity.server_id = srv_activity._id
                    srv_activity._id = local_activity._id
                    response = self.basium.store(srv_activity)
                    if response.isError():
                        self.log.error("Cannot update local activity %s" % response.getError())
                        return
            else:
                # new activity
                srv_activity.server_id = srv_activity._id
                srv_activity._id = -1
                response = self.basium.store(srv_activity)
                if response.isError():
                    self.log.error("Cannot store new activity in local database %s" % response.getError())
                    return

        self._loadList()
        self.sig.updated.emit()
        
    
    def run(self):
        self.log.debug("Starting activitymgr thread")
        
        # connect to database, we have a separate connection in this thread to 
        # simplify database operations
        self.dbconf = basium.DbConf(database="d:/temp/ergotime/ergotime.db", log=self.log)
        self.log.debug("ActivityMgr thread, Opening local database %s" % self.dbconf.database)
        self.basium = basium.Basium(driver="sqlite", checkTables=False, dbconf=self.dbconf)
        if not self.basium.start():
            self.log.error("ActivityMgr thread, Cannot open local database, very limited functionality")

        self.remote_dbconf = basium.DbConf(host=ergotimeserver, database="ergotime", log=self.log) # username="", password=""
        self.remote_basium = basium.Basium(driver="json", checkTables=False, dbconf=self.remote_dbconf)
        if not self.remote_basium.start():
            self.log.error("ReportMgr thread, Cannot start basium to remote server")
        
        while True:
            req = self.toThreadQ.get()
            self.log.debug("activitymgr, request=%s" % req)
            if req == "quit":
                self.log.debug("activitymgr thread stopping")
                return
            elif req == "sync":
                self._do_sync()
            else:
                self.log.error("activitymgr thread, unknown command %s" % req)
                

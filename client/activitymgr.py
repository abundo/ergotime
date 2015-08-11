#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Manage activities
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

import queue
import threading

import PyQt5.QtCore as QtCore

from myglobals import *
from logger import log
from settings import sett

import util

import basium
from common.activity import Activity


class ActivityMgr(QtCore.QObject):
    sig = QtCore.pyqtSignal()
    
    def __init__(self, main_db=None):
        super().__init__()
        self.main_db = main_db
        
        self.activities = []
        self.activities_id = {}
        self.toThreadQ = queue.Queue()
        self.t = threading.Thread(target=self.run)
        self.t.setName("ActivityMGR")
        self.t.daemon = True
        self.t.start()
        
    # Load the list of activities from local db
    def init(self):
        self._loadList()
        self.sig.emit()

    def get(self, activityid):
        if activityid in self.activities_id:
            return self.activities_id[activityid]
        return None

    def _loadList(self):
        activity = Activity()
        dbquery = self.main_db.query().order(activity.q.name)
        try:
            data = self.main_db.load(dbquery)
        except basium.Error as err:
            log.error("Cannot load activitylist from local database, %s" % err)
            return
        self.activities.clear()
        self.activities_id.clear()
        for activity in data:
            self.activities.append(activity)
            self.activities_id[activity.server_id] = activity

    def getList(self):
        return self.activities
   
    # Sync the local database with the one on the server
    def sync(self):
        self.toThreadQ.put("sync")

    def save(self):
        log.debugf(DEBUG_ACTIVITYMGR, "Saving activities")
        for a in self.activities:
            log.debugf(DEBUG_ACTIVITYMGR, "Storing activity %s" % a.name)
            try:
                self.basium.store(a)
            except basium.Error as err:
                log.error("Cant save activity in local database %s" % err)
        

    def stop(self):
        self.toThreadQ.put("quit")

    def _do_sync(self):
        a = Activity()
        query = self.remote_db.query(a)
        try:
            data = self.remote_db.load(query)
        except basium.Error as err:
            log.error("Cannot load list of activities from server %s" % err)
            return

        for srv_activity in data:
            # logger.global("Server activity %s" % srv_activity)
            query = self.basium.query().filter(a.q.server_id, "=", srv_activity._id)
            try:
                data2 = self.basium.load(query)
            except basium.Error as err:
                log.error("Can't load local activity %s" % err)
                return
            if len(data2) > 0:
                # we have the report locally, check if changed
                local_activity = data2[0]
                if local_activity.name != srv_activity.name or local_activity.active != srv_activity.active:
                    log.debugf(DEBUG_ACTIVITYMGR, "Updating local copy of activity")
                    local_activity.name = srv_activity.name
                    local_activity.server_id = srv_activity._id
                    local_activity.active = srv_activity.active
                    try:
                        self.basium.store(local_activity)
                    except basium.Error as err:
                        log.error("Cannot update local activity %s" % err)
                        return
            else:
                # new activity
                log.debugf(DEBUG_ACTIVITYMGR, "New activity '%s' on server, storing in local database" % srv_activity.name)
                srv_activity.server_id = srv_activity._id
                srv_activity._id = -1
                try:
                    self.basium.store(srv_activity)
                except basium.Error as err:
                    log.error("Cannot store new activity in local database %s" % err)
                    return

        self._loadList()
        self.sig.emit()
        
    
    def run(self):
        log.debugf(DEBUG_ACTIVITYMGR, "Starting activitymgr thread")
        
        while True:
            req = self.toThreadQ.get()
            log.debugf(DEBUG_ACTIVITYMGR, "activitymgr, request=%s" % req)
            if req == "quit":
                log.debugf(DEBUG_ACTIVITYMGR, "activitymgr thread stopping")
                return
            elif req == "sync":
                
                # connect to database, we have a separate connection in this thread to 
                # simplify database operations
                tmp, self.basium = util.openLocalDatabase()
                tmp, self.remote_db = util.openRemoteDatabase()

                self._do_sync()

#                self.srv_db.close()        # when basium supports close()
#                self.local_db.close()      # when basium supports close()
            else:
                log.error("activitymgr thread, unknown command %s" % req)

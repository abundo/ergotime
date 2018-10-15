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
import random
from orderedattrdict import AttrDict

import PyQt5.QtCore as QtCore

from myglobals import *
from logger import log
from settings import sett

import util
import lib.db as db
import lib.network as network


class ActivityMgr(QtCore.QObject):
    sig = QtCore.pyqtSignal()
    
    def __init__(self, localdb=None):
        super().__init__()
        self.localdb = localdb

        self.periodicsync_timer = None
                
        self.activities = []
        self.activities_id = {}
        self.toThreadQ = queue.Queue()
        self.t = threading.Thread(target=self.run)
        self.t.setName("ActivityMgr")
        self.t.daemon = True
        self.t.start()

        sett.updated.connect(self.handle_settings)
        self.handle_settings()

    def handle_settings(self):
        """
        Handle changes in settings
        """
        if sett.activity_sync_interval:
            if self.periodicsync_timer:
                # has the interval changed?
                if self.periodicsync_timer.interval != sett.activity_sync_interval:
                    self.periodicsync_timer.cancel()
                    self.periodicsync_timer = None
            if self.periodicsync_timer is None:
                log.debug("ActivityMgr starting autosync timer, interval %s" % sett.activity_sync_interval)
                self._start_periodicsync_timer()
        else:
            if self.periodicsync_timer:
                log.debug("ActivityMgr stopping autosync timer")
                self.periodicsync_timer.cancel()
            self.periodicsync_timer = None

    def _start_periodicsync_timer(self):
        jitter = sett.activity_sync_interval // 10    # 10% jitter
        if jitter < 1:
            jitter = 1
        interval = sett.activity_sync_interval + random.randint(-jitter, jitter)
        log.debug("ActivityMgr interval %s jitter %s" % (interval, jitter))
        self.periodicsync_timer = threading.Timer(interval, self.periodic_sync)
        self.periodicsync_timer.daemon = True
        self.periodicsync_timer.setName("ActivityMgr.Timer")
        self.periodicsync_timer.start()

    def periodic_sync(self):
        log.debug("ActivityMgr.periodic_sync triggered")
        self.sync()
        self._start_periodicsync_timer()
        
    def init(self):
        """Load the list of activities from local db"""
        self._loadList()
        self.sig.emit()

    def get(self, activityid):
        if activityid in self.activities_id:
            return self.activities_id[activityid]
        return None

    def getList(self):
        return self.activities
   
    def save(self):
        log.debugf(DEBUG_ACTIVITYMGR, "Saving activities")
        for activity in self.activities:
            log.debugf(DEBUG_ACTIVITYMGR, "Storing activity %s" % activity.name)
            try:
                self.localdb.update("activity", d=activity, primary_key="_id")
            except db.DbException as err:
                log.error("Cant save activity in local database, %s" % err)
        
    def _loadList(self):
        sql = "SELECT * FROM activity ORDER BY active desc,name"
        activities = self.localdb.select_all(sql)
        
        self.activities.clear()
        self.activities_id.clear()
        for activity in activities:
            self.activities.append(activity)
            self.activities_id[activity.server_id] = activity
        return

    def sync(self):
        """
        Sync the local database with the one on the server
        """
        self.toThreadQ.put("sync")

    def stop(self):
        if self.periodicsync_timer and self.periodicsync_timer.is_alive():
            self.periodicsync_timer.cancel()
        self.toThreadQ.put("quit")


    ##############################################################################
    #
    # Everything below is running in a different thread
    #
    ##############################################################################

    def _do_sync(self):
        """
        Runs as a separate thread
        """
        
        # Get list of all activities on server
        try:
            srv_activities, tmp = network.request("GET", "%s/api/activity" % sett.server_url, decode=True)
        except network.NetworkException as err:
            log.error("Cannot load list of activities from server %s" % err)
            return
#        print("srvactivities", srvactivities)
        
        for srv_activity in srv_activities:
            srv_activity = AttrDict(srv_activity)
            log.debug("Server activity %s" % srv_activity)
             
            sql = "SELECT * FROM activity WHERE server_id=?"
            local_activity = self.localdb.select_one(sql, (srv_activity["_id"],) )
            if local_activity:
                # we have the activity locally, check if changed
                changes = []
                for attr in ['name', "description", "active", "project_id"]:
                    if getattr(local_activity, attr) != getattr(srv_activity, attr):
                        changes.append(attr)
                if len(changes):
                    log.debugf(DEBUG_ACTIVITYMGR, "Updating local copy of activity, changed columns %s,  %s" % (changes, str(srv_activity).replace("\n", " ")))
                    local_activity.name = srv_activity["name"]
                    local_activity.server_id = srv_activity["_id"]
                    local_activity.active = srv_activity["active"]
                    try:
                        self.localdb.update("activity", d=local_activity, primary_key="_id")
                    except db.DbException as err:
                        log.error("Cannot update local activity %s" % err)
                        return
            else:
                # new activity
                log.debugf(DEBUG_ACTIVITYMGR, "New activity '%s' on server, saving in local database" % srv_activity.name)
                srv_activity.server_id = srv_activity._id
                srv_activity._id = -1
                try:
                    self.localdb.insert("activity", d=srv_activity, primary_key="_id")
                except db.DbException as err:
                    log.error("Cannot save new activity in local database %s" % err)
                    return

        self._loadList()
        self.sig.emit()
    
    
    def run(self):
        """
        Runs as a separate thread
        """
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
                self.localdb = util.openLocalDatabase2()

                self._do_sync()
            else:
                log.error("activitymgr thread, unknown command %s" % req)


if __name__ == '__main__':
    """Unit test"""
    import time
    from PyQt5.Qt import QApplication
    
    app = createQApplication()

    localdb = util.openLocalDatabase2(":memory:")
    
    activityMgr = ActivityMgr(localdb=localdb)
    activityMgr.init()
    activityMgr.sync()
    activityMgr.stop()

    while not activityMgr.toThreadQ.empty():
        QApplication.processEvents()
        time.sleep(0.5)

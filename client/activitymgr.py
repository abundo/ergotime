#!/usr/bin/env python3

"""
Manage activities

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
                log.debug(f"ActivityMgr starting autosync timer, interval {sett.activity_sync_interval}")
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
        log.debug(f"ActivityMgr interval {interval} jitter {jitter}")
        self.periodicsync_timer = threading.Timer(interval, self.periodic_sync)
        self.periodicsync_timer.daemon = True
        self.periodicsync_timer.setName("ActivityMgr.Timer")
        self.periodicsync_timer.start()

    def periodic_sync(self):
        log.debug("ActivityMgr.periodic_sync triggered")
        self.sync()
        self._start_periodicsync_timer()

    def init(self):
        """
        Load the list of activities from local db
        """
        self._loadList()
        self.sig.emit()

    def get(self, activityid):
        if activityid in self.activities_id:
            return self.activities_id[activityid]
        return None

    def getList(self):
        return self.activities

    def save(self):
        log.debugf(log.DEBUG_ACTIVITYMGR, "Saving activities")
        for activity in self.activities:
            log.debugf(log.DEBUG_ACTIVITYMGR, f"Storing activity {activity.name}")
            try:
                self.localdb.update("activity", d=activity, primary_key="_id")
            except db.DbException as err:
                log.error(f"Cant save activity in local database, {err}")

    def _loadList(self):
        sql = "SELECT * FROM activity ORDER BY active desc,name"
        activities = self.localdb.select_all(sql)

        self.activities.clear()
        self.activities_id.clear()
        for activity in activities:
            self.activities.append(activity)
            self.activities_id[activity.server_id] = activity

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
            r = requests.get(f"{sett.server_url}/api/activity")
            srv_activities = r.json()
            srv_activities = srv_activities["data"]
        except requests.exceptions.RequestException as err:
            log.error(f"Cannot load list of activities from server {err}")
            return

        for srv_activity in srv_activities:
            srv_activity = AttrDict(srv_activity)
            log.debug(f"Server activity {srv_activity}")

            sql = "SELECT * FROM activity WHERE server_id=?"
            local_activity = self.localdb.select_one(sql, (srv_activity["_id"],))
            if local_activity:
                # we have the activity locally, check if changed
                changes = []
                for attr in ["name", "description", "active"]:
                    if getattr(local_activity, attr) != getattr(srv_activity, attr):
                        changes.append(attr)
                if changes:
                    tmp = str(srv_activity).replace("\n", " ")
                    log.debugf(log.DEBUG_ACTIVITYMGR, f"Updating local copy of activity, changed columns {changes}, {tmp}")
                    local_activity.name = srv_activity["name"]
                    local_activity.server_id = srv_activity["_id"]
                    local_activity.active = srv_activity["active"]
                    try:
                        self.localdb.update("activity", d=local_activity, primary_key="_id")
                    except db.DbException as err:
                        log.error(f"Cannot update local activity {err}")
                        return
            else:
                # new activity
                log.debugf(log.DEBUG_ACTIVITYMGR, f"New activity '{srv_activity.name}' on server, saving in local database")
                srv_activity.server_id = srv_activity._id
                srv_activity._id = -1
                try:
                    self.localdb.insert("activity", d=srv_activity, primary_key="_id")
                except db.DbException as err:
                    log.error(f"Cannot save new activity in local database {err}")
                    return

        self._loadList()
        self.sig.emit()

    def run(self):
        """
        Runs as a separate thread
        """
        log.debugf(log.DEBUG_ACTIVITYMGR, "Starting activitymgr thread")

        while True:
            req = self.toThreadQ.get()
            log.debugf(log.DEBUG_ACTIVITYMGR, f"activitymgr, request={req}")
            if req == "quit":
                log.debugf(log.DEBUG_ACTIVITYMGR, "activitymgr thread stopping")
                return
            elif req == "sync":
                # connect to database, we have a separate connection in this thread to
                # simplify database operations
                self.localdb = util.openLocalDatabase2()
                self._do_sync()
            else:
                log.error(f"activitymgr thread, unknown command {req}")


if __name__ == "__main__":
    # Module test
    import time
    from PyQt5.Qt import QApplication

    app = util.createQApplication()

    localdb = util.openLocalDatabase2(":memory:")

    activityMgr = ActivityMgr(localdb=localdb)
    activityMgr.init()
    activityMgr.sync()
    activityMgr.stop()

    while not activityMgr.toThreadQ.empty():
        QApplication.processEvents()
        time.sleep(0.5)

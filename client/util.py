#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Database utilities
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


import os
import basium

from myglobals import *
from logger import log
from settings import sett

from common.activity import Activity
from common.report import Report
from common.users import Users


def openLocalDatabase():
    dbconf = basium.DbConf(database=localDatabaseName, log=log)
    log.debugf(DEBUG_FILES, "Opening local database %s" % (dbconf.database))
    db = basium.Basium(logger=log, driver="sqlite", checkTables=True, dbconf=dbconf)
    db.addClass(Activity)
    db.addClass(Report)
    db.addClass(Users)
    if not db.start():
        log.error("Cannot open local database, very limited functionality")
        return None, None   # todo exception
    return dbconf, db

def openRemoteDatabase(databaseName=None):
    dbconf = basium.DbConf(host=sett.server_url, database="ergotime", log=log) # username="", password=""
    log.debugf(DEBUG_FILES, "Opening remote database %s on %s" % (dbconf.database, dbconf.host))
    db = basium.Basium(logger=log, driver="json", checkTables=False, dbconf=dbconf)
    db.addClass(Activity)
    db.addClass(Report)
    db.addClass(Users)
    if not db.start():
        log.error("Cannot open ergotime database on remote server, sync aborted")
        return None, None   # todo exception
    return dbconf, db

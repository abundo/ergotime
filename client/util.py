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

from myglobals import *
from logger import log
from settings import sett

import db

def openLocalDatabase2(dbname=None):
    dbconf = { 'name': dbname }
    conn = db.Database(dbconf, driver="sqlite")
    conn.connect()

    sql  = "CREATE TABLE IF NOT EXISTS report ("
    sql += "  _id         INTEGER PRIMARY KEY, "
    sql += "  user_id     INT  NOT NULL default -1, "
    sql += "  activityid  INT  NOT NULL default -1, "
    sql += "  start       TIMESTAMP NOT NULL, "
    sql += "  stop        TIMESTAMP NOT NULL, "
    sql += "  comment     TEXT NOT NULL default '', "

    sql += "  modified    TIMESTAMP NOT NULL, "
    sql += "  seq         INT  NOT NULL default -1, "
    sql += "  deleted     INT  NOT NULL default  0, "

    sql += "  server_id   INT  NOT NULL default -1, "
    sql += "  updated     INT  NOT NULL default -1 "
    sql += ");"
    conn.execute(sql)
    
    sql  = "CREATE TABLE IF NOT EXISTS activity ("
    sql += "  _id         INTEGER PRIMARY KEY, "
    sql += "  name        TEXT NOT NULL default '', "
    sql += "  description TEXT NOT NULL default '', "
    sql += "  project_id  INT  NOT NULL default -1, "
    sql += "  active      INT  NOT NULL default  0, "
    sql += "  server_id   INT  NOT NULL default -1 "
    sql += ");"
    conn.execute(sql)
    
    sql  = "CREATE TABLE IF NOT EXISTS project ("
    sql += "  _id         INTEGER PRIMARY KEY, "
    sql += "  activity_id INT  NOT NULL default -1, "
    sql += "  name        TEXT NOT NULL default '', "
    sql += "  costcenter  TEXT NOT NULL default '', "
    sql += "  active      INT  NOT NULL default  0 "
    sql += ");"
    conn.execute(sql)

    return conn
    

if __name__ == '__main__':
    openLocalDatabase2("c:/temp/ergotime.db")

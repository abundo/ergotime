#!/usr/bin/env python3

"""
Database utilities

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

import sys

import PyQt5.QtWidgets as QtWidgets

from logger import log
from settings import sett
import resource

import lib.db as db


def createQApplication():
    app = QtWidgets.QApplication(sys.argv)

    app.setQuitOnLastWindowClosed(False)
    app.setOrganizationName("Abundo AB")
    app.setOrganizationDomain("abundo.se")
    app.setApplicationName("ErgoTime")
    return app


def openLocalDatabase2(dbname=None):
    dbconf = {"name": sett.localDatabaseName}
    conn = db.Database(dbconf, driver="sqlite")
    conn.connect()
    log.info(f"Open local database {dbconf}")

    sql = "CREATE TABLE IF NOT EXISTS report ("
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

    sql = "CREATE TABLE IF NOT EXISTS activity ("
    sql += "  _id         INTEGER PRIMARY KEY, "
    sql += "  name        TEXT NOT NULL default '', "
    sql += "  description TEXT NOT NULL default '', "
    sql += "  project_id  INT  NOT NULL default -1, "
    sql += "  active      INT  NOT NULL default  0, "
    sql += "  server_id   INT  NOT NULL default -1 "
    sql += ");"
    conn.execute(sql)

    sql = "CREATE TABLE IF NOT EXISTS project ("
    sql += "  _id         INTEGER PRIMARY KEY, "
    sql += "  activity_id INT  NOT NULL default -1, "
    sql += "  name        TEXT NOT NULL default '', "
    sql += "  costcenter  TEXT NOT NULL default '', "
    sql += "  active      INT  NOT NULL default  0 "
    sql += ");"
    conn.execute(sql)

    return conn


if __name__ == "__main__":
    openLocalDatabase2("c:/temp/ergotime.db")

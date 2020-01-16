#!/usr/bin/env python3

"""
HTTP REST API controller

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

import datetime
from orderedattrdict import AttrDict

from flask import request, jsonify, abort
from server import server

import lib.db as db

# ----------------------------------------------------------------------
#  Activities
# ----------------------------------------------------------------------


@server.route("/api/activity/<int:_id>")
@server.route("/api/activity")
def getActivity(_id=None):
    if _id:
        sql = "SELECT * FROM activity WHERE _id=%s"
        rows = db.conn.select_all(sql, (_id, ))
        if len(rows) > 0:
            return jsonify(rows[0])
        abort(404, {'message': 'Row with ID %s not found' % _id})
    else:
        sql = "SELECT * FROM activity"
        rows = db.conn.select_all(sql)
    return jsonify(data=rows)


@server.route("/api/activity", methods=["POST"])
def newActivity():
    abort(403, {'message': "Not implemented"})


@server.route("/api/activity/<int:_id>", methods=["PUT"])
def updateActivity(_id):
    abort(403, {'message': "Not implemented"})


@server.route("/api/activity/<int:_id>", methods=["DELETE"])
def deleteActivity(_id):
    abort(403, {'message': "Not implemented"})


# ----------------------------------------------------------------------
#  Reports
# ----------------------------------------------------------------------


@server.route("/api/report/sync/<int:seq>")
def syncReport(seq):
    maxage = request.args.get("maxage", None)
    limit = request.args.get("limit", None)
    offset = request.args.get("offset", None)
    sql = "SELECT * FROM report"
    where = []
    values = []
    where.append("seq > %s")
    values.append(seq)
    if maxage:
        now = datetime.datetime.now().replace(microsecond=0)
        modified = now - datetime.timedelta(days=int(maxage))
        where.append("modified > %s")
        values.append(modified)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY seq"
    if limit:
        sql += " LIMIT %s" % limit
    if offset:
        sql += " OFFSET %s" % offset
    print(sql, values)
    rows = db.conn.select_all(sql, values)
    return jsonify(data=rows)


@server.route("/api/report/<int:_id>")
@server.route("/api/report")
def getReport(_id=None):
    if _id:
        sql = "SELECT * FROM report WHERE _id=%s"
        row = db.conn.select_one(sql, (_id, ))
        if row:
            return jsonify(data=row)
        abort(404, {'message': 'Row with ID %s not found' % _id})
    else:
        sql = "SELECT * FROM report"
        rows = db.conn.select_all(sql)
    return jsonify(data=rows)


@server.route("/api/report", methods=["POST"])
def newReport():
    data = request.form
    data = AttrDict(data)
    for key in data.keys():
        print("key", key, "value", data[key])
    _id = db.conn.insert("report", d=data, primary_key="_id")
    return jsonify(_id=_id)


@server.route("/api/report/<int:_id>", methods=["PUT"])
def updateReport(_id):
    data = request.form
    data = AttrDict(data)
    for key in data.keys():
        print("key", key, "value", data[key])
    _id = db.conn.update("report", d=data, primary_key="_id")
    return jsonify(id=_id)


@server.route("/api/report/<int:_id>", methods=["DELETE"])
def deleteReport(_id):
    """
    We will never delete reports, they are just marked for removal
    and can be reused later on when new reports are created
    """
    abort(403, {'message': "Not implemented"})


# ----------------------------------------------------------------------
#  Users
# ----------------------------------------------------------------------


@server.route("/api/user/<_id>")
@server.route("/api/user")
def getUser(_id=None):
    print("getUser")
    if _id:
        sql = "SELECT * FROM users WHERE _id=%s"
        rows = db.conn.select_all(sql, (_id, ))
        if len(rows) > 0:
            return jsonify(rows[0])
        abort(404, {'message': 'Row with ID %s not found' % _id})
    else:
        sql = "SELECT * FROM users"
        rows = db.conn.select_all(sql)
    return jsonify(data=rows)


@server.route("/api/user", methods=["POST"])
def newUser():
    print("saveUser")
    t = {}
    d = request.form
    for key in d.keys():
        t[key] = d[key]
    print("t", t)
    _id = db.conn.insert("users", t, "_id")
    return jsonify(_id=_id)


@server.route("/api/user", methods=["PUT"])
def updateUser():
    abort(403, {'message': "Not implemented"})


@server.route("/api/user", methods=["DELETE"])
def deleteUser():
    abort(403, {'message': "Not implemented"})


if __name__ == "__main__":
    server.run(debug=True, host="0.0.0.0")

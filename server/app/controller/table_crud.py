#!/usr/bin/env python3

"""
SQL Table CRUD controller

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

from flask import render_template, jsonify, request
from server import server

import json
from orderedattrdict import AttrDict

import lib.util as util     # read config file
import lib.log as log
import lib.db as db

db.conn = db.Database(config["db_conf"], driver="psql")

table_defs = util.yaml_load("%s/table_crud.yaml" % config["etcdir"])


def set_error(res, message):
    log.debug("set_error(%s, %s)" % (res, message))
    res.status = 'error'
    res.message = message


@server.route("/table/crud/<table>", methods=['POST'])
def table_crud_api(table):
    """
    AJAX API for the data grid
    This API is for INTERNAL use and can change anytime
    todo, only allow request from localhost
    """
    try:
        table_def = table_defs[table]
    except ValueError:
        return "No such table %s\n" % table, 403
    primary_key = table_def.primary_key

    data = AttrDict(request.json)
    cmd = data.cmd
    res = AttrDict()
    # print("data", data)

    if cmd == "get-record":
        # get form data
        print("get-record", data)
        if int(data.recid) > 0:
            rows = None
            sql = "SELECT * FROM %s where %s=%%s" % (table, primary_key)
            values = (data.recid, )
            # print(sql, values)
            try:
                row = db.conn.select_one(sql, values)
            except db.conn.dbexception as e:
                set_error(res, e)

            if row is not None:
                res.status = "success"
                res.record = row
            else:
                set_error(res, "No record with id %s" % data.recid)

    elif cmd == "get-records":
        # get list of rows
        print("get-records", data)
        rows = None
        sql = "SELECT * FROM %s" % table
        limit, offset = None, None
        where = []
        values = []

        if 'offset' in data:
            offset = int(data.offset)
        if 'limit' in data:
            limit = int(data.limit)
        if "search" in data:
            for search in data.search:
                where.append("%s=%%s" % search.field)
                values.append(search.value)
            sql += " WHERE " + " OR ".join(where)
        if 'sort' in data:
            sql += " ORDER by "
            addComma = False
            for field in data.sort:
                if addComma:
                    sql += ", "
                addComma = True
                sql += "%s %s" % (field["field"], field["direction"])

        if limit is not None:
            sql += " limit %s" % limit
            if offset:
                sql += " offset %s" % offset

        try:
            rows = db.conn.select_all(sql, values)
        except db.conn.dbexception as e:
            set_error(res, e)

        if rows is not None:
            res.status = "success"
            res.total = len(rows)

            records = []
            for row in rows:
                record = {}
                for col in row:
                    record[col] = row[col]
                records.append(record)
            res.records = records

            # get total number of rows
            sql = "select count(*) from %s" % table
            res.total = db.conn.count(sql)
            
    elif cmd == "save-record":
        # save form data
        print("save-record", data)

        # convert string to valid python/sql type
        d = AttrDict(data.record.items())
        for col in table_def.columns:
            if col.name == primary_key:
                continue
            if col.type == "checkbox":
                d[col.name] = d[col.name] in ["true", "True", "1", "T", "t", "y", "y", "yes", 1]

        if int(data.recid) > 0:
            # UPDATE
            d[primary_key] = data.recid
            try:
                db.conn.update(table=table, d=d, primary_key=primary_key)
                res.status = 'success'
            except Exception as err:
                set_error(res, str(err))
        else:
            # INSERT
            # if a value is not included or empty, and there is a default, use default
            for col in table_def.columns:
                if "default" in col:
                    if col.name not in d or d[col.name] == "":
                        d[col.name] = col.default
            try:
                db.conn.insert(table=table, d=d, primary_key=primary_key)
                res.status = 'success'
            except Exception as e:
                set_error(res, str(e))

    elif cmd == "save-records":
        # save all changes from datagrid, can be multiple rows
        print("save-records", data)
        for values in data.changes:
            values[primary_key] = values.pop("recid")
            try:
                db.conn.update(table=table, d=values, primary_key=primary_key)
                res.status = 'success'
            except db.conn.dbexception as e:
                set_error(res, str(e))
                break

    elif cmd == "delete-records":
        # print("delete-records", data)
        for selected in data.selected:
            try:
                sql = "DELETE FROM %s WHERE %s=%%s" % (table, primary_key)
                db.conn.delete(sql, (selected,))
                res.status = 'success'
            except db.conn.dbexception as e:
                set_error(res, str(e))

    else:
        set_error(res, "Unknown cmd from w2ui grid %s" % cmd)
    return jsonify(res)


class Datagrid:
    """
    Manage a w2ui grid, with edit controls
    """
    def __init__(self, name=None, htmldiv=None, table=None):
        self.name = name
        self.htmldiv = htmldiv
        self.table = table

    jsgrid = """
    w2utils.settings['dataType'] = 'JSON';
    $$('#${name}').w2grid({
        name: '${name}',
        url: dataj['url'] + dataj['params'],
        show: {
            toolbar: true,
            footer: true,
            toolbarAdd: true,
            toolbarDelete: true,
            toolbarSave: true,
            toolbarEdit: true
        },
        multiSelect: false,
        recid: dataj['primary_key'],
        header: 'Table ' + dataj['table'],
        onAdd: function (event) {
            addEditPopup(-1);
        },
        onEdit: function (event) {
            addEditPopup(this.last.sel_recid, this.records);
            w2ui['grid'].reload();
        },
        onDelete: function (event) {
            console.log('delete has default behaviour');
        },
        searches: [
// { { data['searches'] | safe }}
        ],
        sortData: [
// { { data['sortdata'] | safe }}
        ],
        columns: [
// { { data['coltxt'] | safe }}
        ],
    });
"""

    def api(self):
        """
        API for datagrid
        """

    def render_js(self):
        """Output the needed javascript code"""
        from string import Template
        d = dict(name=self.name)
        t = Template(self.jsgrid)
        s = t.substitute(d)
        return s



@server.route('/table/<table>')
def table_crud(table):
    """
    Show datagrid for requested table
    """
    data = AttrDict()
    data.params = ""
    old_net = request.args.get("old_net", None)
    if old_net is not None:
        data.params = "?old_net=1"

    if table not in table_defs:
        return "Table %s is not available" % table

    datagrid = Datagrid(name="grid1", htmldiv="grid1", table=table)

    table_def = table_defs[table]
    columns = table_def.columns
    sortdata = table_def.sortdata

    data.primary_key = table_def.primary_key

    data.title = table_def.title
    data.table = table

    data.url = "/table/crud/%s" % table

    data.columns = []
    for column in table_def.columns:
        name = column.name
        col = AttrDict()
        col.field = name
        col.caption = column.title
        col.size = "30%"
        col.sortable = True
        col.type = column.type
        data.columns.append(col)

    data.sortdata = []
    data.sortdata.append({'field': sortdata[0]['name'],
                          'direction': sortdata[0]['direction']})

    return render_template('table_crud.html',
                           columns=columns,
                           data=data,
                           datajson=json.dumps(data),
                           datagrid=datagrid)

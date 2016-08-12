#!/bin/env python3

from flask import render_template, jsonify, request
from server import server

import json
import yaml
import psycopg2

import lib.util as util
import lib.log as log
import lib.db as db

with open("%s/table_crud.yaml" % config["etcdir"], "r") as f:
    table_defs = yaml.load(f)

def set_error(res, message):
    res['status'] = 'error'
    res['message'] = message

# ------------------------------------------------------------
#   AJAX API for the data grid
#   This API is for INTERNAL use and can change anytime
#   todo, only allow request from localhost
# ------------------------------------------------------------

@server.route("/table/crud/<table>", methods=['POST'])
def table_crud_api(table):
    
    try:
        table_def = table_defs[table]
    except ValueError:
        return "No such table %s\n" % table, 403
    primary_key = table_def["primary_key"]
        
    old_net = request.args.get("old_net", None)
    if old_net:
        table = "lunet." + table

    data = request.json
    
    cmd = data['cmd']
    res = {}
#    print("data", data)

    if cmd == "get-record":
        # get form data
        # print("get-record", data)
        if int(data['recid']) > 0:
            rows = None
            sql = "SELECT * FROM %s where %s=%%s" % (table, primary_key)
            values = (data['recid'], )
            # print(sql, values)
            try:
                rows = db.conn.select_all(sql, values)
            except psycopg2.Error as e:
                set_error(res, e)
    
            if rows is not None:
                res["status"] = "success"
                
                row = rows[0]
                record = {}
                for col in row:
                    record[col] = row[col] 
                res["record"] = record
            else:
                set_error(res, "No record with id %s" % data['recid'])
        
    elif cmd == "save-record":
        # save form data
        print("save-record", data)
        values = []
        if int(data['recid']) > 0:
            sql = "UPDATE %s SET " % table
            for colname, value in data["record"].items():
                if colname != primary_key:
                    if len(values):
                        sql += ", "
                    sql += "%s=%%s" % colname
                    values.append(value) 
            sql += " WHERE %s = %%s" % primary_key
            values.append(data['recid'])
        else:
            sql = "INSERT INTO %s " % table
            s = []
            v = []
            for colname, value in data['record'].items():
                if colname != primary_key:
                    s.append(colname)
                    v.append("%s")
                    values.append(value)
                else:
                    id_value = value
                    
            sql += "(" + ",".join(s) + ") "
            sql += " VALUES (%s)" % ",".join(v)

        print("  sql    ;", sql)
        print("  values :", values)
        try:
            db.conn.execute(sql, values)
            res['status'] = 'success'
        except Exception as e:
            set_error(res, str(e))
            

    elif cmd == "get-records":
        # get list of rows
        rows = None
        sql = "SELECT * FROM %s" % table
        limit, offset = None, None
        where = []
        values = []
        
        if 'offset' in data:
            offset = int(data["offset"])
        if 'limit' in data:
            limit = int(data['limit'])
        if "search" in data:
            for search in data['search']:
                where.append("%s=%%s" % search['field'])
                values.append(search['value'])
            sql += " WHERE " + " OR ".join(where)
        if 'sort' in data:
            sql += " ORDER by "
            addComma = False
            for field in data['sort']:
                if addComma:
                    sql += ", "
                addComma = True
#                 if field['field'] == "recid":
#                     sql += "_id %s" % (field['direction'])
#                 else:
                sql += "%s %s" % (field['field'], field['direction'])

        if limit is not None:
            sql += " limit %s" % limit
            if offset:
                sql += " offset %s" % offset
                
        # print(sql, values)
        try:
            rows = db.conn.execute(sql, values)
        except psycopg2.Error as e:
            set_error(res, e)

        if rows is not None:
            res["status"] = "success"
            res["total"] = len(rows)
            
            records = []
            for row in rows:
                record = {}
                for col in row:
                    record[col] = row[col] 
                records.append(record)
            res["records"] = records
            
            # get total number of rows
            sql = "select count(*) from %s" % table
            if len(where):
                sql += " WHERE " + " OR ".join(where)
            # print(sql, values)
            rows = db.conn.execute(sql, values)
            # print("rows", rows)
            
            # mysql
            #res["total"] = rows[0]['count(*)']
            
            # psql
            res["total"] = rows[0]['count']

    elif cmd == "save-records":
        # save all changes from datagrid, can be multiple rows
        print("save-records", data)
        for tmp in data['changes']:
            sql = "UPDATE %s SET " % table
            values = []
            for colname, value in tmp.items():
                name = colname
                if name == "recid": 
                    name = primary_key # todo, primary key
                    primary_key_value = value
                else:
                    if len(values):
                        sql += ", "
                    sql += "%s=%%s" % name
                    values.append(value)
            sql += " WHERE %s = %%s" % primary_key
            values.append(primary_key_value)
            print("  sql    ;", sql)
            print("  values :", values)
            try:
                db.conn.execute(sql, values, fetchall=False)
                res['status'] = 'success'
                print("success")
            except psycopg2.Error as e:
                print("error", e)
                set_error(res, str(e))
                return jsonify(res)
            

    elif cmd == "delete-records":
        # print("delete-records", data)
        for selected in data["selected"]:
            sql = "DELETE FROM %s WHERE %s=%%s" % (table, primary_key)
            try:
                db.conn.execute(sql, (selected, ))
                res['status'] = 'success'
            except psycopg2.Error as e:
                set_error(res, str(e))
            
    else:
        print("Unknown cmd", cmd)
    return jsonify(res)


class Datagrid:
    """
    Manage a w2ui grid, with edit controls
    """
    def __init__(self, name=None, htmldiv=None, table=None):
        self.name = name
        self.htmldiv = htmldiv
        self.table = table

    jsgrid="""
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
        """API for datagrid"""

    def render_js(self):
        """Output the needed javascript code"""
        from string import Template
        d = dict(name=self.name)
        t = Template(self.jsgrid)
        s = t.substitute(d)
        return s

# ------------------------------------------------------------
#   Show datagrid for requested table
# ------------------------------------------------------------

@server.route('/table/<table>')
def table_crud(table):
    data = {}
    data["params"] = ""
    old_net = request.args.get("old_net", None)
    if old_net is not None:
        data["params"] = "?old_net=1"
           
    if table not in table_defs:
        return "Table %s is not available" % table

    datagrid = Datagrid(name="grid1", htmldiv="grid1", table=table)

    table_def = table_defs[table]
    columns = table_def['columns']
    sortdata = table_def['sortdata']

    data['primary_key'] = table_def['primary_key']
    
    data['title'] = table_def['title']
    data['table'] = table
    
    data['url'] = "/table/crud/" + table

    data['columns'] = []
    for column in columns:
        name = column['name']
        col = {}
        col['field'] = name 
        col['caption'] = column['title'] 
        col['size'] = "30%" 
        col['sortable'] = True
        col['type'] = column['type']
        data['columns'].append(col)
         
    data['sortdata'] = []
    data['sortdata'].append( { 'field': sortdata[0]['name'], 
                               'direction': sortdata[0]['direction'] } )
        
    return render_template('table_crud.html', columns=columns,\
                           data = data, datajson=json.dumps(data), 
                           datagrid=datagrid)

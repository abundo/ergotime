#!/usr/bin/env python3

"""
Database management

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

from orderedattrdict import AttrDict


class DbException(Exception):
    pass


class Database:
    """
    Handle database connections

    Keep the connection open, and if any error try to reconnect
    before returning any errors
    """
    def __init__(self, db_conf, driver=None):
        self.db_conf = db_conf
        if "driver" in self.db_conf:
            self.driver = self.db_conf["driver"]
        else:
            self.driver = driver

        self.conn = None
        self.cursor = None
        self.dbexception = DbException

        if self.driver not in ["psql", "mysql", "sqlite"]:
            raise ValueError("Driver type '%s' not implemented" % self.driver)

        self.valueholder = "%s"
        if self.driver == "sqlite":
            self.valueholder = "?"

    def connect(self):
        if self.conn:
            return self.conn

        if self.driver == "psql":
            import psycopg2
            import psycopg2.extras
            self.dbexception = psycopg2.Error

            self.conn = psycopg2.connect(
                host=self.db_conf["host"],
                user=self.db_conf["user"],
                password=self.db_conf["pass"],
                database=self.db_conf["name"])
            self.conn.autocommit = False

            # return querys as dictionaries
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        elif self.driver == "mysql":
            import pymysql
            import pymysql.cursors
            self.dbexception = pymysql.MySQLError

            self.conn = pymysql.connect(
                host=self.db_conf["host"],
                user=self.db_conf["user"],
                passwd=self.db_conf["pass"],
                db=self.db_conf["name"],
                cursorclass=pymysql.cursors.DictCursor)
            self.cursor = self.conn.cursor()

        elif self.driver == "sqlite":
            import sqlite3
            self.dbexception = sqlite3.Error

            self.conn = sqlite3.connect(self.db_conf["name"],
                                        check_same_thread=False,
                                        detect_types=sqlite3.PARSE_DECLTYPES)
            self.conn.row_factory = sqlite3.Row   # return querys as dictionaries
            self.cursor = self.conn.cursor()

        return self.conn

    def disconnect(self):
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.conn:
            self.conn.close()
        self.conn = None

    def begin(self):
        for i in range(0, 2):
            self.connect()
            try:
                self.conn.begin()
                return
            except self.dbexception as err:
                if i == 1:
                    raise DbException(str(err))
            self.disconnect()

    def commit(self):
        """
        We don't retry commit, if the connection is gone there are
        no transaction to commit
        """
        self.conn.commit()

    def rollback(self):
        """
        We don't retry rollback, if the connection is gone there are
        no transaction to rollback
        """
        self.conn.rollback()

    def execute(self, sql, values=None):
        """
        Execute a query,
        if error try to reconnect and redo the query to handle timeouts, connection issues
        """
        # print("execute", "\n    sql   :", sql, "\n    values:", values)
        for i in range(0, 2):
            self.connect()
            try:
                if values:
                    self.cursor.execute(sql, values)
                else:
                    self.cursor.execute(sql)
                return
            except self.dbexception as err:
                if i < 2:
                    raise DbException(str(err))
                self.disconnect()

    def last_insert_id(self):
        key = "LAST_INSERT_ID()"
        rows = self.execute(key)
        if rows:
            row = rows[0]
            if key in row:
                return row[key]
        return None

    def count(self, sql, values=None, commit=True):
        self.execute(sql, values)
        row = self.cursor.fetchone()
        if commit:
            self.commit()
        if row:
            if self.driver == "mysql":
                return row["count(*)"]
            elif self.driver == "psql":
                return row["count"]
            elif self.driver == "sqlite":
                return row[0]
        return None

    def insert(self, table=None, d=None, primary_key="_id", exclude=None, commit=True):
        """
        Insert a row in a table, using table name and a dict
        Primary is the key, which should be updated with last_inserted_id
        exclude are columns that should be ignored
        """
        if exclude is None:
            exclude = []
        exclude.append(primary_key)  # we always exclude the primary_key
        columns = []
        values = []
        for colname in set(d.keys()) - set(exclude):
            columns.append(colname)
            values.append(d[colname])
        sql = "INSERT into %s (%s) VALUES (%s)" %\
            (table,
             ",".join(columns),
             ",".join([self.valueholder] * len(values)))
        if primary_key and self.driver == "psql":
            sql += " RETURNING %s" % primary_key

        self.execute(sql, values)
        if self.driver == "mysql":
            id_ = self.last_insert_id()
        elif self.driver == "psql":
            res = self.cursor.fetchone()
            id_ = res[primary_key]
        elif self.driver == "sqlite":
            id_ = self.cursor.lastrowid
        if commit:
            self.commit()
        d[primary_key] = id_
        return id_

    def update(self, table=None, d=None, primary_key="_id", exclude=None, commit=True):
        """
        Update a row in a table, using table name and a dict
        Primary is the key, which should be updated with last_inserted_id
        exclude are columns that should be ignored
        """
        if exclude is None:
            exclude = []
        if primary_key:
            exclude.append(primary_key)  # we always exclude the primary_key
        columns = []
        values = []
        for colname in set(d.keys()) - set(exclude):
            columns.append(colname)
            values.append(d[colname])
        fstr = "{!s}=%s" % self.valueholder
        sql = "UPDATE %s SET %s" %\
            (table, ",".join(fstr.format(colname) for colname in columns))
        sql += " WHERE %s=%s" % (primary_key, self.valueholder)
        values.append(d[primary_key])
        self.execute(sql, values)
        if commit:
            self.commit()

    def delete(self, sql=None, values=None, commit=True):
        self.execute(sql, values)
        if commit:
            self.commit()
        if self.driver == "mysql":
            pass
        elif self.driver == "psql":
            pass
        elif self.driver == "sqlite":
            return self.cursor.rowcount
        return 0

    def select_one(self, sql=None, values=None, commit=True):
        """
        Returns a dict, or None if not found
        """
        self.execute(sql, values)
        row = self.cursor.fetchone()
        if commit:
            self.commit()
        if row:
            row = AttrDict(row)
        return row

    def select_all(self, sql=None, values=None, commit=True):
        """
        Returns a list of dicts
        """
        self.execute(sql, values)
        rows = self.cursor.fetchall()
        if commit:
            self.commit()
        for ix, row in enumerate(rows):
            rows[ix] = AttrDict(row)
        return rows


conn = None

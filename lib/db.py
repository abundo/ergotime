#!/usr/bin/env python3
"""
Database management
"""

import psycopg2
import psycopg2.extras
from orderedattrdict import AttrDict


class DbException(Exception):
    pass


class DB_connect:
    """
    Handle database connections
    
    Keep the connection open, and if any error try to reconnect
    before returning any errors
    """
    
    exception = DbException
    
    def __init__(self, db_conf):
        self.db_conf = db_conf
        self.conn = None
        self.cursor = None
        
    def connect(self):
        if self.conn:
            return self.conn
        if 1:
            self.conn = psycopg2.connect(
                    host=self.db_conf['host'], 
                    user=self.db_conf['user'], 
                    password=self.db_conf['pass'],
                    database=self.db_conf['name'])
            self.conn.autocommit = False
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            self.conn = pymysql.connect(
                    host=self.db_conf['host'], 
                    user=self.db_conf['user'], 
                    passwd=self.db_conf['pass'],
                    db=self.db_conf['name'],
                    cursorclass=pymysql.cursors.DictCursor)
            self.cursor = self.conn.cursor()
        return self.conn
    
    def disconnect(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.conn = None
    
    def begin(self):
        for i in range(0, 2):
            self.connect()
            try:
                self.conn.begin()
                return
            except pymysql.MySQLError as e:
                if i == 1:
                    raise 
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

    def execute(self, sql, values=None, commit=True, fetchall=True):
        """
        Execute a query,
        if error try to reconnect and redo the query to handle timeouts
        """
        for i in range(0, 2):
            self.connect()
            try:
                if values is not None:
                    self.cursor.execute(sql, values)
                else:
                    self.cursor.execute(sql)
                if fetchall:
                    rows = self.cursor.fetchall()
                if commit:
                    self.conn.commit()
                if fetchall:
                    return rows
                return
            # except pymysql.MySQLError as e:
            except psycopg2.Error as e:
                if i < 2:
                    raise 
                self.disconnect()
    
    def last_insert_id(self):
        key = "LAST_INSERT_ID()"
        rows = self.execute(key, commit=False, fetchall=False)
        if len(rows):
            row = rows[0]
            if key in row:
                return row[key]
        return None
    
    def row_count(self):
        key = "ROW_COUNT()"
        rows = self.execute(key, commit=False, fetchall=False)
        if len(rows):
            row = rows[0]
            if key in row:
                return row[key]
        return None

    def insert(self, table=None, d=None, primary_key=None, exclude=[], commit=True):
        """
        Insert a row in a table, using table name and a dict
        Primary is the key, which should be updated with last_inserted_id
        exclude are columns that should be ignored
        """
        exclude.append(primary_key)  # we always exclude the primary_key
        columns = []
        values = []
        for colname in set(d.keys()) - set(exclude):
            columns.append(colname)
            values.append(d[colname])
        sql = "INSERT into %s (%s) VALUES (%s)" %\
            (table, ",".join(columns), ",".join(["%s"] * len(values) ) )
        if primary_key:
            sql += " RETURNING %s" % primary_key
        print("sql", sql)
        print("values", values)
        
        self.execute(sql, values, commit=False, fetchall=False)
        if 0:
            id_ = self.last_insert_id()
        if 1:
            res = self.cursor.fetchone()
            id_ = res[primary_key]
        if commit:
            self.commit()
        d[primary_key] = id_
        return id_

    def update(self, table=None, d=None, primary_key=None, exclude=[], commit=True):
        """
        Update a row in a table, using table name and a dict
        Primary is the key, which should be updated with last_inserted_id
        exclude are columns that should be ignored
        """
        if primary_key:
            exclude.append(primary_key)  # we always exclude the primary_key
        columns = []
        values = []
        for colname in set(d.keys()) - set(exclude):
            columns.append(colname)
            values.append(d[colname])
        sql = "UPDATE %s SET %s" %\
            (table, ",".join("{!s}=%s".format(colname) for colname in columns))
        sql += " WHERE %s=%%s" % primary_key
        values.append(d[primary_key])
        self.execute(sql, values, commit=False, fetchall=False)

        if commit:
            self.commit()

    def delete(self, sql=None, values=None, commit=True):
        self.execute(sql, values, commit=False, fetchall=False)
        if commit:
            self.commit()
        
    def select_one(self, sql=None, values=None):
        """
        Returns an OrderedAttrDict, or None if not found
        """
        self.execute(sql, values, commit=False, fetchall=False)
        row = self.cursor.fetchone()
        if row is not None:
            row = AttrDict(row)
        return row

    def select_all(self, sql=None, values=None):
        """
        Returns a list of OrdererdAttrDict
        """
        self.execute(sql, values, commit=False, fetchall=False)
        rows = self.cursor.fetchall()
        for ix in range(0, len(rows)):
            rows[ix] = AttrDict(rows[ix])
        return rows



import sys, yaml
with open("/etc/ergotime/ergotime.yaml", "r") as f:
    try:
        config = yaml.load(f)
    except yaml.YAMLError as err:
        print("Cannot load config, err: %s" % err)
        sys.exit(1)

# todo config from flask app.config?
conn = DB_connect(config['db_conf'])

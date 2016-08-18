#!/usr/bin/env python3

"""
Database management
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

        if not self.driver in ["psql", "mysql", "sqlite"]: 
            raise ValueError("Driver type '%s' not implemented" % self.driver)
        if not driver in ["psql", "mysql", "sqlite"]: 
            raise ValueError("Driver type not implemented (%s)" % self.driver)
        

    def connect(self):
        if self.conn:
            return self.conn

        if self.driver == "psql":
            import psycopg2
            import psycopg2.extras
            self.dbexception = psycopg2.Error
            
            self.conn = psycopg2.connect(
                    host=self.db_conf['host'], 
                    user=self.db_conf['user'], 
                    password=self.db_conf['pass'],
                    database=self.db_conf['name'])
            self.conn.autocommit = False
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) # return querys as dictionaries
            
        elif self.driver == "mysql":
            import pymysql
            import pymysql.cursors
            self.dbexception = pymysql.MySQLError
            
            self.conn = pymysql.connect(
                    host=self.db_conf['host'], 
                    user=self.db_conf['user'], 
                    passwd=self.db_conf['pass'],
                    db=self.db_conf['name'],
                    cursorclass=pymysql.cursors.DictCursor)
            self.cursor = self.conn.cursor()

        elif self.driver == "sqlite":
            import sqlite3
            self.dbexception = sqlite3.Error
            
            self.conn = sqlite3.connect(self.db_conf["name"],  check_same_thread=False, detect_types=sqlite3.PARSE_DECLTYPES)
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
            except self.dbexception as e:
                if i == 1:
                    raise DbException(str(e))
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

    def execute(self, sql, values=None, commit=True):
        """
        Execute a query,
        if error try to reconnect and redo the query to handle timeouts
        """
        # print("execute", "\n    sql   :", sql, "\n    values:", values)
        for i in range(0, 2):
            self.connect()
            try:
                if values is not None:
                    self.cursor.execute(sql, values)
                else:
                    self.cursor.execute(sql)
                if commit:
                    self.conn.commit()
                return
            # except pymysql.MySQLError as e:
#            except psycopg2.Error as e:
            except self.dbexception as e:
                if i < 2:
                    raise DbException(str(e))
                self.disconnect()
    
    def last_insert_id(self):
        key = "LAST_INSERT_ID()"
        rows = self.execute(key, commit=False)
        if len(rows):
            row = rows[0]
            if key in row:
                return row[key]
        return None
    
    def count(self, sql, commit=True):
        key = "ROW_COUNT()"
        rows = self.execute(key, commit=False)
        if commit:
            self.commit()
        if len(rows):
            row = rows[0]
            if key in row:
                return row[key]
        return None

    def insert(self, table=None, d=None, primary_key="_id", exclude=[], commit=True):
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
            (table, ",".join(columns), ",".join(["?"] * len(values) ) )
        if primary_key and self.driver == "psql":
            sql += " RETURNING %s" % primary_key
        print("sql", sql)
        print("values", values)
        
        self.execute(sql, values, commit=False)
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

    def update(self, table=None, d=None, primary_key="_id", exclude=[], commit=True):
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
            (table, ",".join("{!s}=?".format(colname) for colname in columns))
        sql += " WHERE %s=?" % primary_key
        values.append(d[primary_key])
        self.execute(sql, values, commit=commit)

    def delete(self, sql=None, values=None, commit=True):
        self.execute(sql, values, commit=commit)
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
        self.execute(sql, values, commit=False)
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
        self.execute(sql, values, commit=False)
        rows = self.cursor.fetchall()
        if commit:
            self.commit()
        for ix in range(0, len(rows)):
            rows[ix] = AttrDict(rows[ix])
        return rows

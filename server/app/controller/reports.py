#!/usr/bin/env python3

"""
Reports Controller

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

from flask import render_template, request
from server import server

import datetime
from orderedattrdict import AttrDict

import lib.log as log
import lib.util as util     # read settings
import lib.db as db2
import lib.htmllib

db2.conn = db2.Database(config["db_conf"])

htmllib = lib.htmllib.Htmllib(db2.conn)

dateformat = '%Y-%m-%d'
datetimeformat = dateformat + ' %H:%M:%S'

errors = []


def strTimedeltaHM(td, includeDecimal=False):
    """
    Convert a timedelta to hours and minutes
    """
    seconds = td.total_seconds()
    hours = seconds / 3600
    minutes = (seconds / 60) % 60
    res = "%02i:%02i" % (hours, minutes)
    if includeDecimal:
        res += "\n(%i.%02i)" % (hours, minutes * 100 / 60)
    return res


class MyDateTime:

    def __init__(self, *args, **kwargs):
        if len(args) == 0 and len(kwargs) == 0:
            self.obj = datetime.datetime.now()
        else:
            self.obj = datetime.datetime(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.obj, name)

    def __str__(self):
        return self.obj.strftime(datetimeformat)

    def copy(self):
        tmp = MyDateTime()
        tmp.obj = self.obj.replace(second=self.obj.second)
        return tmp

    @property
    def year(self):
        return self.obj.year

    @year.setter
    def year(self, value):
        self.obj = self.obj.replace(year=value)

    @property
    def month(self):
        return self.obj.month

    @month.setter
    def month(self, value):
        self.obj = self.obj.replace(month=value)

    @property
    def day(self):
        return self.obj.day

    @day.setter
    def day(self, value):
        self.obj = self.obj.replace(day=value)

    def setFromStr(self, s):
        self.obj = datetime.datetime.strptime(s, datetimeformat)

    def strToDatetime(self, s):
        return self.obj.strptime(s, datetimeformat)

    def strYMD(self):
        return self.obj.strftime(dateformat)

    def strYM(self):
        return self.obj.strftime('%Y-%m')

    def firstDayInMonth(self, offset=0):
        y = self.obj.year
        m = self.obj.month
        if offset > 0:
            while offset:
                offset -= 1
                m += 1
                if m > 12:
                    m = 1
                    y += 1
        else:
            while offset:
                offset += 1
                m -= 1
                if m < 1:
                    m = 12
                    y -= 1

        return datetime.datetime(y, m, 1)

    def strFirstDayInMonth(self, offset=0):
        return self.firstDayInMonth(offset).strftime(dateformat)

    def lastDayInMonth(self, offset=0):
        y = self.obj.year
        m = self.obj.month
        offset += 1     # we go one month extra, then back one day
        if offset > 0:
            while offset:
                offset -= 1
                m += 1
                if m > 12:
                    m = 1
                    y += 1
        else:
            while offset:
                offset += 1
                m -= 1
                if m < 1:
                    m = 12
                    y -= 1
        return datetime.datetime(y, m, 1) - datetime.timedelta(days=1)

    def strLastDayInMonth(self, offset=0):
        return self.lastDayInMonth(offset).strftime(dateformat)

    def setFirstDayInMonth(self, offset):
        self.day = 1
        self.obj = self.firstDayInMonth(offset)

    def setLastDayInMonth(self, offset):
        self.obj = self.lastDayInMonth(offset)

    def addTime(self, days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
        self.obj = self.obj + datetime.timedelta(days, seconds, microseconds, milliseconds, minutes, hours, weeks)


class ReportRes:
    def __init__(self, start, stop, comment):
        self.start = start
        self.stop = stop
        self.length = stop - start
        self.comment = comment.strip()

    def strLength(self):
        return strTimedeltaHM(self.length)


class ActivityDay:
    def __init__(self, date):
        self.date = date

        self.total = datetime.timedelta()
        self.reports = []

    def addReport(self, report):
        self.reports.append(report)
        self.total += report.length

    def strTotal(self, includeDecimal=False):
        return strTimedeltaHM(self.total, includeDecimal=includeDecimal)

    # go through all reports, return dict with values
    # If non-first entry, return empty date
    def iterReport(self):
        for report in self.reports:
            yield report


class ActivityMonth:
    def __init__(self, periodStart, periodStop, description=None):
        self.periodStart = periodStart
        self.periodStop = periodStop
        self.description = description

        self.days = []
        self.total = datetime.timedelta()

    def addDay(self, day):
        self.days.append(day)
        self.total += day.total

    def strTotal(self, includeDecimal=False):
        return strTimedeltaHM(self.total, includeDecimal=includeDecimal)


class Activities:
    def __init__(self):
        self.activityMonth = []         # array of ActivityMonth()
        self.total = datetime.timedelta()

    def addActivity(self, activity):
        self.activityMonth.append(activity)
        self.total += activity.total

    def strTotal(self):
        return strTimedeltaHM(self.total)


def sectotime(sec):
    return "%02i:%02i" % (sec / 3600, (sec / 60) % 60)


def sectotime_sec(sec):
    return "%02i:%02i:%02i" % (sec / 3600, (sec / 60) % 60, sec % 60)


def strToDatetime(s):
    return datetime.datetime.strptime(s, datetimeformat)


def datetimeToStr(d):
    return d.strftime(datetimeformat)


def datetimeToDateStr(d):
    return d.strftime(dateformat)


def datetimeToYearMonth(d):
    return d.strftime('%Y-%m')


def getFirstDayInMonth(d, offset=0):
    y = d.year
    m = d.month
    if offset > 0:
        while offset:
            offset -= 1
            m += 1
            if m > 12:
                m = 1
                y += 1
    else:
        while offset:
            offset += 1
            m -= 1
            if m < 1:
                m = 12
                y -= 1

    return datetime.datetime(y, m, 1).strftime(dateformat)


def getLastDayInMonth(d, offset=0):
    y = d.year
    m = d.month
    offset += 1     # we go one month to long, then one day before
    if offset > 0:
        while offset:
            offset -= 1
            m += 1
            if m > 12:
                m = 1
                y += 1
    else:
        while offset:
            offset += 1
            m -= 1
            if m < 1:
                m = 12
                y -= 1
    d = datetime.datetime(y, m, 1) - datetime.timedelta(days=1)
    return d.strftime(dateformat)


def addActivity(activity=None,
                userid=None,
                start=None,
                debug=None):
    """
    Add reports for the specified activity and month
    """
    lastday = [0, 0, 0]
    activityDay = None

    if activity.description:
        tmp = activity.description
    else:
        tmp = activity.name

    stop = start.copy()
    stop.setFirstDayInMonth(1)
    stop.addTime(seconds=-1)

    activityMonth = ActivityMonth(start, stop, description=tmp)

    values = []
    sql = "SELECT * FROM report WHERE"
    sql += " user_id=%s AND"
    values.append(userid)

    sql += " activityid=%s AND"
    values.append(activity._id)

    sql += " start>=%s AND"
    values.append(str(start.obj))

    sql += " stop<=%s AND"
    values.append(str(stop.obj))

    sql += " deleted=0"
    sql += " ORDER BY start"
    try:
        data = db2.conn.select_all(sql, values)
        for report in data:
            # new day?
            if lastday != [report.start.year, report.start.month, report.start.day]:
                if activityDay:
                    activityMonth.addDay(activityDay)
                activityDay = ActivityDay(report.start.date())
                lastday = [report.start.year, report.start.month, report.start.day]

            comment = report.comment
            if debug is not None:
                comment += " (%s)" % report._id

            rep = ReportRes(report.start, report.stop, comment)
            activityDay.addReport(rep)

        if activityDay is not None:
            activityMonth.addDay(activityDay)
    except db2.DbException as err:
        errors.append("db.Error %s" % err)

    return activityMonth


@server.route("/reports/monthly")
def reports_monthly():
    errors.clear()
    p = AttrDict()
    activities = Activities()

    # parameters, in url
    p.userid = request.args.get("userid", 1, type=int)
    p.activityid = request.args.get("activityid", -1, type=int)
    p.start = request.args.get("start", None)
    p.debug = request.args.get("debug", None)
    p.action = request.args.get("action", "-noaction-")

    p.dstart = MyDateTime()
    try:
        if p.start is not None:
            p.dstart.setFromStr(p.start + "-01 00:00:00")
    except ValueError as e:
        print(e)
        errors.append("Incorrect start date, using todays date")

    p.dstart.day = 1

    p.prevstart = p.dstart.copy()
    p.prevstart.setFirstDayInMonth(-1)

    p.nowstart = MyDateTime()
    p.prevstart.setFirstDayInMonth(0)

    p.nextstart = p.dstart.copy()
    p.nextstart.setFirstDayInMonth(1)

    # Show filters, at top of screen
    p.param = "&userid=%s&activityid=%s" % (p.userid, p.activityid)

    if p.action == "+A" or p.action == "-A":
        if p.activityid < 0:
            if p.action == "+A":
                # get first activity
                sql = "SELECT * FROM activity ORDER BY name LIMIT 1"
            else:
                # get last activity
                sql = "SELECT * FROM activity ORDER BY name DESC LIMIT 1"
            data = db2.conn.select_one(sql, (p.activityid,))
            if data:
                p.activityid = data._id
        else:
            direction = ">"
            desc = ""
            if p.action == "-A":
                direction = "<"
                desc = "DESC"

            try:
                # get current activity name from id
                sql = "SELECT * FROM activity WHERE _id=%s"
                data = db2.conn.select_one(sql, (p.activityid,))
                if data:
                    # get next/prev activity
                    sql = "SELECT * FROM activity WHERE name %s %%s ORDER BY name %s LIMIT 1" % (direction, desc)
                    try:
                        data2 = db2.conn.select_one(sql, (data.name, ))
                        if data2:
                            print("data2", data2)
                            p.activityid = data2._id
                        else:
                            p.activityid = -1
                    except db2.conn.exception as err:
                        errors.append("db.Error %s" % err)
                else:
                    errors.append("Can't get current activity from activityid %s" % p.activityid)
            except db2.conn.exception as err:
                errors.append("db.Error: %s" % err)

    if p.userid is None:
        errors.append("Please specify user")
    elif p.activityid is None:
        errors.append("Please specifiy activity")
    else:
        sql = "SELECT * FROM activity"
        values = []

        if p.activityid > 0:
            sql += " WHERE _id=%s"
            values.append(p.activityid)

        sql += " ORDER BY name"
        try:
            activitylist = db2.conn.select_all(sql, values)
            for activity in activitylist:
                activityMonth = addActivity(
                    activity=activity,
                    userid=p.userid,
                    start=p.dstart,
                    debug=p.debug)
                if len(activityMonth.days) > 0:
                    activities.addActivity(activityMonth)

        except db2.DbException as err:
            errors.append("Can't load list of activities %s", err)

    log.debug("p.dstart 2  %s" % p.dstart)
    log.debug("p.prevstart %s" % p.prevstart)
    log.debug("p.nowstart  %s" % p.nowstart)
    log.debug("p.nextstart %s" % p.nextstart)

    args = {
        'errors': errors,
        'activities': activities,
        'p': p,
        'htmllib': htmllib,
    }
    return render_template('reports.html', **args)

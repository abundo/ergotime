#!/usr/bin/env python3

"""
Activities controller

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

from flask import render_template
from flask.ext.login import login_required
from server import server

import lib.log as log
import lib.util as util   # read settings
import lib.db as db2
import lib.htmllib

db2.conn = db2.Database(config["db_conf"])

htmllib = lib.htmllib.Htmllib(db2.conn)

dateformat = '%Y-%m-%d'
datetimeformat = dateformat + ' %H:%M:%S'

errors = []


@server.route("/activity/list")
@login_required
def activity_list():
    errors.clear()
    args = {}
    return render_template('activity.html', **args)

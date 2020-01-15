#!/usr/bin/env python3

"""
Helpers to create HTML code

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


class Htmllib:

    def __init__(self, db=None):
        self.db = db

    def getUserCombo(self, name="userid", selected=None):
        s = "<select name='%s'>" % name
        try:
            sql = "SELECT * FROM users ORDER BY name"
            data = self.db.select_all(sql)
            for user in data:
                if selected == str(user._id):
                    tmp = " selected"
                else:
                    tmp = ""
                s += "<option value='%s'%s>%s</option>" % (user._id, tmp, user.name)
        except self.db.exception:
            pass
        s += "</select>"
        return s

    def getActivityCombo(self, name="activity", selected=None, additional=None):
        s = "<select name='%s'>" % name
        if selected:
            selected = str(selected)
        if additional:
            for activity in additional:
                s += "  <option value='%s'>%s</option>" % (activity[0], activity[1])
        try:
            sql = "SELECT * FROM activity ORDER BY name"
            data = self.db.select_all(sql)
            for activity in data:
                if selected == str(activity._id):
                    tmp = " selected"
                else:
                    tmp = ""
                s += "  <option value='%s'%s>%s</option>" % (activity._id, tmp, activity.name)
        except self.db.exception:
            pass
        s += "</select>"
        return s

    def checkBox(self, name="checkbox", value=None):
        s = "<input type='checkbox' name=%s" % name
        if value is not None and value != "":
            s += " checked"
        s += ">"
        return s

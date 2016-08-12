#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) 2013, Anders Lowinger, Abundo AB
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the <organization> nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


class Htmllib:

    def __init__(self, db=None):
        self.db = db

    def getUserCombo(self, name='userid', selected=None):
        s = "<select name='%s'>" % name
        try:
            sql = "SELECT * FROM users ORDER BY name"
            data = self.db.select_all(sql)
            for user in data:
                if selected == str(user._id):
                    tmp = ' selected'
                else:
                    tmp = ''
                s += "<option value='%s'%s>%s</option>" % (user._id, tmp, user.name)
        except self.db.exception as err:
            pass
        s += "</select>"
        return s

    def getActivityCombo(self, name='activity', selected=None, additional=None):
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
                    tmp = ' selected'
                else:
                    tmp = ''
                s += "  <option value='%s'%s>%s</option>" % (activity._id, tmp, activity.name)
        except self.db.exception as err:
            pass
        s += "</select>"
        return s
    
    def checkBox(self, name='checkbox', value=None):
        s = "<input type='checkbox' name=%s" % name
        if value != None and value != '':
            s += " checked"
        s += ">"
        return s

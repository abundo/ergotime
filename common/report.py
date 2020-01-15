#!/usr/bin/env python3

"""
Model for Reports

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


class Report(AttrDict):

    _primary_key = "_id"

    def __init__(self):
        super().__init__()

        self._id = -1
        self.user_id = -1
        self.activityid = -1
        self.start = None
        self.stop = None
        self.comment = ""
        
        self.modified = None
        self.seq = -1
        self.deleted = 0
        
        self.server_id = -1     # used on client, _id on server
        self.updated = 0        # used on client, indicates local updates need sync

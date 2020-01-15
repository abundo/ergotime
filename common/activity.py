#!/usr/bin/env python3

"""
Model for Activites

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


class Activity(AttrDict):

    _primary_key = "_id"

    def __init__(self):
        super().__init__()
        
        self._id = -1
        self.name = ""
        self.description = ""
        self.active = 0

#!/usr/bin/env python3
"""
Starts the flask web server in debug mode

Used during development

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

import sys
import yaml


with open("/etc/ergotime/ergotime.yaml", "r") as f:
    try:
        config = yaml.load(f)
    except yaml.YAMLError as err:
        print("Cannot load config, err: %s" % err)
        sys.exit(1)

sys.path.insert(0, config["basedir"])

from server.app import server

# app.config["myconf"] = config

server.run(host="0.0.0.0", debug=True)

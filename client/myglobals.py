#!/usr/bin/env python3

"""
Global variables

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

import os
import sys
import PyQt5.QtWidgets as QtWidgets

# ----------------------------------------------------------------------

# Setup debug bitmask, used during development

DEBUG_FILES             = 1 << 0
DEBUG_SETTINGS          = 1 << 1
DEBUG_ACTIVITYMGR       = 1 << 3
DEBUG_REPORTMGR         = 1 << 4
DEBUG_MAINWIN           = 1 << 5
DEBUG_OPTIONS           = 1 << 6
DEBUG_SYSTRAY           = 1 << 7

DEBUG_LEVEL = 0
DEBUG_LEVEL |= DEBUG_FILES       * 1
DEBUG_LEVEL |= DEBUG_SETTINGS    * 0
DEBUG_LEVEL |= DEBUG_ACTIVITYMGR * 1
DEBUG_LEVEL |= DEBUG_REPORTMGR   * 1
DEBUG_LEVEL |= DEBUG_MAINWIN     * 1
DEBUG_LEVEL |= DEBUG_OPTIONS     * 1
DEBUG_LEVEL |= DEBUG_SYSTRAY     * 1

# ----------------------------------------------------------------------


runFromIde = "runFromIde" in os.environ


# Create datadir in the users home directory

userdir = os.path.expanduser("~") + os.sep + ".ergotime"
if not os.path.exists(userdir):
    os.mkdir(userdir)

userconffile = userdir + os.sep + "ergotime.ini"

if DEBUG_LEVEL & DEBUG_FILES:
    localDatabaseName = "ergotime-devel.db"   # todo find out automatically if we are running from the IDE
else:
    localDatabaseName = "ergotime.db"
localDatabaseName = userdir + os.sep + localDatabaseName


def createQApplication():
    app = QtWidgets.QApplication(sys.argv)

    app.setQuitOnLastWindowClosed(False)
    app.setOrganizationName("Abundo AB")
    app.setOrganizationDomain("abundo.se")
    app.setApplicationName("ErgoTime")
    return app

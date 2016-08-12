#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Global variables
'''

'''
Copyright (c) 2013, Anders Lowinger, Abundo AB
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
   * Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.
   * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.
   * Neither the name of the <organization> nor the
     names of its contributors may be used to endorse or promote products
     derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

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

DEBUG = 0
DEBUG |= DEBUG_FILES       * 1
DEBUG |= DEBUG_SETTINGS    * 0
DEBUG |= DEBUG_ACTIVITYMGR * 1
DEBUG |= DEBUG_REPORTMGR   * 1
DEBUG |= DEBUG_MAINWIN     * 1
DEBUG |= DEBUG_OPTIONS     * 1
DEBUG |= DEBUG_SYSTRAY     * 1

# ----------------------------------------------------------------------


runFromIde = "runFromIde" in os.environ


# Create datadir in the users home directory

userdir = os.path.expanduser("~") + os.sep + ".ergotime"
if not os.path.exists(userdir):
    os.mkdir(userdir)

userconffile = userdir + os.sep + "ergotime.ini" 

if DEBUG & DEBUG_FILES:
    localDatabaseName = "ergotime-devel.db" # todo find out automatically if we are running from the IDE
else:
    localDatabaseName = "ergotime.db"
localDatabaseName = userdir + os.sep + localDatabaseName


def createQApplication():
    app = QtWidgets.QApplication(sys.argv)
    
    app.setQuitOnLastWindowClosed(False);
    app.setOrganizationName("Abundo AB");
    app.setOrganizationDomain("abundo.se");
    app.setApplicationName("ErgoTime");
    return app

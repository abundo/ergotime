'''
Created on 13 nov 2013

@author: anders
'''

import os

# ----------------------------------------------------------------------

# Setup debug bitmask, used during development

DEBUG_FILES             = 1 << 0
DEBUG_SETTINGS          = 1 << 1
DEBUG_BASIUM            = 1 << 2
DEBUG_ACTIVITYMGR       = 1 << 3
DEBUG_REPORTMGR         = 1 << 4
DEBUG_MAINWIN           = 1 << 5
DEBUG_OPTIONS           = 1 << 6
DEBUG_SYSTRAY           = 1 << 7

DEBUG = 0
DEBUG |= DEBUG_FILES       * 1
DEBUG |= DEBUG_SETTINGS    * 0
DEBUG |= DEBUG_BASIUM      * 1
DEBUG |= DEBUG_ACTIVITYMGR * 1
DEBUG |= DEBUG_REPORTMGR   * 1
DEBUG |= DEBUG_MAINWIN     * 1
DEBUG |= DEBUG_OPTIONS     * 1
DEBUG |= DEBUG_SYSTRAY     * 1

# ----------------------------------------------------------------------

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

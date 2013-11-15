'''
Created on 13 nov 2013

@author: anders
'''

from PySide import QtCore

idleTimeout = 600

attrs = [
    "idleTimeout", 
    "reportSyncInterval", 
    "activitySyncInterval",
]


qsettings = QtCore.QSettings()

for attr in attrs:
    print(attr)

if __name__ == '__main__':
    pass

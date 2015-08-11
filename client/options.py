#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
GUI edit options
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

# import PyQt5.QtCore as QtCore
import PyQt5.QtWidgets as QtWidgets
from PyQt5.Qt import QFont

import options_win

from myglobals import *
from logger import log
from settings import sett


class OptionsWin(QtWidgets.QDialog, options_win.Ui_Options):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.txtPassword.setEchoMode(QtWidgets.QLineEdit.Password)
        self.comboLoglevel.addItem("INFO")
        self.comboLoglevel.addItem("WARNING")
        self.comboLoglevel.addItem("ERROR")
        self.comboLoglevel.addItem("DEBUG")
        self.comboLoglevel.addItem("CONSOLE")
        
        self.comboFontSize.addItems(
            ['6','7','8','9','10','11','12','13','14',
             '15','16','18','20','22','24','26','28',
             '32','36','40','44','48','54','60','66',
             '72','80','88','96'])
        
        # Copy from settings -> GUI

        # ----- tab general
        self.comboFontName.setFont(QFont(sett.fontName))
        self.comboFontSize.setCurrentIndex(self.comboFontSize.findText(sett.fontSize))
        self.txtUsername.setText(sett.username)
        self.txtPassword.setText("<Not displayed>")
        self.spinIdleTimeout.setValue(sett.idle_timeout)
        self.txtDatabasedir.setText(sett.database_dir)
        self.comboLoglevel.setCurrentIndex( self.comboLoglevel.findText(sett.loglevel) )
        
        # ----- tab activity
        self.spinActivitySyncInterval.setValue(sett.activity_sync_interval)
        
        # ----- tab report
        self.spinReportSyncInterval.setValue(sett.report_sync_interval)
        
        # ----- tab network
        self.txtServerUrl.setText(sett.server_url)
        self.spinNetworkTimeout.setValue(sett.networkTimeout)
        
        self.btnOk.clicked.connect(self.ok)
        self.btnCancel.clicked.connect(self.cancel)

    def ok(self):
        log.debugf(DEBUG_OPTIONS, "Saving new settings")

        # Copy from GUI -> settings
        
        # ----- tab general
        
        font = self.comboFontName.currentFont().toString().split(",")
        sett.fontName = font[0]
        sett.fontSize = self.comboFontSize.itemText(self.comboFontSize.currentIndex())
        sett.username = self.txtUsername.text()
        sett.password = self.txtPassword.text()
        sett.idle_timeout = self.spinIdleTimeout.value()
        sett.database_dir = self.txtDatabasedir.text()
        sett.loglevel = self.comboLoglevel.currentText()

        # ----- tab activity
        sett.activity_sync_interval = self.spinActivitySyncInterval.value()
        
        # ----- tab report
        sett.report_sync_interval = self.spinReportSyncInterval.value()
        
        # ----- tab network
        sett.server_url = self.txtServerUrl.text()
        sett.networkTimeout = self.spinNetworkTimeout.value()
        
        sett.sync()
        self.accept()
      
    def cancel(self):
        log.debugf(DEBUG_OPTIONS, "cancel, no settings saved")
        self.reject()


if __name__ == '__main__':
    """Module test"""
    app = createQApplication()
    win = OptionsWin()
    win.exec_()

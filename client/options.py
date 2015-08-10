'''
Created on 13 nov 2013

@author: anders
'''

import PyQt5.QtCore as QtCore
# import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
from PyQt5.Qt import QGuiApplication, QFont

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

        # ----- general
        
        self.comboFontName.setFont(QFont(sett.fontName))
        self.comboFontSize.setCurrentIndex(self.comboFontSize.findText(sett.fontSize))
        self.txtUsername.setText(sett.username)
        self.txtPassword.setText("<Not displayed>")
        self.spinIdleTimeout.setValue(sett.idle_timeout)
        self.txtDatabasedir.setText(sett.database_dir)
        self.comboLoglevel.setCurrentIndex( self.comboLoglevel.findText(sett.loglevel) )
        
        # ----- activity
        self.spinActivitySyncInterval.setValue(sett.activity_sync_interval)
        
        # ----- report
        self.spinReportSyncInterval.setValue(sett.report_sync_interval)
        
        # ----- network
        self.txtServerUrl.setText(sett.server_url)
        self.spinNetworkTimeout.setValue(sett.networkTimeout)
        
        self.spinIdleTimeout.setValue(sett.idle_timeout)
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
    pass

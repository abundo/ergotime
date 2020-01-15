#!/usr/bin/env python3

"""
GUI Window, edit options

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
            ["6", "7", "8", "9", "10", "11", "12", "13", "14",
             "15", "16", "18", "20", "22", "24", "26", "28",
             "32", "36", "40", "44", "48", "54", "60", "66",
             "72", "80", "88", "96"])

        # Copy from settings -> GUI

        # ----- tab general
        self.comboFontName.setFont(QFont(sett.fontName))
        self.comboFontSize.setCurrentIndex(self.comboFontSize.findText(sett.fontSize))
        self.txtUsername.setText(sett.username)
        self.txtPassword.setText("<Not displayed>")
        self.spinIdleTimeout.setValue(sett.idle_timeout)
        self.txtDatabasedir.setText(sett.database_dir)
        self.comboLoglevel.setCurrentIndex(self.comboLoglevel.findText(sett.loglevel))

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


if __name__ == "__main__":
    # Module test
    app = createQApplication()
    win = OptionsWin()
    win.exec_()

#!/usr/bin/env python3

"""
GUI About dialog

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

import util
import about_win


class AboutWin(QtWidgets.QDialog, about_win.Ui_Options):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.btnClose.clicked.connect(self.accept)


if __name__ == "__main__":
    # Module test
    app = util.createQApplication()
    win = AboutWin()
    win.exec_()

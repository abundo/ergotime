#!/usr/bin/env python3

"""
Application startup

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
import os.path

import sys
import traceback

import PyQt5.QtCore as QtCore
import PyQt5.QtWidgets as QtWidgets

from myglobals import *

import main


old_stdout = sys.stdout
old_stderr = sys.stderr
app = None


def handle_exception(exc_type, exc_value, exc_traceback):
    """
    handle all python exceptions, show a dialog box with the error
    """

    # KeyboardInterrupt is a special case.
    # We don't raise the error dialog when it occurs.
    if issubclass(exc_type, KeyboardInterrupt):
        if app:
            app.quit()

    filename, line, dummy1, dummy2 = traceback.extract_tb(exc_traceback).pop()
    filename = os.path.basename(filename)
    error = "%s: %s" % (exc_type.__name__, exc_value)

    QtWidgets.QMessageBox.critical(
        None, "Error",
        "<html>A critical error has occured.<br/> "
        + "<b>%s</b><br/><br/>" % error
        + "It occurred at <b>line %d</b> of file <b>%s</b>.<br/>" % (line, filename)
        + "</html>"
    )

    print("Closed due to an error. This is the full error report:")
    print()
    print("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    sys.exit(1)


def main_():
    # global app
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"     # Handle HIDPI
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    QtWidgets.QApplication.setStyle("Fusion")
    app = QtWidgets.QApplication(sys.argv)

    app.setQuitOnLastWindowClosed(False)
    app.setOrganizationName("Abundo AB")
    app.setOrganizationDomain("abundo.se")
    app.setApplicationName("ErgoTime")

    sys.excepthook = handle_exception

    w_main = main.MainWin()
    try:
        w_main.show()
        sys.exit(app.exec_())
    except Exception as err:
        # Restore stdout/stderr so we can see the error
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        print("Error: %s" % err)


if __name__ == "__main__":
    main_()

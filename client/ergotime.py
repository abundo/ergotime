#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Application startup
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

import os.path
import builtins

from myglobals import *

import sys
import traceback
import encodings.idna   # make sure cxfreeze includes the module

import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets

import main


old_stdout = sys.stdout
old_stderr = sys.stderr


def handle_exception(exc_type, exc_value, exc_traceback):
    """ handle all exceptions """

    # KeyboardInterrupt is a special case.
    # We don't raise the error dialog when it occurs.
    if issubclass(exc_type, KeyboardInterrupt):
        if app:
            app.quit()

    filename, line, dummy, dummy = traceback.extract_tb( exc_traceback ).pop()
    filename = os.path.basename( filename )
    error    = "%s: %s" % ( exc_type.__name__, exc_value )

    QtWidgets.QMessageBox.critical(None,"Error",
        "<html>A critical error has occured.<br/> "
        + "<b>%s</b><br/><br/>" % error
        + "It occurred at <b>line %d</b> of file <b>%s</b>.<br/>" % (line, filename)
        + "</html>")

    print("Closed due to an error. This is the full error report:")
    print()
    print("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    sys.exit(1)
  
def main_():
    global app
    app = QtWidgets.QApplication(sys.argv)
    
    app.setQuitOnLastWindowClosed(False);
    app.setOrganizationName("Abundo AB");
    app.setOrganizationDomain("abundo.se");
    app.setApplicationName("ErgoTime");

    sys.excepthook = handle_exception

    w_main = main.MainWin()
    try:
        w_main.show()
        sys.exit( app.exec_() )
    except Exception as e:
        # Restore stdout/stderr so we can see the error
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        print("Error: %s" % e)

if __name__ == '__main__':
    main_()

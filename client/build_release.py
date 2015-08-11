#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Build script for cx_freeze
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

# Let's start with some default (for me) imports...

import sys
from cx_Freeze import setup, Executable

# Process the includes, excludes and packages first

#sys.path.append("d:/hack/git/basium")
#sys.path.append("d:/hack/git/ergotime")
#sys.path.append("d:/hack/git/ergotime/client/model")

includes = ["logging.handlers","sqlite3"]
includes.append("basium_driver_json")
includes.append("basium_driver_sqlite")

excludes = []

packages = ["atexit", "basium"]

path = sys.path
path.append("d:/hack/git/ergotime")
path.append("d:/hack/git/ergotime/client")

# This is a place where the user custom code may go. You can do almost
# whatever you want, even modify the data_files, includes and friends
# here as long as they have the same variable name that the setup call
# below is expecting.

# No custom code added

# The setup for cx_Freeze is different from py2exe. Here I am going to
# use the Python class Executable from cx_Freeze

base = None
if sys.platform == "win32":
    base = "Win32GUI"

GUI2Exe_Target_1 = Executable(
    # what to build
    script = "ergotime.py",
    initScript = None,
    base = base,
#    targetDir = r"dist/",
    targetName = "ergotime.exe",
    compress = False,
    copyDependentFiles = True,
    appendScriptToExe = False,
    appendScriptToLibrary = False,
    icon = "resource/ergotime.ico"
    )


# That's serious now: we have all (or almost all) the options cx_Freeze
# supports. I put them all even if some of them are usually defaulted
# and not used. Some of them I didn't even know about.

setup(

    name = "ErgoTime Client",
    version = "1.0.0",
    description = "ErgoTime Client",
    author = "Anders Löwinger",

    options = {"build_exe": {"includes": includes,
                             "excludes": excludes,
                             "packages": packages,
                             "path": path
                             }
               },

    executables = [GUI2Exe_Target_1]
    )

# This is a place where any post-compile code may go.
# You can add as much code as you want, which can be used, for example,
# to clean up your folders or to do some particular post-compilation
# actions.

# No post-compilation code added


# And we are done. That's a setup script :-D

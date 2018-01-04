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

from cx_Freeze import setup, Executable
import sys
import shutil

# Remove the existing folders
shutil.rmtree("build", ignore_errors=True)

sys.path.append("d:/hack/eclipse/ergotime")

includes = ["logging.handlers", "sqlite3", "codecs"]
includefiles = []
excludes = []
packages = ["atexit"]

# This is a place where the user custom code may go. You can do almost
# whatever you want, even modify the data_files, includes and friends
# here as long as they have the same variable name that the setup call
# below is expecting.

base = None
if sys.platform == "win32":
    base = "Win32GUI"

GUI2Exe_Target_1 = Executable(
    # what to build
    script = "ergotime.py",
    initScript = None,
    base = base,
    
    targetName = "ergotime.exe",
#    compress = False,
#    copyDependentFiles = True,
#    copy_dependent_files = True,
#    appendScriptToExe = False,
#    append_script_to_exe = False,
#    appendScriptToLibrary = False,
    icon = "resource/ergotime.ico"
)


# BUild target
setup(
    name = "ErgoTime Client",
    version = "1.0.1",
    description = "ErgoTime Client",
    author = "Anders Löwinger",

    options = {"build_exe": {"includes": includes,
                             "include_files": includefiles,
                             "excludes": excludes,
                             "packages": packages,
                             "path": sys.path,
                             }
               },

    executables = [GUI2Exe_Target_1]
)


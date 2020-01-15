#!/usr/bin/env python3

"""
Build script for cx_freeze

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
    script="ergotime.py",
    initScript=None,
    base=base,
    
    targetName="ergotime.exe",
    # compress = False,
    # copyDependentFiles = True,
    # copy_dependent_files = True,
    # appendScriptToExe = False,
    # append_script_to_exe = False,
    # appendScriptToLibrary = False,
    icon="resource/ergotime.ico"
)


# BUild target
setup(
    name="ErgoTime Client",
    version="1.0.1",
    description="ErgoTime Client",
    author="Anders Löwinger",

    options={"build_exe": {"includes": includes,
                           "include_files": includefiles,
                           "excludes": excludes,
                           "packages": packages,
                           "path": sys.path,
                           }
               },

    executables=[GUI2Exe_Target_1]
)

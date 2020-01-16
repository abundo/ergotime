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

DEST = "../../ergotime.cxfreeze"

# Remove the existing folders
shutil.rmtree(DEST, ignore_errors=True)


includes = ["logging.handlers", "sqlite3", "codecs"]
includefiles = []
excludes = ["tkinter", "html", "lib2to3", "multiprocessing", "unittest", "xml", "xmlrpc"]
packages = ["atexit"]

base = None
if sys.platform == "win32":
    base = "Win32GUI"

GUI2Exe_Target_1 = Executable(
    # what to build
    script="ergotime.py",
    initScript=None,
    base=base,
    
    targetName="ergotime.exe",
    icon="resource/ergotime.ico"
)


# BUild target
setup(
    name="ErgoTime Client",
    version="1.0.1",
    description="Ergotime Client",
    author="Anders Löwinger",

    options={
        "build_exe": {
            "build_exe": DEST,
            "includes": includes,
            "include_files": includefiles,
            "excludes": excludes,
            "packages": packages,
            "path": sys.path,
        }
    },

    executables=[GUI2Exe_Target_1]
)

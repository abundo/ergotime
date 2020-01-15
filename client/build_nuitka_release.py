#!/usr/bin/env python3

r"""
Build a release, standalone executable, for windows using nuitka

Change directory into the client directory, and run this script

Example:
    \pyhton3.7\python build_nuitka_release.py


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

import sys
from distutils.dir_util import copy_tree
import subprocess
import shutil


# Location for the ergotime.build and ergotime.dist directories
DEST = "../.."


# Remove the existing build
shutil.rmtree("%s/ergotime.dist" % DEST, ignore_errors=True)


def main():
    cmd = []
    cmd.append(sys.executable)
    cmd.append("-m")
    cmd.append("nuitka")
    cmd.append("--follow-imports")
    cmd.append("--standalone")
    cmd.append("--plugin-enable=qt-plugins")
    cmd.append("--output-dir=%s" % DEST)
    cmd.append("--windows-icon=resource/ergotime.ico")
    cmd.append("--windows-disable-console")
    cmd.append("ergotime.py")

    print("#" * 79)
    print("# Compiling code")
    print("#" * 79)
    p = subprocess.run(cmd, check=True)

    if p.returncode == 0:
        src = "resource"
        dst = "%s/ergotime.dist/resource" % DEST
        print("#" * 79)
        print("# Copying resource files")
        print("# src %s" % src)
        print("# dst %s" % dst)
        print("#" * 79)
        files = copy_tree(src, dst, )
        for f in files:
            print(f)

    else:
        print("#" * 79)
        print("# ERROR Compilation did not complete")
        print("#" * 79)


if __name__ == "__main__":
    main()

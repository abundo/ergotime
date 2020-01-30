#!/usr/bin/env python3

r"""
Build a release, standalone executable, for windows using nuitka

Change directory into the ergotime\client directory, and run this script

Example:

    \python3.7\python build_nuitka_release.py


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
import sys
import subprocess
import shutil


# Location for the ergotime.build and ergotime.dist directories
DEST = "../.."


# Remove the existing build
shutil.rmtree("%s/ergotime.dist" % DEST, ignore_errors=True)

current_path = os.path.dirname(os.path.realpath(__file__))
parent_path = current_path.rsplit(os.path.sep)[:-1]
parent_path = os.path.sep.join(parent_path)

# Add ergotime to PYTHONPATH,  import lib.* does not work without this
p = os.environ.get("PYTHONPATH", "")
p = parent_path + ";" + p
os.environ["PYTHONPATH"] = p
print("path", p)


def main():
    print("#" * 79)
    print("# Compiling user interface and resources")
    print("#" * 79)
    cmd = ["compile_ui.bat"]
    print(" ".join(cmd))
    p = subprocess.run(cmd, check=True)

    cmd = []
    cmd.append(sys.executable)  # Same python intepreter as this script is started with
    cmd.append("-m")
    cmd.append("nuitka")
    cmd.append("--follow-imports")
    cmd.append("--remove-output")
    cmd.append("--standalone")
    cmd.append("--plugin-enable=qt-plugins")
    cmd.append("--output-dir=%s" % DEST)
    cmd.append("--windows-icon=%s\\resource\\ergotime.ico" % current_path)
    cmd.append("--assume-yes-for-downloads")
    cmd.append("--windows-disable-console")
    cmd.append("--mingw64")
    cmd.append("ergotime.py")

    print("#" * 79)
    print("# Compiling code")
    print("#" * 79)
    print(" ".join(cmd))
    p = subprocess.run(cmd, check=True)

    if p.returncode != 0:
        print("#" * 79)
        print("# ERROR Compilation did not complete")
        print("#" * 79)
    else:
        print("#" * 79)
        print("# Ok")
        print("#" * 79)


if __name__ == "__main__":
    main()

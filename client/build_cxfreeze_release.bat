@echo off
rem
rem Build a windows release, using the cxfreeze tool
rem

set PYTHON=c:\python37

%PYTHON%\python build_cxfreeze_release.py build

mkdir build\exe.win-amd64-3.6\resource
xcopy resource build\exe.win-amd64-3.6\resource /s /y

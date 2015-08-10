rem set TARGETDIR=c:\opt\ergotime2-pyqt
set PYTHON=c:\opt\python34
set CXFREEZE=%PYTHON%\scripts\cxfreeze
set PYTHONPATH=d:\hack\git\basium
%PYTHON%\python build_release.py build

mkdir build\exe.win-amd64-3.4\resource
xcopy resource build\exe.win-amd64-3.4\resource /s

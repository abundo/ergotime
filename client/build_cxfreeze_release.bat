rem set TARGETDIR=c:\opt\ergotime2-pyqt

set PYTHON=c:\opt\python36
rem set CXFREEZE=%PYTHON%\scripts\cxfreeze

%PYTHON%\python build_release.py build

mkdir build\exe.win-amd64-3.6\resource
xcopy resource build\exe.win-amd64-3.6\resource /s /y

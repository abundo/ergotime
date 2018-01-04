@echo off

rem PySide
rem set qtui=c:\opt\python36\scripts\pyside-uic.exe

rem PyQT 
set qtui=c:\opt\python36\scripts\pyuic5.exe

for /r %%i in (*.ui) do %qtui% %%~fi -o %%~di%%~pi%%~ni.py

@echo off
rem set qtui=c:\opt\python34\scripts\pyside-uic.exe
set qtui=pyuic5
for /r %%i in (*.ui) do %qtui% %%~fi -o %%~di%%~pi%%~ni.py

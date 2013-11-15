@echo off
set qtui=c:\opt\python33\scripts\pyside-uic.exe
for /r %%i in (*.ui) do %qtui% %%~fi -o %%~di%%~pi%%~ni.py

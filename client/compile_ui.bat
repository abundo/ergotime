@echo off
rem
rem Used for Windows platform
rem Compile all .ui files to .py files
rem

rem PySide
rem set qtui=c:\python37\scripts\pyside-uic.exe

rem PyQT 
set qtui=c:\python37\scripts\pyuic5.exe
set qtrcc=c:\python37\scripts\pyrcc5.exe

echo =========================================================================
echo Build resources
echo =========================================================================
%qtrcc% resource.qrc -o resource.py

echo =========================================================================
echo Compile the .ui files
echo =========================================================================
for /r %%i in (*.ui) do %qtui% %%~fi -o %%~di%%~pi%%~ni.py

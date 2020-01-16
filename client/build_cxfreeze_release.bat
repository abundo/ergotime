@echo off
rem
rem Build a windows release, using the cxfreeze tool
rem
rem Make sure you have installed cx-freeze, example:
rem     \python3.7\script\pip install cx-freeze

set PYTHON=c:\python37

echo =========================================================================
echo  Compile user interface files and resources
echo =========================================================================
call compile_ui.bat

echo =========================================================================
echo  Build program
echo =========================================================================

%PYTHON%\python build_cxfreeze_release.py build

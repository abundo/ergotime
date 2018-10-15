#!/bin/bash

for f in *.ui
do
  echo Compiling $f
  pyuic5 $f -o "${f%.*}".py 
done

# for /r %%i in (*.ui) do %qtui% %%~fi -o %%~di%%~pi%%~ni.py

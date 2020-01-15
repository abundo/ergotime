#!/bin/bash

# Used for Linux/unix platform
# Compile all .ui files to .py files

for f in *.ui
do
  echo Compiling $f
  pyuic5 $f -o "${f%.*}".py 
done

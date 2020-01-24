# Ergotime

Server and client application for tracking worked time and generate reports.

The client Supports full offline mode, with reliable two-way sync with server


# License

See the [LICENSE](LICENSE) file for license rights and limitations (GPLv3).


# Quick Start

## Server

Todo


## Client

Todo

dependencies:
- pip install requests

# Development

Common for client and server
- Visual Studio Code as IDE
- flake8 as linter


## Client

Developed with
- python3.7
- pyqt5 for GUI
- sqlite3 for local database

To build releases
- nuitka
- cxfreeze

Tested and supports windows and linux (ubuntu/fedora). 
Should be possible to port to osx without too much issues.


## Server

Developed with
  - python3
  - flask as Web GUI

Uses
  - postgresql as database

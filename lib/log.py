#!/usr/bin/env python3

"""
Logging functionality

Copyright (C) 2020 Anders Lowinger, anders@abundo.se

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import logging
import logging.handlers

INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
DEBUG = logging.DEBUG

level_dict = {"info": logging.INFO,
              "warning": logging.WARNING,
              "error": logging.ERROR,
              "debug": logging.DEBUG}


def activateSyslog():
    syslogger = logging.handlers.SysLogHandler(address="/dev/log")

    formatter = logging.Formatter("%(module)s [%(process)d]: %(levelname)s %(message)s")
    syslogger.setFormatter(formatter)
    logger.addHandler(syslogger)


def setLevel(level):
    if isinstance(level, str):
        level = level_dict[level]
    logger.setLevel(level)


def info(msg):
    msg = str(msg).replace("\n", ", ")
    logger.info(msg)


def warning(msg):
    msg = str(msg).replace("\n", ", ")
    logger.warning(msg)


def error(msg):
    msg = str(msg).replace("\n", ", ")
    logger.error(msg)


def debug(msg):
    try:
        msg = str(msg).replace("\n", ", ")
    except UnicodeDecodeError:
        return
    logger.debug(msg)


formatstr = "%(asctime)s %(levelname)s %(message)s "
loglevel = logging.INFO
logger = logging.getLogger("ergotime")
logger.setLevel(loglevel)

# remove all handlers
for hdlr in logger.handlers:
    logger.removeHandler(hdlr)

consolehandler = logging.StreamHandler()

formatter = logging.Formatter(formatstr)
consolehandler.setFormatter(formatter)
logger.addHandler(consolehandler)

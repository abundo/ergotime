#!/usr/bin/env python3

"""
Idle detector

Support:
- Windows
- Linux

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

import platform

import ctypes
import ctypes.util


class WindowsIdleDetect:

    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.c_uint),
            ("dwTime", ctypes.c_uint),
        ]

    def __init__(self):
        self.lastInputInfo = self.LASTINPUTINFO()
        self.lastInputInfo.cbSize = ctypes.sizeof(self.lastInputInfo)

    def get_idle(self):
        """
        Returns idle time in seconds
        """
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(self.lastInputInfo))
        idle_ms = ctypes.windll.kernel32.GetTickCount() - self.lastInputInfo.dwTime
        return idle_ms // 1000


class LinuxIdleDetect:

    class XScreenSaverInfo(ctypes.Structure):
        """
        typedef struct { ... } XScreenSaverInfo;
        """
        _fields_ = [("window",      ctypes.c_ulong),    # screen saver window
                    ("state",       ctypes.c_int),      # off,on,disabled
                    ("kind",        ctypes.c_int),      # blanked,internal,external
                    ("since",       ctypes.c_ulong),    # milliseconds
                    ("idle",        ctypes.c_ulong),    # milliseconds
                    ("event_mask",  ctypes.c_ulong)]    # events

    def __init__(self):
        XScreenSaverInfo_p = ctypes.POINTER(self.XScreenSaverInfo)
        display_p = ctypes.c_void_p
        xid = ctypes.c_ulong
        c_int_p = ctypes.POINTER(ctypes.c_int)
        try:
            libX11path = ctypes.util.find_library("X11")
            if libX11path is None:
                raise OSError("libX11 could not be found.")
            libX11 = ctypes.cdll.LoadLibrary(libX11path)
            libX11.XOpenDisplay.restype = display_p
            libX11.XOpenDisplay.argtypes = ctypes.c_char_p,
            libX11.XDefaultRootWindow.restype = xid
            libX11.XDefaultRootWindow.argtypes = display_p,

            libXsspath = ctypes.util.find_library("Xss")
            if libXsspath is None:
                raise OSError("libXss could not be found.")
            self.libXss = ctypes.cdll.LoadLibrary(libXsspath)
            self.libXss.XScreenSaverQueryExtension.argtypes = display_p, c_int_p, c_int_p
            self.libXss.XScreenSaverAllocInfo.restype = XScreenSaverInfo_p
            self.libXss.XScreenSaverQueryInfo.argtypes = (display_p, xid, XScreenSaverInfo_p)
            self.dpy_p = libX11.XOpenDisplay(None)
            if self.dpy_p is None:
                raise OSError("Could not open X Display.")
            _event_basep = ctypes.c_int()
            _error_basep = ctypes.c_int()
            if self.libXss.XScreenSaverQueryExtension(self.dpy_p, ctypes.byref(_event_basep),
                                                      ctypes.byref(_error_basep)) == 0:
                raise OSError("XScreenSaver Extension not available on display.")
            self.xss_info_p = self.libXss.XScreenSaverAllocInfo()
            if self.xss_info_p is None:
                raise OSError("XScreenSaverAllocInfo: Out of Memory.")
            self.rootwindow = libX11.XDefaultRootWindow(self.dpy_p)
            self.xss_available = True
        except OSError:
            # Logging?
            self.xss_available = False

    def get_idle(self):
        """
        Return the idle time in seconds
        """
        if self.xss_available:
            if self.libXss.XScreenSaverQueryInfo(self.dpy_p, self.rootwindow, self.xss_info_p):
                return int(self.xss_info_p.contents.idle) / 1000
        return 0


class DummyIdleDetect:
    """
    This idle detector is always returning zero (not idle)
    Used when no supported idle detector can be found
    """
    def get_idle(self):
        return 0


try:
    if platform.system() == "Windows":
        idle_detector = WindowsIdleDetect()
    elif platform.system() == "Linux":
        idle_detector = LinuxIdleDetect()
except OSError:
    idle_detector = DummyIdleDetect()


def get_idle():
    return idle_detector.get_idle()


if __name__ == "__main__":
    # Module test
    import time
    while True:
        idle = get_idle()
        print("Idle:", idle)
        time.sleep(1)

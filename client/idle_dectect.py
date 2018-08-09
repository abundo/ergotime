#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Idle detector

Support:
- Windows

'''

'''
Copyright (c) 2013, Anders Lowinger, Abundo AB
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
   * Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.
   * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.
   * Neither the name of the <organization> nor the
     names of its contributors may be used to endorse or promote products
     derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

import os
import platform

import ctypes
import struct


class WindowsIdleDetect:
    
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [
            ('cbSize', ctypes.c_uint),
            ('dwTime', ctypes.c_uint),
        ]

    def __init_(self):
        self.lastInputInfo = self.LASTINPUTINFO()
        self.lastInputInfo.cbSize = ctypes.sizeof(self.lastInputInfo)
    
    def getIdle(self):
        """
        Returns idle time in seconds
        """
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(self.lastInputInfo))
        idle_ms = ctypes.windll.kernel32.GetTickCount() - self.lastInputInfo.dwTime
        return idle_ms // 1000


class LinuxIdleDetect:

    class XScreenSaverInfo( ctypes.Structure):
      """
      typedef struct { ... } XScreenSaverInfo;
      """
      _fields_ = [('window',      ctypes.c_ulong), # screen saver window
                  ('state',       ctypes.c_int),   # off,on,disabled
                  ('kind',        ctypes.c_int),   # blanked,internal,external
                  ('since',       ctypes.c_ulong), # milliseconds
                  ('idle',        ctypes.c_ulong), # milliseconds
                  ('event_mask',  ctypes.c_ulong)] # events
    
    def __init__(self):
        # libraries
        self.xlib = ctypes.cdll.LoadLibrary("libX11.so.6")
        self.xss  = ctypes.cdll.LoadLibrary("libXss.so.1")
        
        self.display = self.xlib.XOpenDisplay(bytes(os.environ["DISPLAY"], 'ascii'))
        self.root = self.xlib.XDefaultRootWindow(self.display)
        self.xss.XScreenSaverAllocInfo.restype = ctypes.POINTER(self.XScreenSaverInfo)
        self.xss_info = self.xss.XScreenSaverAllocInfo()
        
    def get_idle(self):
        """
        Returns idle time in seconds
        """
        self.xss.XScreenSaverQueryInfo( self.display, self.root, self.xss_info)
        idle_ms = self.xss_info.contents.idle 
        return idle_ms // 1000
        

class DummyIdleDetect:

    def get_idle(self):
        return 0


if platform.system() == "Windows":
    idle_detector = WindowsIdleDetect()

elif platform.system() == "Linux":
    idle_detector = LinuxIdleDetect()

else:
    idle_detector = DummyIdleDetect()


def getIdle():
    return idle_detector.get_idle()


if __name__ == '__main__':
    """Test code for idle detect"""
    import time
    while True:
        idle = getIdle()
        print("Idle:", idle)
        time.sleep(1)

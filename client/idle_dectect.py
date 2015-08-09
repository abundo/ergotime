"""
Idle detector

Platform support:
- Windows
- Todo Linux
"""

from ctypes import Structure, windll, c_uint, sizeof, byref

class LASTINPUTINFO(Structure):
    _fields_ = [
        ('cbSize', c_uint),
        ('dwTime', c_uint),
    ]

def getIdle():
    """Returns idle time in seconds"""
    windll.user32.GetLastInputInfo(byref(lastInputInfo))
    millis = windll.kernel32.GetTickCount() - lastInputInfo.dwTime
    return millis // 1000


lastInputInfo = LASTINPUTINFO()
lastInputInfo.cbSize = sizeof(lastInputInfo)

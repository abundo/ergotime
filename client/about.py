'''
Created on 13 nov 2013

@author: anders
'''

import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets

import about_win

class AboutWin(QtWidgets.QDialog, about_win.Ui_Options):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.btnClose.clicked.connect(self.accept)

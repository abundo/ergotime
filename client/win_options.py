'''
Created on 13 nov 2013

@author: anders
'''


from PySide import QtCore, QtGui
import ui_options


class Win_Options(QtGui.QDialog, ui_options.Ui_Options):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        
        self.txtPassword.setEchoMode(QtGui.QLineEdit.Password)

        self.settings = QtCore.QSettings()

        self.btnOk.clicked.connect(self.ok)
        self.btnCancel.clicked.connect(self.cancel)

    def ok(self):
        print("ok")
        self.accept()
      
    def cancel(self):
        print("cancel")
        self.reject()


if __name__ == '__main__':
    pass

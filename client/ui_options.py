# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\hack\eclipse\ErgoTime\ui_options.ui'
#
# Created: Thu Nov 14 01:57:08 2013
#      by: pyside-uic 0.2.15 running on PySide 1.2.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Options(object):
    def setupUi(self, Options):
        Options.setObjectName("Options")
        Options.setWindowModality(QtCore.Qt.WindowModal)
        Options.resize(532, 383)
        self.verticalLayout = QtGui.QVBoxLayout(Options)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtGui.QTabWidget(Options)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtGui.QWidget()
        self.tab.setObjectName("tab")
        self.gridLayout = QtGui.QGridLayout(self.tab)
        self.gridLayout.setObjectName("gridLayout")
        self.txtIdletimeout = QtGui.QLineEdit(self.tab)
        self.txtIdletimeout.setObjectName("txtIdletimeout")
        self.gridLayout.addWidget(self.txtIdletimeout, 3, 2, 1, 1)
        self.label_2 = QtGui.QLabel(self.tab)
        self.label_2.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 6, 0, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem1, 0, 3, 1, 1)
        self.txtDatabasedir = QtGui.QLineEdit(self.tab)
        self.txtDatabasedir.setObjectName("txtDatabasedir")
        self.gridLayout.addWidget(self.txtDatabasedir, 4, 2, 1, 1)
        self.comboLoglevel = QtGui.QComboBox(self.tab)
        self.comboLoglevel.setObjectName("comboLoglevel")
        self.gridLayout.addWidget(self.comboLoglevel, 5, 2, 1, 1)
        self.label_5 = QtGui.QLabel(self.tab)
        self.label_5.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 5, 0, 1, 1)
        self.comboFont = QtGui.QFontComboBox(self.tab)
        self.comboFont.setObjectName("comboFont")
        self.gridLayout.addWidget(self.comboFont, 0, 2, 1, 1)
        self.txtUsername = QtGui.QLineEdit(self.tab)
        self.txtUsername.setObjectName("txtUsername")
        self.gridLayout.addWidget(self.txtUsername, 1, 2, 1, 1)
        self.label = QtGui.QLabel(self.tab)
        self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_4 = QtGui.QLabel(self.tab)
        self.label_4.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 4, 0, 1, 1)
        self.label_3 = QtGui.QLabel(self.tab)
        self.label_3.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 3, 0, 1, 1)
        self.label_6 = QtGui.QLabel(self.tab)
        self.label_6.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 2, 0, 1, 1)
        self.txtPassword = QtGui.QLineEdit(self.tab)
        self.txtPassword.setObjectName("txtPassword")
        self.gridLayout.addWidget(self.txtPassword, 2, 2, 1, 1)
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.gridLayout_2 = QtGui.QGridLayout(self.tab_2)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label_7 = QtGui.QLabel(self.tab_2)
        self.label_7.setObjectName("label_7")
        self.gridLayout_2.addWidget(self.label_7, 0, 0, 1, 1)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem2, 0, 2, 1, 1)
        self.txtActivitySyncInterval = QtGui.QLineEdit(self.tab_2)
        self.txtActivitySyncInterval.setObjectName("txtActivitySyncInterval")
        self.gridLayout_2.addWidget(self.txtActivitySyncInterval, 0, 1, 1, 1)
        spacerItem3 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_2.addItem(spacerItem3, 1, 0, 1, 1)
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QtGui.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.gridLayout_3 = QtGui.QGridLayout(self.tab_3)
        self.gridLayout_3.setObjectName("gridLayout_3")
        spacerItem4 = QtGui.QSpacerItem(185, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_3.addItem(spacerItem4, 0, 2, 1, 1)
        self.label_8 = QtGui.QLabel(self.tab_3)
        self.label_8.setObjectName("label_8")
        self.gridLayout_3.addWidget(self.label_8, 0, 0, 1, 1)
        spacerItem5 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_3.addItem(spacerItem5, 1, 0, 1, 1)
        self.txtReportSyncInterval = QtGui.QLineEdit(self.tab_3)
        self.txtReportSyncInterval.setObjectName("txtReportSyncInterval")
        self.gridLayout_3.addWidget(self.txtReportSyncInterval, 0, 1, 1, 1)
        self.tabWidget.addTab(self.tab_3, "")
        self.tab_4 = QtGui.QWidget()
        self.tab_4.setObjectName("tab_4")
        self.gridLayout_4 = QtGui.QGridLayout(self.tab_4)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.txtServerUrl = QtGui.QLineEdit(self.tab_4)
        self.txtServerUrl.setObjectName("txtServerUrl")
        self.gridLayout_4.addWidget(self.txtServerUrl, 0, 1, 1, 1)
        self.label_9 = QtGui.QLabel(self.tab_4)
        self.label_9.setObjectName("label_9")
        self.gridLayout_4.addWidget(self.label_9, 0, 0, 1, 1)
        spacerItem6 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_4.addItem(spacerItem6, 1, 0, 1, 1)
        self.tabWidget.addTab(self.tab_4, "")
        self.verticalLayout.addWidget(self.tabWidget)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem7 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem7)
        self.btnOk = QtGui.QPushButton(Options)
        self.btnOk.setObjectName("btnOk")
        self.horizontalLayout.addWidget(self.btnOk)
        self.btnCancel = QtGui.QPushButton(Options)
        self.btnCancel.setObjectName("btnCancel")
        self.horizontalLayout.addWidget(self.btnCancel)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Options)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Options)
        Options.setTabOrder(self.comboFont, self.txtUsername)
        Options.setTabOrder(self.txtUsername, self.txtPassword)
        Options.setTabOrder(self.txtPassword, self.txtIdletimeout)
        Options.setTabOrder(self.txtIdletimeout, self.txtDatabasedir)
        Options.setTabOrder(self.txtDatabasedir, self.comboLoglevel)
        Options.setTabOrder(self.comboLoglevel, self.txtActivitySyncInterval)
        Options.setTabOrder(self.txtActivitySyncInterval, self.txtReportSyncInterval)
        Options.setTabOrder(self.txtReportSyncInterval, self.txtServerUrl)
        Options.setTabOrder(self.txtServerUrl, self.btnOk)
        Options.setTabOrder(self.btnOk, self.btnCancel)
        Options.setTabOrder(self.btnCancel, self.tabWidget)

    def retranslateUi(self, Options):
        Options.setWindowTitle(QtGui.QApplication.translate("Options", "Ergotime Options", None, QtGui.QApplication.UnicodeUTF8))
        self.txtIdletimeout.setInputMask(QtGui.QApplication.translate("Options", "00000", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Options", "Username", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("Options", "Log Level", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Options", "Font", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("Options", "Database directory", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("Options", "Idle timeout", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("Options", "Password", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QtGui.QApplication.translate("Options", "General", None, QtGui.QApplication.UnicodeUTF8))
        self.label_7.setText(QtGui.QApplication.translate("Options", "Periodic sync interval", None, QtGui.QApplication.UnicodeUTF8))
        self.txtActivitySyncInterval.setInputMask(QtGui.QApplication.translate("Options", "00000", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QtGui.QApplication.translate("Options", "Activity", None, QtGui.QApplication.UnicodeUTF8))
        self.label_8.setText(QtGui.QApplication.translate("Options", "Periodic sync interval", None, QtGui.QApplication.UnicodeUTF8))
        self.txtReportSyncInterval.setInputMask(QtGui.QApplication.translate("Options", "00000", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QtGui.QApplication.translate("Options", "Report", None, QtGui.QApplication.UnicodeUTF8))
        self.label_9.setText(QtGui.QApplication.translate("Options", "Server URL", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QtGui.QApplication.translate("Options", "Network", None, QtGui.QApplication.UnicodeUTF8))
        self.btnOk.setText(QtGui.QApplication.translate("Options", "OK", None, QtGui.QApplication.UnicodeUTF8))
        self.btnCancel.setText(QtGui.QApplication.translate("Options", "Cancel", None, QtGui.QApplication.UnicodeUTF8))


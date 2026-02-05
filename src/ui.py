from PySide6.QtCore import (QCoreApplication, QMetaObject, QRect,
                            Qt)
from PySide6.QtGui import (QAction)
from PySide6.QtWidgets import (QComboBox, QDialogButtonBox, QHBoxLayout, QSizePolicy, QSpacerItem,
                               QVBoxLayout, QWidget)
from PySide6.QtWidgets import (QLabel, QMenu, QMenuBar, QPushButton, QSlider, QStatusBar)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        self.actionCalculate_the_area = QAction(MainWindow)
        self.actionCalculate_the_area.setObjectName(u"actionCalculate_the_area")
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName(u"actionOpen")
        self.actionOpen_Calibration_Image = QAction(MainWindow)
        self.actionOpen_Calibration_Image.setObjectName(u"actionOpen_Calibration_Image")
        self.actionAuto_Gamma_by_area = QAction(MainWindow)
        self.actionAuto_Gamma_by_area.setObjectName(u"actionAuto_Gamma_by_area")
        self.actionConnect_Camera = QAction(MainWindow)
        self.actionConnect_Camera.setObjectName(u"actionConnect_Camera")
        self.actionConnect_cti_file = QAction(MainWindow)
        self.actionConnect_cti_file.setObjectName(u"actionConnect_cti_file")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.pixmap_label = QLabel(self.centralwidget)
        self.pixmap_label.setObjectName(u"pixmap_label")
        self.pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.pixmap_label)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_2 = QLabel(self.centralwidget)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_2.addWidget(self.label_2)

        self.pushButton = QPushButton(self.centralwidget)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setCheckable(True)

        self.horizontalLayout_2.addWidget(self.pushButton)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_4.addWidget(self.label_3)

        self.pushButton_2 = QPushButton(self.centralwidget)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setCheckable(True)

        self.horizontalLayout_4.addWidget(self.pushButton_2)

        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.gamma_label = QLabel(self.centralwidget)
        self.gamma_label.setObjectName(u"gamma_label")

        self.horizontalLayout_5.addWidget(self.gamma_label)

        self.gamma_slider = QSlider(self.centralwidget)
        self.gamma_slider.setObjectName(u"gamma_slider")
        self.gamma_slider.setOrientation(Qt.Orientation.Horizontal)

        self.horizontalLayout_5.addWidget(self.gamma_slider)

        self.verticalLayout.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(250, -1, 250, -1)
        self.apply_countour_button = QPushButton(self.centralwidget)
        self.apply_countour_button.setObjectName(u"apply_countour_button")
        self.apply_countour_button.setCheckable(True)
        self.apply_countour_button.setChecked(False)

        self.horizontalLayout_3.addWidget(self.apply_countour_button)

        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.verticalLayout_2.addLayout(self.verticalLayout)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 23))
        self.menuFunctions = QMenu(self.menubar)
        self.menuFunctions.setObjectName(u"menuFunctions")
        self.menuFIle = QMenu(self.menubar)
        self.menuFIle.setObjectName(u"menuFIle")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFIle.menuAction())
        self.menubar.addAction(self.menuFunctions.menuAction())
        self.menuFunctions.addAction(self.actionCalculate_the_area)
        self.menuFunctions.addSeparator()
        self.menuFunctions.addAction(self.actionAuto_Gamma_by_area)
        self.menuFIle.addAction(self.actionOpen)
        self.menuFIle.addAction(self.actionOpen_Calibration_Image)
        self.menuFIle.addAction(self.actionConnect_Camera)
        self.menuFIle.addSeparator()
        self.menuFIle.addAction(self.actionConnect_cti_file)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)

    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Area Calculator", None))
        self.actionCalculate_the_area.setText(QCoreApplication.translate("MainWindow", u"Calculate the area", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", u"Open", None))
        self.actionOpen_Calibration_Image.setText(
            QCoreApplication.translate("MainWindow", u"Open Calibration Image", None))
        self.actionAuto_Gamma_by_area.setText(QCoreApplication.translate("MainWindow", u"Auto Gamma by area", None))
        self.actionConnect_Camera.setText(QCoreApplication.translate("MainWindow", u"Connect Basic Camera", None))
        self.actionConnect_cti_file.setText(QCoreApplication.translate("MainWindow", u"Connect .cti file", None))
        self.pixmap_label.setText(QCoreApplication.translate("MainWindow", u"TextLabel", None))
        self.label_2.setText("")
        self.pushButton.setText(QCoreApplication.translate("MainWindow", u"AutoGamma1", None))
        self.label_3.setText("")
        self.pushButton_2.setText(QCoreApplication.translate("MainWindow", u"AutoGamma2", None))
        self.gamma_label.setText(QCoreApplication.translate("MainWindow", u"TextLabel", None))
        self.apply_countour_button.setText(QCoreApplication.translate("MainWindow", u"Apply Contour", None))
        self.menuFunctions.setTitle(QCoreApplication.translate("MainWindow", u"Functions", None))
        self.menuFIle.setTitle(QCoreApplication.translate("MainWindow", u"FIle", None))
    # retranslateUi

    def add_snap_button(self):
        self.horizontalLayout_6 = QHBoxLayout()
        self.snap_pushButton = QPushButton('Snap')
        self.snap_pushButton.setCheckable(True)
        self.horizontalLayout_6.setContentsMargins(250, -1, 250, -1)
        self.horizontalLayout_6.addWidget(self.snap_pushButton)

        self.verticalLayout.insertLayout(1, self.horizontalLayout_6)


    def delete_snap_button(self):
        if self.horizontalLayout_6 is not None:
            self.horizontalLayout_6.deleteLater()
            self.snap_pushButton.deleteLater()

class ChooseCameraDialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(247, 290)
        self.verticalLayout_2 = QVBoxLayout(Dialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.comboBox = QComboBox(Dialog)
        self.comboBox.setObjectName(u"comboBox")

        self.verticalLayout.addWidget(self.comboBox)

        self.verticalSpacer = QSpacerItem(30, 31, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        self.buttonBox.setSizePolicy(sizePolicy)
        self.buttonBox.setOrientation(Qt.Orientation.Vertical)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setCenterButtons(True)

        self.horizontalLayout.addWidget(self.buttonBox)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)

    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
    # retranslateUi

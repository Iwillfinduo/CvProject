
from PySide6.QtCore import (QCoreApplication, QMetaObject, QRect,
                            Qt)
from PySide6.QtGui import (QAction)
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QMenu, QMenuBar, QPushButton, QSlider, QStatusBar, QVBoxLayout, QWidget)


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
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayoutWidget = QWidget(self.centralwidget)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(0, 0, 791, 541))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.pixmap_label = QLabel(self.verticalLayoutWidget)
        self.pixmap_label.setObjectName(u"pixmap_label")
        self.pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.pixmap_label)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_2 = QLabel(self.verticalLayoutWidget)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_2.addWidget(self.label_2)

        self.horizontalSlider = QSlider(self.verticalLayoutWidget)
        self.horizontalSlider.setObjectName(u"horizontalSlider")
        self.horizontalSlider.setOrientation(Qt.Orientation.Horizontal)

        self.horizontalLayout_2.addWidget(self.horizontalSlider)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_3 = QLabel(self.verticalLayoutWidget)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_4.addWidget(self.label_3)

        self.horizontalSlider_2 = QSlider(self.verticalLayoutWidget)
        self.horizontalSlider_2.setObjectName(u"horizontalSlider_2")
        self.horizontalSlider_2.setOrientation(Qt.Orientation.Horizontal)

        self.horizontalLayout_4.addWidget(self.horizontalSlider_2)

        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.gamma_label = QLabel(self.verticalLayoutWidget)
        self.gamma_label.setObjectName(u"gamma_label")

        self.horizontalLayout_5.addWidget(self.gamma_label)

        self.gamma_slider = QSlider(self.verticalLayoutWidget)
        self.gamma_slider.setObjectName(u"gamma_slider")
        self.gamma_slider.setOrientation(Qt.Orientation.Horizontal)

        self.horizontalLayout_5.addWidget(self.gamma_slider)

        self.verticalLayout.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(250, -1, 250, -1)
        self.apply_countour_button = QPushButton(self.verticalLayoutWidget)
        self.apply_countour_button.setObjectName(u"apply_countour_button")
        self.apply_countour_button.setCheckable(True)
        self.apply_countour_button.setChecked(False)

        self.horizontalLayout_3.addWidget(self.apply_countour_button)

        self.verticalLayout.addLayout(self.horizontalLayout_3)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 33))
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
        self.menuFIle.addAction(self.actionOpen)
        self.menuFIle.addAction(self.actionOpen_Calibration_Image)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)

    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Thingie", None))
        self.actionCalculate_the_area.setText(QCoreApplication.translate("MainWindow", u"Calculate the area", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", u"Open", None))
        self.actionOpen_Calibration_Image.setText(
            QCoreApplication.translate("MainWindow", u"Open Calibration Image", None))
        self.pixmap_label.setText(QCoreApplication.translate("MainWindow", u"TextLabel", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"TextLabel", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"TextLabel", None))
        self.gamma_label.setText(QCoreApplication.translate("MainWindow", u"TextLabel", None))
        self.apply_countour_button.setText(QCoreApplication.translate("MainWindow", u"Apply Contour", None))
        self.menuFunctions.setTitle(QCoreApplication.translate("MainWindow", u"Functions", None))
        self.menuFIle.setTitle(QCoreApplication.translate("MainWindow", u"FIle", None))
    # retranslateUi

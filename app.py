import os
import sys

import cv2 as cv
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog

from ui import Ui_MainWindow
from utils import OpenCVToQtAdapter

filename = '../data/first/Tv68.bmp'


class ImageViewer(QMainWindow):
    def __init__(self):
        self.filename = filename
        self.image_cv = cv.imread(filename, cv.IMREAD_GRAYSCALE)
        super().__init__()
        self.alpha = 1.0
        self.beta = 1.0
        self.gamma = 1.0
        self.image_init_flag =False
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.gamma_label.setText(str(self.gamma))
        self.ui.gamma_slider.valueChanged.connect(self._slider_move)
        self.ui.actionOpen.triggered.connect(self._open_file)
        self.ui.apply_countour_button.clicked.connect(self.display_image)
        self.display_image()

    def _slider_move(self):
        gamma = self.ui.gamma_slider.value() / 10.0
        self.gamma = gamma
        self.ui.gamma_label.setText(str(gamma))
        self.display_image()

    def _open_file(self):
        filename = QFileDialog.getOpenFileName(self, 'Open file', os.getcwd(),
                                               'Image Files (*.png *.jpg *.bmp)')
        print(filename)
        self.filename = filename[0]
        self.image_cv = cv.imread(self.filename, cv.IMREAD_GRAYSCALE)
        self.display_image()

    def display_image(self):
        """Отображает изображение OpenCV в виджете"""
        cv_img = self.image_cv
        alpha = 1.0  # Simple contrast control
        gamma = self.gamma
        lookUpTable = np.empty((1, 256), np.uint8)
        for i in range(256):
            lookUpTable[0, i] = np.clip(pow(i / 255.0, gamma) * 255.0, 0, 255)
        gamma_img = cv.LUT(cv_img, lookUpTable)
        if self.ui.apply_countour_button.isChecked():
            gamma_img = self._apply_countours(gamma_img)
        pixmap = OpenCVToQtAdapter.convert_cv_to_qt(gamma_img)
        if self.image_init_flag:
            self.ui.pixmap_label.setPixmap(
                pixmap.scaled(self.ui.pixmap_label.width(), self.ui.pixmap_label.height(), Qt.KeepAspectRatio,
                              Qt.SmoothTransformation))
        else:
            self.ui.pixmap_label.setPixmap(pixmap)
        self.image_init_flag = True

    def _apply_countours(self, image):
        temp_image = (255-image)
        contours, hierarchy = cv.findContours(temp_image, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        backtorgb = cv.cvtColor(image, cv.COLOR_GRAY2RGB)
        return cv.drawContours(backtorgb, contours, -1, (255,0,0), 3)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    viewer = ImageViewer()
    viewer.show()

    sys.exit(app.exec())

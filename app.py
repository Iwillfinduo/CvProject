import os
import sys

import cv2 as cv
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox

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
        self.contours = None
        self.image_init_flag = False
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.gamma_label.setText(str(self.gamma))
        self.ui.gamma_slider.valueChanged.connect(self._slider_move)
        self.ui.actionOpen.triggered.connect(self._open_file)
        self.ui.actionCalculate_the_area.triggered.connect(self._calculate_area)
        self.ui.apply_countour_button.clicked.connect(self.display_image)
        self.ui.actionOpen_Calibration_Image.triggered.connect(self._calibrate_area)
        self.display_image()

    def _slider_move(self):
        gamma = self.ui.gamma_slider.value() / 10.0
        self.gamma = gamma
        self.alpha = self.ui.horizontalSlider.value()
        self.beta = self.ui.horizontalSlider_2.value()
        self.ui.gamma_label.setText(str(gamma))
        self.ui.label_2.setText(str(self.alpha))
        self.ui.label_3.setText(str(self.beta))
        self.display_image()

    def _open_file(self):
        filename = QFileDialog.getOpenFileName(self, 'Open file', os.getcwd(),
                                               'Image Files (*.png *.jpg *.bmp)')
        print(filename)
        if filename[0]:
            self.filename = filename[0]
            self.image_cv = cv.imread(self.filename, cv.IMREAD_GRAYSCALE)
            self.display_image()

    def _calibrate_area(self):
        filename = QFileDialog.getOpenFileName(self, 'Open file', os.getcwd(),
                                               'Image Files (*.png *.jpg *.bmp)')
        print(filename)
        if filename[0]:
            image_cv = cv.imread(filename[0], cv.IMREAD_GRAYSCALE)
            length, units = OpenCVToQtAdapter.process_calibration_image(image_cv)
            self.unit_factor = int(units[0])/length
            self.unit_name = units[1]

    def display_image(self):
        """Отображает изображение OpenCV в виджете"""
        cv_img = self.image_cv
        gamma = self.gamma
        lookUpTable = np.empty((1, 256), np.uint8)
        for i in range(256):
            lookUpTable[0, i] = np.clip(pow(i / 255.0, gamma) * 255.0, 0, 255)
        gamma_img = cv.LUT(cv_img, lookUpTable)
        if self.ui.apply_countour_button.isChecked():
            gamma_img = self._apply_contours(gamma_img)
        pixmap = OpenCVToQtAdapter.convert_cv_to_qt(gamma_img)
        if self.image_init_flag:
            self.ui.pixmap_label.setPixmap(
                pixmap.scaled(self.ui.pixmap_label.width(), self.ui.pixmap_label.height(), Qt.KeepAspectRatio,
                              Qt.SmoothTransformation))
        else:
            self.ui.pixmap_label.setPixmap(pixmap)
        self.image_init_flag = True

    def _calculate_area(self):
        if self.contours:
            summ_of_areas = 0
            for contour in self.contours:
                summ_of_areas += cv.contourArea(contour)
            areas_units = summ_of_areas * self.unit_factor
            message_box = QMessageBox()
            message_box.setIcon(QMessageBox.Information)
            message_box.setWindowTitle('Area Calculation')
            message_box.setText(f'Calculated_area: {areas_units:.4f} {self.unit_name} \n {summ_of_areas} px')
            message_box.exec()
        else:
            pass

    def _apply_contours(self, image):
        temp_image = (255 - image)
        _, temp_image = cv.threshold(image, 0., 10., cv.THRESH_OTSU)
        contours, hierarchy = cv.findContours(temp_image, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        print(len(contours))
        self.contours = contours
        backtorgb = cv.cvtColor(image, cv.COLOR_GRAY2RGB)
        return cv.drawContours(backtorgb, contours, -1, (255, 0, 0), 3)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    viewer = ImageViewer()
    viewer.show()

    sys.exit(app.exec())

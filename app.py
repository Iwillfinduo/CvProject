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
        self.gamma = 1.0
        self.first_parameter = 0.7
        self.second_parameter = 0.5
        self.unit_factor = None
        self.contours = None
        self.processed_image = None
        self.image_init_flag = False
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.gamma_label.setText(str(self.gamma))
        self.ui.gamma_slider.valueChanged.connect(self._slider_move)
        self.ui.actionOpen.triggered.connect(self._open_file)
        self.ui.actionCalculate_the_area.triggered.connect(self._calculate_area)
        self.ui.apply_countour_button.clicked.connect(self.display_image)
        self.ui.actionOpen_Calibration_Image.triggered.connect(self._calibrate_area)
        self.ui.pushButton.clicked.connect(self._apply_first_auto_gamma)
        self.ui.pushButton_2.clicked.connect(self._apply_second_auto_gamma)
        self.display_image()

    def _apply_second_auto_gamma(self):
        if self.ui.pushButton_2.isChecked():
            self.ui.pushButton.setChecked(False)
            self._apply_first_auto_gamma()
            self.auto_gamma_flag = True
            self.gamma = OpenCVToQtAdapter.gamma_from_high_percentile(self.image_cv, target=self.second_parameter)
            self.ui.label_3.setText(f"Auto gamma set to {self.gamma:.2f}")
            self.ui.gamma_label.setText(f'{self.gamma:.2f}')
            self.ui.gamma_slider.setValue(int(self.gamma * 10))
        else:
            self.auto_gamma_flag = False
        self.display_image()

    def _apply_first_auto_gamma(self):
        if self.ui.pushButton.isChecked():
            self.ui.pushButton_2.setChecked(False)
            self.auto_gamma_flag = False
            self._apply_second_auto_gamma()
            self.processed_image = OpenCVToQtAdapter.stretch_bright_region(self.image_cv,
                                                                           threshold=self.first_parameter)
        else:
            self.processed_image = None

        self.display_image()

    def _slider_move(self):
        if not self.auto_gamma_flag:
            gamma = self.ui.gamma_slider.value() / 10.0
            self.gamma = gamma
            self.ui.gamma_label.setText(str(gamma))
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
            self.unit_factor = int(units[0]) / length
            self.unit_name = units[1]

    def display_image(self):
        """Отображает изображение OpenCV в виджете"""
        cv_img = self.image_cv
        gamma = self.gamma
        if self.processed_image is None:
            lookUpTable = np.empty((1, 256), np.uint8)
            for i in range(256):
                lookUpTable[0, i] = np.clip(pow(i / 255.0, gamma) * 255.0, 0, 255)
            gamma_img = cv.LUT(cv_img, lookUpTable)
        else:
            gamma_img = self.processed_image
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
            message_box = QMessageBox()
            for contour in self.contours:
                summ_of_areas += cv.contourArea(contour)
            if self.unit_factor:
                areas_units = summ_of_areas * self.unit_factor
                message_box = QMessageBox()
                message_box.setIcon(QMessageBox.Information)
                message_box.setWindowTitle('Area Calculation')
                message_box.setText(f'Calculated_area: {areas_units:.4f} {self.unit_name} \n {summ_of_areas} px')
            else:
                message_box.setIcon(QMessageBox.Information)
                message_box.setWindowTitle('Area Calculation')
                message_box.setText(f'Area are not calibrated,\n {summ_of_areas} px')
            message_box.exec()
        else:
            pass

    def _apply_contours(self, image):
        temp_image = (255 - image)
        _, temp_image = cv.threshold(image, 0., 10., cv.THRESH_OTSU)
        contours, hierarchy = cv.findContours(temp_image, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        print(len(contours))
        self.contours = contours
        back_to_rgb = cv.cvtColor(image, cv.COLOR_GRAY2RGB)
        return cv.drawContours(back_to_rgb, contours, -1, (255, 0, 0), 3)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    viewer = ImageViewer()
    viewer.show()

    sys.exit(app.exec())

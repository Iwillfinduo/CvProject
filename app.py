import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QProgressDialog

from ui import Ui_MainWindow
from utils import OpenCVToQtAdapter, Image

filename = '../data/first/Tv68.bmp'


class ImageViewer(QMainWindow):
    def __init__(self):
        # inner logic calls and variables
        self.filename = filename
        self.image = Image(filename)
        super().__init__()
        self.auto_gamma_flag = False
        self.gamma = 1.0
        self.first_parameter = 0.7
        self.second_parameter = 0.5
        self.unit_factor = None
        self.processed_image = None
        self.image_init_flag = False

        # Ui calls
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.gamma_label.setText(str(self.gamma))
        self.ui.gamma_slider.setMaximum(150)
        self.ui.gamma_slider.valueChanged.connect(self._slider_move)
        self.ui.actionOpen.triggered.connect(self._open_file)
        self.ui.actionCalculate_the_area.triggered.connect(self._calculate_area)
        self.ui.apply_countour_button.clicked.connect(self.display_image)
        self.ui.actionOpen_Calibration_Image.triggered.connect(self._calibrate_area)
        self.ui.pushButton.clicked.connect(self._apply_first_auto_gamma)
        self.ui.pushButton_2.clicked.connect(self._apply_second_auto_gamma)
        self.ui.actionAuto_Gamma_by_area.triggered.connect(self._auto_gamma_by_area)
        self.display_image()

    def _apply_second_auto_gamma(self):
        if self.ui.pushButton_2.isChecked():
            self.ui.pushButton.setChecked(False)
            self._apply_first_auto_gamma()
            self.auto_gamma_flag = True
            self.gamma = self.image.gamma_from_high_percentile(target=self.second_parameter)
            self.ui.label_3.setText(f"Auto gamma set to {self.gamma:.2f}")
            self._update_gamma()
        else:
            self.auto_gamma_flag = False
        self.display_image()

    def _apply_first_auto_gamma(self):
        if self.ui.pushButton.isChecked():
            self.ui.pushButton_2.setChecked(False)
            self.auto_gamma_flag = False
            self._apply_second_auto_gamma()
            self.processed_image = self.image.stretch_bright_region(threshold=self.first_parameter)
        else:
            self.processed_image = None

        self.display_image()

    def _slider_move(self):
        if not self.auto_gamma_flag and self.processed_image is None:
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
            self.image = Image(self.filename)
            self.display_image()

    def _calibrate_area(self):
        filename = QFileDialog.getOpenFileName(self, 'Open file', os.getcwd(),
                                               'Image Files (*.png *.jpg *.bmp)')
        print(filename)
        if filename[0]:
            length, units = OpenCVToQtAdapter.process_calibration_image(filename[0])
            self.unit_factor = int(units[0]) / length
            self.unit_name = units[1]

    def display_image(self):
        """Отображает изображение OpenCV в виджете"""
        if self.processed_image is None:
            gamma_img = self.image.apply_gamma(self.gamma)
        else:
            gamma_img = self.processed_image
        is_contours = False
        if self.ui.apply_countour_button.isChecked():
            gamma_img = gamma_img.apply_contours()
            is_contours = True
        pixmap = gamma_img.get_pixmap(use_contours=is_contours)
        if self.image_init_flag:
            self.ui.pixmap_label.setPixmap(
                pixmap.scaled(self.ui.pixmap_label.width(), self.ui.pixmap_label.height(), Qt.KeepAspectRatio,
                              Qt.SmoothTransformation))
        else:
            self.ui.pixmap_label.setPixmap(pixmap)
        self.image_init_flag = True

    def _calculate_area(self):
        message_box = QMessageBox()
        sum_of_areas, areas_units = self.image.calculate_area(
            self.unit_factor) if self.processed_image is None else self.processed_image.calculate_area(self.unit_factor)
        if areas_units > 0:
            message_box = QMessageBox()
            message_box.setIcon(QMessageBox.Information)
            message_box.setWindowTitle('Area Calculation')
            message_box.setText(f'Calculated_area: {areas_units:.4f} {self.unit_name} \n {sum_of_areas} px')
        elif sum_of_areas >= 0:
            message_box.setIcon(QMessageBox.Information)
            message_box.setWindowTitle('Area Calculation')
            message_box.setText(f'Area are not calibrated,\n {sum_of_areas} px')
        else:
            return
        message_box.exec()

    def _auto_gamma_by_area(self):
        progress_dialog = QProgressDialog()
        progress_dialog.setWindowTitle('Auto gamma')
        progress_dialog.setValue(0)
        progress_dialog.setLabelText('Finding suitable gamma value')
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setMaximum(150)
        progress_dialog.setMinimum(0)
        image = self.image.clone()
        gamma = image.calculate_gamma_from_contour_graph(max_gamma=15,modal_window=progress_dialog)
        self.gamma = gamma
        self._update_gamma()
        self.display_image()
    def _update_gamma(self):
        gamma = self.gamma
        self.ui.gamma_label.setText(f'{self.gamma:.2f}')
        self.ui.gamma_slider.setValue(int(self.gamma * 10))


if __name__ == "__main__":
    app = QApplication(sys.argv)

    viewer = ImageViewer()
    viewer.show()

    sys.exit(app.exec())

import os
import sys
import time

from PySide6.QtCore import Qt, Slot, QTimer, QSize
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QProgressDialog, QWidget, QDialog
from PySide6.QtMultimedia import QCameraDevice, QMediaDevices

from ObjectClasses import Image, VideoThread
from ui import Ui_MainWindow, ChooseCameraDialog
from utils import OpenCVToQtAdapter

filename = 'placeholder.png'


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
        self.thread = None

        # Ui calls
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.gamma_label.setText(str(self.gamma))
        self.ui.gamma_slider.setMaximum(150)
        self.ui.gamma_slider.valueChanged.connect(self._slider_move)
        self.ui.actionOpen.triggered.connect(self._open_file)
        self.ui.actionCalculate_the_area.triggered.connect(self._calculate_area)
        self.ui.apply_countour_button.clicked.connect(self.display_image)
        self.ui.actionConnect_Camera.triggered.connect(self._connect_video_thread)
        self.ui.actionOpen_Calibration_Image.triggered.connect(self._calibrate_area)
        self.ui.pushButton.clicked.connect(self._apply_first_auto_gamma)
        self.ui.pushButton_2.clicked.connect(self._apply_second_auto_gamma)
        self.ui.actionAuto_Gamma_by_area.triggered.connect(self._auto_gamma_by_area)
        self.ui.pixmap_label.setMinimumSize(QSize(200, 200))
        # Don't call display_image() here - wait for the widget to be properly sized

    def showEvent(self, event):
        """Called when the widget is shown - this ensures proper sizing"""
        super().showEvent(event)
        # Use a single-shot timer to ensure the widget is fully laid out
        QTimer.singleShot(100, self.display_image)

    def resizeEvent(self, event):
        """Called when the widget is resized - this ensures proper sizing"""
        self.display_image()

    def _connect_video_thread(self):

        modal = ChooseCameraLogic(parent=self)
        thread_id = modal.get_chosen_camera()
        print(thread_id)
        if thread_id is not None:
            self.ui.add_snap_button()
            self.ui.snap_pushButton.clicked.connect(self._snap_camera)
            if self.thread is not None:
                self.thread.stop()
            self.thread = None
            self.thread = VideoThread(thread_id)
            self.thread.frame_ready.connect(self.display_video_slot)
            self.thread.start()

        print(self.thread)
    def get_filtered_pixmap(self):
        image = self.image
        if self.ui.pushButton.isChecked():
            image = image.stretch_bright_region(threshold=self.first_parameter)

        else:
            image = image.apply_gamma(self.gamma)
        is_contours = False
        if self.ui.apply_countour_button.isChecked():
            image = image.apply_contours()
            is_contours = True
        return image.get_pixmap(use_contours=is_contours)

    @Slot(Image)
    def display_video_slot(self, image):
        if self.thread is None:
            return
        self.image = image
        pixmap = self.get_filtered_pixmap()
        self.ui.pixmap_label.setPixmap(
            pixmap.scaled(self.ui.pixmap_label.width(), self.ui.pixmap_label.height(), Qt.KeepAspectRatio,
                          Qt.SmoothTransformation))

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

    def _snap_camera(self):
        if self.ui.snap_pushButton.isChecked():
            last_image = self.thread.stop()
            self.image = last_image
            pixmap = self.get_filtered_pixmap()
            self.ui.pixmap_label.setPixmap(
                pixmap.scaled(self.ui.pixmap_label.width(), self.ui.pixmap_label.height(), Qt.KeepAspectRatio,
                              Qt.SmoothTransformation))
        else:
            self.thread.start()

    def _open_file(self):
        filename = QFileDialog.getOpenFileName(self, 'Open file', os.getcwd(),
                                               'Image Files (*.png *.jpg *.bmp)')
        print(filename)
        self.ui.delete_snap_button()
        if filename[0]:
            if self.thread is not None:
                self.thread.stop()
                self.thread = None
            self.filename = filename[0]
            self.image = Image(self.filename)
            self.processed_image = None
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

        # Check if the label has proper dimensions before scaling
        if self.ui.pixmap_label.width() > 0 and self.ui.pixmap_label.height() > 0:
            # Always scale the image to fit the label properly
            scaled_pixmap = pixmap.scaled(
                self.ui.pixmap_label.width(),
                self.ui.pixmap_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.ui.pixmap_label.setPixmap(scaled_pixmap)
        else:
            # If label dimensions are not ready, just set the pixmap without scaling
            self.ui.pixmap_label.setPixmap(pixmap)

        self.image_init_flag = True

    def _calculate_area(self):
        message_box = QMessageBox()
        contours = self.image.get_contours()
        sum_of_areas, areas_units = self.image.calculate_area(
            self.unit_factor) if self.processed_image is None else self.processed_image.calculate_area(self.unit_factor)

        if areas_units > 0:
            message_box = QMessageBox()
            message_box.setIcon(QMessageBox.Information)
            message_box.setWindowTitle('Area Calculation')
            message_box.setText(
                f'Calculated_area: {areas_units:.4f} {self.unit_name} \n{sum_of_areas} px \nAmount_of_contours {len(contours)}')
        elif sum_of_areas >= 0:
            message_box.setIcon(QMessageBox.Information)
            message_box.setWindowTitle('Area Calculation')
            message_box.setText(f'Area are not calibrated,\n{sum_of_areas} px \nAmount_of_contours {len(contours)}')
        else:
            return
        message_box.exec()

    def _auto_gamma_by_area(self):
        progress_dialog = QProgressDialog()
        progress_dialog.setWindowTitle('Auto gamma')
        progress_dialog.setValue(0)
        progress_dialog.setLabelText('Finding suitable gamma value')
        progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        progress_dialog.setMaximum(150)
        progress_dialog.setMinimum(0)
        progress_dialog.setCancelButton(None)
        image = self.image.clone()
        gamma = image.calculate_gamma_from_contour_graph_with_std(max_gamma=15, modal_window=progress_dialog)
        self.gamma = gamma
        self._update_gamma()
        self.display_image()

    def _update_gamma(self):
        self.ui.gamma_label.setText(f'{self.gamma:.2f}')
        self.ui.gamma_slider.setValue(int(self.gamma * 10))

class ChooseCameraLogic(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setModal(True)
        self.ui = ChooseCameraDialog()
        self.ui.setupUi(self)
        inputs = QMediaDevices.videoInputs()
        self.ids = []
        for input in inputs:
            self.ui.comboBox.addItem(input.description())
            self.ids.append(int(''.join(filter(str.isdigit, str(input.id().toStdString())))))

        print(self.ids)
        self.choose = None

        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)
        self.exec()


    def accept(self):
        self.choose = self.ids[self.ui.comboBox.currentIndex()]
        self.close()

    def discard(self):
        self.close()

    def get_chosen_camera(self, parent=None):
        return self.choose





if __name__ == "__main__":
    # ТОЧКА ВХОДА ТУТ
    app = QApplication(sys.argv)

    viewer = ImageViewer()
    viewer.show()

    sys.exit(app.exec())

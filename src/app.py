import os
import sys

from PySide6.QtCore import Qt, Slot, QTimer, QSize
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QProgressDialog, QDialog
from PySide6.QtMultimedia import QMediaDevices

from ObjectClasses import Image, VideoThread, HikrobotThread
from ui import Ui_MainWindow, ChooseCameraDialog
from utils import OpenCVToQtAdapter

filename = 'placeholder.png'


class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        # Данные изображения
        self.filename = filename
        self.image = Image(filename)
        self.processed_image = None

        # Параметры обработки
        self.gamma = 1.0
        self.auto_gamma_flag = False
        self.first_parameter = 0.7
        self.second_parameter = 0.5
        self.unit_factor = None
        self.unit_name = None
        self.image_init_flag = False

        # Камера
        self.thread = None
        self._camera_cti_file = None
        self._camera_index = None
        self._is_camera_mode = False  # Режим камеры или файла

        # UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.gamma_label.setText(str(self.gamma))
        self.ui.gamma_slider.setMaximum(150)
        self.ui.gamma_slider.valueChanged.connect(self._slider_move)
        self.ui.actionOpen.triggered.connect(self._open_file)
        self.ui.actionCalculate_the_area.triggered.connect(self._calculate_area)
        self.ui.actionConnect_Camera.triggered.connect(self._connect_video_thread)
        self.ui.actionOpen_Calibration_Image.triggered.connect(self._calibrate_area)
        self.ui.pushButton.toggled.connect(self._apply_first_auto_gamma_toggled)
        self.ui.pushButton_2.toggled.connect(self._apply_second_auto_gamma_toggled)
        self.ui.actionAuto_Gamma_by_area.triggered.connect(self._auto_gamma_by_area)
        self.ui.pixmap_label.setMinimumSize(QSize(200, 200))
        self.ui.actionConnect_cti_file.triggered.connect(self._connect_cti_file)
        self.ui.actionProcess_Image_Array.triggered.connect(self._process_images_array)

        # Контуры: автоматический стоп-кадр только для камеры
        self.ui.apply_countour_button.toggled.connect(self._on_contours_toggled)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, self.display_image)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.display_image()

    # ==================== Обработка контуров ====================

    def _on_contours_toggled(self, checked: bool):
        """Обработка включения/выключения контуров"""
        if self._is_camera_mode:
            # Режим камеры: управляем стоп-кадром
            if checked:
                # Включили контуры -> стоп-кадр
                self._pause_camera()
            else:
                # Выключили контуры -> возобновляем видео
                self._restart_camera()
        self.display_image()

    def _pause_camera(self):
        """Остановка камеры и захват последнего кадра"""
        if self.thread and self.thread.isRunning():
            last_image = self.thread.stop()
            if last_image:
                self.image = last_image
        self.display_image()

    def _check_buttons(self) -> bool:
        return self.ui.apply_countour_button.isChecked() or self.ui.pushButton.isChecked() or self.ui.pushButton_2.isChecked()

    def _restart_camera(self):
        """Перезапуск камеры"""
        if not self._check_buttons():
            if self._camera_cti_file is not None:
                # Hikrobot камера
                self._start_hikrobot_camera()
            elif self._camera_index is not None:
                # Обычная камера
                self._start_video_camera()

    def _start_hikrobot_camera(self):
        """Запуск Hikrobot камеры"""
        if self.thread:
            if self.thread.isRunning():
                self.thread.stop()
            self.thread = None

        self.thread = HikrobotThread(self._camera_cti_file, camera_index=self._camera_index)
        self.thread.error_occurred.connect(lambda msg: print(f"Error: {msg}"))
        self.thread.frame_ready.connect(self.display_video_slot)
        self.thread.start()

    def _start_video_camera(self):
        """Запуск обычной камеры"""
        if self.thread:
            if self.thread.isRunning():
                self.thread.stop()
            self.thread = None

        self.thread = VideoThread(self._camera_index)
        self.thread.frame_ready.connect(self.display_video_slot)
        self.thread.start()

    # ==================== Подключение камер ====================

    def _connect_cti_file(self):
        """Подключение Hikrobot камеры"""
        filename = QFileDialog.getOpenFileName(self, 'Open file', '/', 'Cti File (*.cti)')

        if not filename[0]:
            return

        devices = HikrobotThread.get_devices(filename[0])
        print(devices)

        if not devices:
            print("No devices found")
            return

        ids = [int(device.split(':')[0].split()[1]) for device in devices]
        models = [device.split(':')[1] for device in devices]
        modal = ChooseCameraLogic(parent=self, inputs={'ids': ids, 'names': models})
        thread_id = modal.get_chosen_camera()

        if thread_id is not None:
            # Останавливаем предыдущий поток
            if self.thread is not None:
                self.thread.stop()

            # Сохраняем параметры камеры
            self._camera_cti_file = filename[0]
            self._camera_index = thread_id
            self._is_camera_mode = True

            # Сбрасываем контуры
            self.ui.apply_countour_button.setChecked(False)

            # Запускаем камеру
            self._start_hikrobot_camera()

    def _connect_video_thread(self):
        """Подключение обычной камеры"""
        modal = ChooseCameraLogic(parent=self)
        thread_id = modal.get_chosen_camera()

        if thread_id is not None:
            # Останавливаем предыдущий поток
            if self.thread is not None:
                self.thread.stop()

            # Сохраняем параметры камеры
            self._camera_cti_file = None
            self._camera_index = thread_id
            self._is_camera_mode = True

            # Сбрасываем контуры
            self.ui.apply_countour_button.setChecked(False)

            # Запускаем камеру
            self._start_video_camera()

    # ==================== Отображение ====================

    @Slot(object)
    def display_video_slot(self, image):
        """Отображение кадра с камеры"""
        if self.thread is None:
            return

        # Игнорируем кадры если контуры включены (мы на стоп-кадре)
        if self.ui.apply_countour_button.isChecked():
            return

        self.image = image
        pixmap = self._get_pixmap(apply_contours=False)
        self._set_pixmap(pixmap)

    def display_image(self):
        """Отображает изображение (файл или стоп-кадр)"""
        if self.image is None:
            return

        apply_contours = self.ui.apply_countour_button.isChecked()
        pixmap = self._get_pixmap(apply_contours=apply_contours)
        self._set_pixmap(pixmap)
        self.image_init_flag = True

    def _get_pixmap(self, apply_contours: bool):
        """Получение pixmap с применением фильтров"""
        # Выбираем базовое изображение
        if self.ui.pushButton.isChecked():
            # Режим stretch_bright_region
            image = self.image.stretch_bright_region(threshold=self.first_parameter)
        elif self.processed_image is not None:
            image = self.processed_image
        else:
            image = self.image.apply_gamma(self.gamma)

        # Применяем контуры если нужно
        if apply_contours:
            image = image.apply_contours()

        return image.get_pixmap(use_contours=apply_contours)

    def _set_pixmap(self, pixmap):
        """Установка pixmap с масштабированием"""
        label = self.ui.pixmap_label
        if label.width() > 0 and label.height() > 0:
            scaled = pixmap.scaled(
                label.width(),
                label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            label.setPixmap(scaled)
        else:
            label.setPixmap(pixmap)

    # ==================== Открытие файла ====================

    def _open_file(self):
        """Открытие файла изображения"""
        filename = QFileDialog.getOpenFileName(
            self, 'Open file', os.getcwd(),
            'Image Files (*.png *.jpg *.bmp)'
        )

        if filename[0]:
            # Останавливаем камеру
            if self.thread is not None:
                self.thread.stop()
                self.thread = None

            # Переключаемся в режим файла
            self._is_camera_mode = False
            self._camera_cti_file = None
            self._camera_index = None

            # Загружаем изображение
            self.filename = filename[0]
            self.image = Image(self.filename)
            self.processed_image = None

            self.display_image()

    # ==================== Остальные методы ====================

    def _slider_move(self):
        if not self.auto_gamma_flag and self.processed_image is None:
            gamma = self.ui.gamma_slider.value() / 10.0
            self.gamma = gamma
            self.ui.gamma_label.setText(str(gamma))
        self.display_image()

    def _apply_second_auto_gamma_toggled(self, checked: bool):
        if self._is_camera_mode:
            if checked:
                self._pause_camera()

            else:
                self._restart_camera()

        if checked:
            self.ui.pushButton.setChecked(False)
            self.auto_gamma_flag = True
            self.gamma = self.image.gamma_from_high_percentile(target=self.second_parameter)
            self.ui.label_3.setText(f"Auto gamma set to {self.gamma:.2f}")
            self._update_gamma()
        else:
            self._restart_camera()
            self.auto_gamma_flag = False
        self.display_image()

    def _apply_first_auto_gamma_toggled(self, checked: bool):
        if self._is_camera_mode:
            if checked:
                self._pause_camera()
            else:
                self._restart_camera()

        if checked:
            self.ui.pushButton_2.setChecked(False)
            self.auto_gamma_flag = False
            self.processed_image = self.image.stretch_bright_region(threshold=self.first_parameter)
        else:
            self.processed_image = None
        self.display_image()

    def _calibrate_area(self):
        filename = QFileDialog.getOpenFileName(
            self, 'Open file', os.getcwd(),
            'Image Files (*.png *.jpg *.bmp)'
        )
        if filename[0]:
            length, units = OpenCVToQtAdapter.process_calibration_image(filename[0])
            self.unit_factor = int(units[0]) / length
            self.unit_name = units[1]

    def _process_images_array(self):
        """Пакетная обработка изображений с автогаммой и сохранением результатов в CSV"""
        import csv
        from datetime import datetime

        filenames, _ = QFileDialog.getOpenFileNames(
            self,
            'Select Images',
            os.getcwd(),
            'Image Files (*.png *.jpg *.bmp)'
        )

        if not filenames:
            return

        csv_path, _ = QFileDialog.getSaveFileName(
            self,
            'Save Results',
            os.path.join(os.getcwd(), f'results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'),
            'CSV Files (*.csv)'
        )

        if not csv_path:
            return

        progress = QProgressDialog('Processing images...', 'Cancel', 0, len(filenames), self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle('Batch Processing')

        results = []

        for i, filename in enumerate(filenames):
            if progress.wasCanceled():
                break

            progress.setLabelText(f'Processing {os.path.basename(filename)}...')
            progress.setValue(i)

            # Загрузка изображения
            temp_image = Image(filename)

            gamma = temp_image.calculate_gamma_from_contour_graph_with_std(max_gamma=15, modal_window=None)
            temp_image = temp_image.apply_gamma(gamma)

            # Расчет площади
            sum_of_areas, areas_units = temp_image.calculate_area(self.unit_factor)
            contours = temp_image.get_contours()

            results.append({
                'filename': os.path.basename(filename),
                'gamma': gamma,
                'area_px': sum_of_areas,
                'area_units': areas_units if self.unit_factor else 0,
                'unit_name': self.unit_name or 'N/A',
                'contours_count': len(contours)
            })

        progress.setValue(len(filenames))

        if results:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['filename', 'gamma', 'area_px', 'area_units', 'unit_name', 'contours_count']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                writer.writerows(results)

            QMessageBox.information(
                self,
                'Success',
                f'Processed {len(results)} images\nResults saved to:\n{csv_path}'
            )

    def _calculate_area(self):
        message_box = QMessageBox()
        contours = self.image.get_contours()

        if self.processed_image is None:
            sum_of_areas, areas_units = self.image.calculate_area(self.unit_factor)
        else:
            sum_of_areas, areas_units = self.processed_image.calculate_area(self.unit_factor)

        if areas_units > 0:
            message_box.setIcon(QMessageBox.Information)
            message_box.setWindowTitle('Area Calculation')
            message_box.setText(
                f'Calculated_area: {areas_units:.4f} {self.unit_name}\n'
                f'{sum_of_areas} px\nAmount_of_contours {len(contours)}'
            )
        elif sum_of_areas >= 0:
            message_box.setIcon(QMessageBox.Information)
            message_box.setWindowTitle('Area Calculation')
            message_box.setText(
                f'Area are not calibrated,\n{sum_of_areas} px\n'
                f'Amount_of_contours {len(contours)}'
            )
        else:
            return
        message_box.exec()

    def _auto_gamma_by_area(self):
        if self._is_camera_mode:
            self._pause_camera()
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
        if self._is_camera_mode:
            self._restart_camera()
        self.display_image()

    def _update_gamma(self):
        self.ui.gamma_label.setText(f'{self.gamma:.2f}')
        self.ui.gamma_slider.setValue(int(self.gamma * 10))

    def closeEvent(self, event):
        """Закрытие приложения"""
        if self.thread:
            self.thread.stop()
        event.accept()


class ChooseCameraLogic(QDialog):
    def __init__(self, parent=None, inputs: dict = None):
        super().__init__(parent=parent)
        self.setModal(True)
        self.ui = ChooseCameraDialog()
        self.ui.setupUi(self)
        self.ids = []

        if inputs is None:
            inputs = QMediaDevices.videoInputs()
            for input in inputs:
                self.ui.comboBox.addItem(input.description())
                self.ids.append(int(''.join(filter(str.isdigit, str(input.id().toStdString())))))
        else:
            self.ids = inputs['ids']
            self.ui.comboBox.addItems(inputs['names'])

        self.choose = None
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)
        self.exec()

    def accept(self):
        self.choose = self.ids[self.ui.comboBox.currentIndex()]
        self.close()

    def discard(self):
        self.close()

    def get_chosen_camera(self):
        return self.choose


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ImageViewer()
    viewer.show()
    sys.exit(app.exec())

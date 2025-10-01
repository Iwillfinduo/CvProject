from typing import Optional

import cv2
import cv2 as cv
import numpy as np
from PySide6.QtCore import QThread, Signal
from harvesters.core import Harvester
from utils import OpenCVToQtAdapter



class Image:
    '''Класс для удобного взаимодействия с изображением
     и изменения его параметров без создания высокой связности
     QT приложения(теперь QT App делает 0 вызовов к opencv)'''

    def __init__(self, image_path, image=None):
        if image is None:
            image = cv.imread(image_path, cv.IMREAD_GRAYSCALE)
        self.image = image
        self.image_path = image_path
        self.contours = None
        self.processed_image = None
        self.image_with_contours = None

    # Getters, setters and simple staff:
    def get_image(self):
        return self.image

    def get_processed_image(self):
        return self.processed_image

    def get_image_with_contours(self):
        return self.image_with_contours

    def get_contours(self):
        if self.contours is None:
            self.apply_contours()
        return self.contours

    def clone(self):
        return Image(image_path=self.image_path, image=self.image)

    def open_image(self, filename):
        self.image_path = filename
        self.image = cv.imread(self.image_path, cv.IMREAD_GRAYSCALE)
        return self.image

    # Meaningful functions
    def apply_gamma(self, gamma):
        lookUpTable = np.empty((1, 256), np.uint8)
        for i in range(256):
            lookUpTable[0, i] = np.clip(pow(i / 255.0, gamma) * 255.0, 0, 255)
        gamma_img = cv.LUT(self.image, lookUpTable)
        self.processed_image = gamma_img
        self.is_applied_contours = False
        return self

    def apply_contours(self):
        # FIXED: ERROR WHILE CHANGING GAMMA IF CONTOURS ARE APPLIED
        if self.processed_image is None:
            processed_image = self.image
        else:
            processed_image = self.processed_image
        _, temp_image = cv.threshold(processed_image, 0., 10., cv.THRESH_OTSU)
        contours, hierarchy = cv.findContours(temp_image, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        # print(len(contours))
        self.contours = contours
        back_to_rgb = cv.cvtColor(processed_image, cv.COLOR_GRAY2RGB)
        self.image_with_contours = cv.drawContours(back_to_rgb, contours, -1, (255, 0, 0), 3)
        return self

    def calculate_area(self, unit_factor=None):
        if self.contours:
            summ_of_areas = 0
            areas_in_units = -1
            for contour in self.contours:
                summ_of_areas += cv.contourArea(contour)
            if unit_factor:
                areas_in_units = summ_of_areas * (unit_factor) ** 2
            return summ_of_areas, areas_in_units
        else:
            return -1, -1

    def get_pixmap(self, use_processed=True, use_contours=True):
        if use_contours and self.contours:
            return OpenCVToQtAdapter.convert_cv_to_qt(self.image_with_contours)
        if use_processed and self.processed_image is not None:
            return OpenCVToQtAdapter.convert_cv_to_qt(self.processed_image)
        return OpenCVToQtAdapter.convert_cv_to_qt(self.image)

    def gamma_from_high_percentile(self, top_percent=0.001, target=0.6):
        norm = self.image / 255.0
        sorted_vals = np.sort(norm.flatten())
        top_k = max(1, int(len(sorted_vals) * top_percent))
        bright_avg = np.mean(sorted_vals[-top_k:])
        gamma = np.log(target) / np.log(bright_avg)
        return np.clip(gamma, 0.5, 10.0)

    def stretch_bright_region(self, threshold=0.85):
        gray = self.image / 255.0
        stretched = np.clip((gray - threshold) / (1.0 - threshold), 0, 1)
        return Image(self.image_path, (stretched * 255).astype(np.uint8))

    def _calculate_gamma_from_contour_graph(self, min_gamma=1.0, max_gamma=10.0, area_difference_coefficient=10 ** 6,
                                            modal_window=None):
        # DEPRECATED
        prev_area = 0.0
        num = 0
        gamma = min_gamma
        while gamma <= max_gamma:
            self.apply_gamma(gamma)
            contour_img = self.apply_contours()
            current_area, _ = contour_img.calculate_area()
            if prev_area - current_area > area_difference_coefficient:
                if modal_window is not None:
                    modal_window.setValue(100)
                return gamma + 0.1
            if modal_window is not None:
                modal_window.setValue(num)
            # print(prev_area - current_area, gamma)
            prev_area = current_area
            num += 1
            gamma += 0.1
        return min_gamma

    def calculate_gamma_from_contour_graph(self, min_gamma=1.0, max_gamma=10.0, area_difference_coefficient=20,
                                           modal_window=None):
        # DEPRECATED
        prev_area = 0.0
        num = 0
        gamma = min_gamma
        while gamma <= max_gamma:
            self.apply_gamma(gamma)
            contour_img = self.apply_contours()
            current_area, _ = contour_img.calculate_area()
            if prev_area / current_area > area_difference_coefficient:
                if modal_window is not None:
                    modal_window.setValue(100)
                return gamma + 0.1
            if modal_window is not None:
                modal_window.setValue(num)
            # print(prev_area/current_area, gamma)
            prev_area = current_area
            num += 1
            gamma += 0.1
        return min_gamma

    def calculate_gamma_from_contour_graph_with_std(self, min_gamma=1.0, max_gamma=10.0, area_difference_coefficient=20,
                                                    modal_window=None):
        '''Предподсчитывает все значения площадей в зависимости от гаммы
         и ищет максимальное стандартное квадратичное отклонение окна'''
        num = 0
        gamma = min_gamma
        areas = []
        while gamma <= max_gamma:
            self.apply_gamma(gamma)
            contour_img = self.apply_contours()
            current_area, _ = contour_img.calculate_area()
            areas.append(current_area)
            # print(prev_area/current_area, gamma)
            num += 1
            if modal_window is not None:
                modal_window.setValue(num * 100 / ((max_gamma - min_gamma) / 0.1))
            gamma += 0.1
        return min_gamma + 0.1 * OpenCVToQtAdapter.find_std_deviation(areas)


class VideoThread(QThread):
    frame_ready = Signal(Image)

    def __init__(self, video_source=0):
        super().__init__()
        self.video_source = video_source
        self.running = False

    def run(self):
        cap = cv2.VideoCapture(self.video_source)
        self.cap = cap
        if not cap.isOpened():
            raise RuntimeError('Cannot open video source')
        self.running = True
        while self.running:
            ret, frame = cap.read()
            if ret:
                gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
                image = Image('', gray)
                self.frame_ready.emit(image)
            else:
                print("can't read video source frame")
                break
        ret, frame = self.cap.read()
        if ret:
            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            self.last_image = Image('', gray)
        cap.release()

    def stop(self):
        self.running = False
        self.wait()
        last_image = self.last_image
        self.last_image = None
        return last_image


# UNTESTED
class HikrobotThread(QThread):
    frame_ready = Signal(Image)  # OpenCV image as custom class (grayscale)

    def __init__(self, cti_file: Optional[str] = None, camera_index: int = 0):
        super().__init__()
        self.cti_file = cti_file
        self.camera_index = camera_index
        self.running = False
        self.harvester = None
        self.ia = None
        self.last_frame = None

    def run(self):
        try:
            self.harvester = Harvester()

            if self.cti_file:
                self.harvester.add_file(self.cti_file)
            else:
                self.harvester.add_file('/opt/mvIMPACT_Acquire/lib/x86_64/mvGenTLProducer.cti')

            self.harvester.update()

            if len(self.harvester.device_info_list) == 0:
                raise RuntimeError('Cannot open camera - no devices found')

            self.ia = self.harvester.create(self.camera_index)
            self.ia.start()

            self.running = True
            while self.running:
                with self.ia.fetch(timeout=1.0) as buffer:
                    component = buffer.payload.components[0]
                    frame = component.data.reshape(component.height, component.width)

                    # Конвертация в черно-белое
                    gray = self._convert_to_grayscale(frame, component.data_format)
                    image = Image('', gray)
                    self.frame_ready.emit(image)

        except Exception as e:
            print(f"Camera error: {e}")
        finally:
            # Захватываем последний кадр перед освобождением ресурсов
            try:
                if self.ia:
                    with self.ia.fetch_buffer(timeout=1.0) as buffer:
                        component = buffer.payload.components[0]
                        frame = component.data.reshape(component.height, component.width)
                        gray = self._convert_to_grayscale(frame, component.data_format)
                        self.last_frame = gray
            except:
                self.last_frame = None

            self._cleanup()

    def _convert_to_grayscale(self, frame: np.ndarray, data_format: str) -> np.ndarray:
        """Конвертация кадра в черно-белое"""
        if len(frame.shape) == 2:  # Уже монохромное
            return frame
        elif data_format == 'BayerRG8':
            bgr_frame = cv2.cvtColor(frame, cv2.COLOR_BAYER_RG2BGR)
            return cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
        elif len(frame.shape) == 3:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            return frame.astype(np.uint8)

    def _cleanup(self):
        """Очистка ресурсов"""
        if self.ia:
            try:
                self.ia.stop_image_acquisition()
                self.ia.destroy()
            except Exception as e:
                print(f"Camera error: {e}")
        if self.harvester:
            try:
                self.harvester.reset()
            except Exception as e:
                print(f"Camera error: {e}")

    def stop(self):
        """Остановка потока и возврат последнего кадра"""
        self.running = False
        self.wait()
        last_frame = self.last_frame
        self.last_frame = None
        return last_frame

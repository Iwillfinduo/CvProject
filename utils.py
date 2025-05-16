import numpy as np
import cv2 as cv
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt
import pytesseract


class OpenCVToQtAdapter:
    @staticmethod
    def convert_cv_to_qt(cv_img: np.ndarray, swap_rgb=True, mirror=False) -> QPixmap:
        """
        Конвертирует изображение OpenCV в QPixmap для отображения в PySide6

        Параметры:
            cv_img (numpy.ndarray): Изображение в формате OpenCV (BGR)
            swap_rgb (bool): Если True, меняет каналы BGR на RGB (по умолчанию True)
            mirror (bool): Если True, зеркально отражает изображение по горизонтали

        Возвращает:
            QPixmap: Изображение, готовое для отображения в PySide6
        """
        # Конвертируем цветовое пространство при необходимости
        if swap_rgb and len(cv_img.shape) == 3 and cv_img.shape[2] == 3:
            cv_img = cv.cvtColor(cv_img, cv.COLOR_BGR2RGB)

        # Зеркальное отражение при необходимости
        if mirror:
            cv_img = cv.flip(cv_img, 1)

        # Определяем формат QImage в зависимости от типа изображения
        if len(cv_img.shape) == 2:
            # Ч/б изображение
            h, w = cv_img.shape
            qt_format = QImage.Format_Grayscale8
            bytes_per_line = w
        elif cv_img.shape[2] == 3:
            # Цветное изображение (RGB)
            h, w, _ = cv_img.shape
            qt_format = QImage.Format_RGB888
            bytes_per_line = w * 3
        elif cv_img.shape[2] == 4:
            # Изображение с альфа-каналом (RGBA)
            h, w, _ = cv_img.shape
            qt_format = QImage.Format_RGBA8888
            bytes_per_line = w * 4
        else:
            raise ValueError("Неподдерживаемый формат изображения")

        # Создаем QImage и преобразуем в QPixmap
        q_img = QImage(cv_img.data, w, h, bytes_per_line, qt_format)
        return QPixmap.fromImage(q_img)

    @staticmethod
    def process_calibration_image(image_path):
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        image = cv.imread(image_path, cv.IMREAD_GRAYSCALE)
        height, width = image.shape

        # Обрезаем нижние 10% и правые 32% изображения
        cropped = image[int(height * 0.9):height, int(width * 0.68):width]

        # Бинаризация
        _, thresh = cv.threshold(cropped, 200, 255, cv.THRESH_BINARY)

        # Ищем контуры
        contours, _ = cv.findContours(thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

        max_length = 0  # Максимальная длина стороны

        for cnt in contours:
            rect = cv.minAreaRect(cnt)
            w, h = rect[1]

            if w > max_length:
                max_length = w
        text = pytesseract.image_to_string(thresh)

        return max_length, text.split()[0:2]

    @staticmethod
    def auto_gamma_mean(gray_image):
        mean = np.mean(gray_image)
        gamma = np.log(128) / np.log(mean + 1e-7)  # Стремимся к средней яркости 128
        return gamma

    @staticmethod
    def gamma_from_high_percentile(gray_image, top_percent=0.001, target=0.6):
        norm = gray_image / 255.0
        sorted_vals = np.sort(norm.flatten())
        top_k = max(1, int(len(sorted_vals) * top_percent))
        bright_avg = np.mean(sorted_vals[-top_k:])
        gamma = np.log(target) / np.log(bright_avg)
        return np.clip(gamma, 0.5, 10.0)

    @staticmethod
    def stretch_bright_region(image, threshold=0.85):
        gray = image / 255.0
        stretched = np.clip((gray - threshold) / (1.0 - threshold), 0, 1)
        return (stretched * 255).astype(np.uint8)


class Image:
    def __init__(self, image_path, image = None):
        if image is None:
            image = cv.imread(image_path, cv.IMREAD_GRAYSCALE)
        self.image = image
        self.image_path = image_path
        self.contours = None
        self.processed_image = None
        self.image_with_contours = None


    def open_image(self, filename):
        self.image_path = filename
        self.image = cv.imread(self.image_path, cv.IMREAD_GRAYSCALE)
        return self.image

    def apply_gamma(self, gamma):
        lookUpTable = np.empty((1, 256), np.uint8)
        for i in range(256):
            lookUpTable[0, i] = np.clip(pow(i / 255.0, gamma) * 255.0, 0, 255)
        gamma_img = cv.LUT(self.image, lookUpTable)
        self.processed_image = gamma_img
        self.is_applied_contours = False
        return self

    def apply_contours(self):
        #FIXED: ERROR WHILE CHANGING GAMMA IF CONTOURS ARE APPLIED
        if self.processed_image is None:
            processed_image = self.image
        else:
            processed_image = self.processed_image
        _, temp_image = cv.threshold(processed_image, 0., 10., cv.THRESH_OTSU)
        contours, hierarchy = cv.findContours(temp_image, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        #print(len(contours))
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
                areas_in_units = summ_of_areas * unit_factor
            return summ_of_areas, areas_in_units
        else:
            return -1, -1

    def get_image(self):
        return self.image
    def get_processed_image(self):
        return self.processed_image
    def get_image_with_contours(self):
        return self.image_with_contours

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
        return Image(self.image_path,(stretched * 255).astype(np.uint8))









import os
import sys

import cv2 as cv
import numpy as np
import pytesseract
from PySide6.QtGui import QImage, QPixmap


class OpenCVToQtAdapter:
    '''Статический класс с вспомогательными статическими функциями'''
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
        pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD").encode('unicode_escape').decode()
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
        if sys.platform  == 'linux':
            text_thresh = thresh.copy()
            text_thresh = cv.bitwise_not(text_thresh)
        else:
            text_thresh = thresh
        text = pytesseract.image_to_string(text_thresh, lang='eng')
        print(text)
        out_text = []
        for part in text.split():
            if part.isdigit():
                out_text.append(part)
            elif len(out_text) > 0:
                out_text.append(part)
                break
        return max_length, out_text

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

    @staticmethod
    def find_std_deviation(y, window=5):
        std_dev = []
        max_std_index = 0
        max_std_value = float("-inf")
        for i in range(len(y) - window):
            segment = y[i:i + window]
            deviation = np.std(segment)
            if deviation > max_std_value:
                max_std_index = i
                max_std_value = deviation
            std_dev.append((np.std(segment)))

        print(std_dev)

        return max_std_index + window
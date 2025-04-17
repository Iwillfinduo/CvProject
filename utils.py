import numpy as np
import cv2
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt


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
            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)

        # Зеркальное отражение при необходимости
        if mirror:
            cv_img = cv2.flip(cv_img, 1)

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
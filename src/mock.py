import numpy as np
import cv2
from typing import Optional, List, Dict, Any
from PySide6.QtCore import QThread, Signal
import time
import random

from ObjectClasses import Image

class MockHikrobotThread(QThread):
    frame_ready = Signal(Image)  # Эмуляция сигнала Image

    def __init__(self, cti_file: Optional[str] = None, camera_index: int = 0):
        super().__init__()
        self.cti_file = cti_file
        self.camera_index = camera_index
        self.running = False
        self.last_frame = None
        self.width = 640
        self.height = 480
        self.fps = 30
        self.frame_count = 0

        # Параметры для генерации тестовых изображений
        self.test_patterns = ['chessboard', 'gradient', 'circles', 'noise', 'color_bars']
        self.current_pattern = 'gradient'

    @staticmethod
    def get_devices(cti_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Возвращает список эмулированных устройств
        """
        devices = [
            {
                'index': 0,
                'model': 'Mock-Camera-1000',
                'vendor': 'Hikrobot-Emulator',
                'serial_number': 'MOCK001'
            },
            {
                'index': 1,
                'model': 'Mock-Camera-2000',
                'vendor': 'Hikrobot-Emulator',
                'serial_number': 'MOCK002'
            },
            {
                'index': 2,
                'model': 'Mock-Camera-3000',
                'vendor': 'Hikrobot-Emulator',
                'serial_number': 'MOCK003'
            }
        ]
        return devices

    def set_test_pattern(self, pattern: str):
        """Установка типа тестового изображения"""
        if pattern in self.test_patterns:
            self.current_pattern = pattern

    def _generate_test_image(self) -> np.ndarray:
        """Генерация тестового изображения"""
        if self.current_pattern == 'chessboard':
            return self._generate_chessboard()
        elif self.current_pattern == 'gradient':
            return self._generate_gradient()
        elif self.current_pattern == 'circles':
            return self._generate_circles()
        elif self.current_pattern == 'noise':
            return self._generate_noise()
        elif self.current_pattern == 'color_bars':
            return self._generate_color_bars()
        else:
            return self._generate_chessboard()

    def _generate_chessboard(self) -> np.ndarray:
        """Генерация шахматной доски"""
        cell_size = 40
        img = np.zeros((self.height, self.width), dtype=np.uint8)

        for i in range(0, self.height, cell_size):
            for j in range(0, self.width, cell_size):
                if (i // cell_size + j // cell_size) % 2 == 0:
                    img[i:i + cell_size, j:j + cell_size] = 255

        # Добавляем движущийся объект для имитации изменений
        size = 20 + int(15 * np.sin(self.frame_count * 0.1))
        x = self.width // 2 + int(100 * np.sin(self.frame_count * 0.05))
        y = self.height // 2 + int(80 * np.cos(self.frame_count * 0.05))
        cv2.rectangle(img, (x, y), (x + size, y + size), 128, -1)

        return img

    def _generate_gradient(self) -> np.ndarray:
        """Генерация градиента"""
        x = np.linspace(0, 255, self.width)
        y = np.linspace(0, 255, self.height)
        X, Y = np.meshgrid(x, y)

        # Динамический градиент
        phase = self.frame_count * 0.02
        img = (128 + 127 * np.sin(X * 0.01 + phase) * np.cos(Y * 0.01 + phase))
        return img.astype(np.uint8)

    def _generate_circles(self) -> np.ndarray:
        """Генерация концентрических кругов"""
        img = np.zeros((self.height, self.width), dtype=np.uint8)
        center_x, center_y = self.width // 2, self.height // 2

        # Движущийся центр
        offset_x = int(50 * np.sin(self.frame_count * 0.03))
        offset_y = int(50 * np.cos(self.frame_count * 0.03))

        for i in range(1, 10):
            radius = i * 30
            color = 255 if i % 2 == 0 else 128
            cv2.circle(img, (center_x + offset_x, center_y + offset_y),
                       radius, color, 3)

        return img

    def _generate_noise(self) -> np.ndarray:
        """Генерация шума с движущимися паттернами"""
        img = np.random.randint(0, 255, (self.height, self.width), dtype=np.uint8)

        # Добавляем структурированный шум
        for i in range(5):
            x = int(self.width * np.random.random())
            y = int(self.height * np.random.random())
            w = int(50 + 30 * np.sin(self.frame_count * 0.1 + i))
            h = int(50 + 30 * np.cos(self.frame_count * 0.1 + i))
            cv2.rectangle(img, (x, y), (x + w, y + h), 200, -1)

        return img

    def _generate_color_bars(self) -> np.ndarray:
        """Генерация цветных полос (конвертируемых в grayscale)"""
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        bar_width = self.width // 8

        colors = [
            (255, 0, 0),  # Red
            (0, 255, 0),  # Green
            (0, 0, 255),  # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
            (255, 255, 255),  # White
            (0, 0, 0)  # Black
        ]

        # Сдвигаем полосы для анимации
        shift = int(self.frame_count * 2) % bar_width

        for i, color in enumerate(colors):
            x_start = i * bar_width - shift
            x_end = (i + 1) * bar_width - shift
            if x_end > 0 and x_start < self.width:
                x_start_clip = max(0, x_start)
                x_end_clip = min(self.width, x_end)
                img[:, x_start_clip:x_end_clip] = color

        # Конвертируем в grayscale как в оригинальном классе
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def run(self):
        """Основной цикл эмуляции камеры"""
        self.running = True
        frame_time = 1.0 / self.fps

        try:
            while self.running:
                start_time = time.time()

                # Генерируем тестовое изображение
                frame = self._generate_test_image()
                self.last_frame = frame
                self.frame_count += 1


                image = Image('', frame)
                self.frame_ready.emit(image)

                # Поддерживаем постоянный FPS
                processing_time = time.time() - start_time
                sleep_time = max(0, frame_time - processing_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except Exception as e:
            print(f"Mock camera error: {e}")
        finally:
            self.running = False

    def stop(self):
        """Остановка эмуляции"""
        self.running = False
        self.wait()
        last_frame = self.last_frame
        self.last_frame = None
        return last_frame

    def set_resolution(self, width: int, height: int):
        """Установка разрешения"""
        self.width = width
        self.height = height

    def set_fps(self, fps: int):
        """Установка FPS"""
        self.fps = max(1, fps)

    def simulate_error(self):
        """Имитация ошибки камеры (для тестирования)"""
        self.running = False


# Класс-обертка для совместимости с оригинальным интерфейсом
class HikrobotThread(MockHikrobotThread):
    """
    Совместимый класс, который можно использовать вместо оригинального HikrobotThread
    """

    def __init__(self, cti_file: Optional[str] = None, camera_index: int = 0):
        super().__init__(cti_file, camera_index)

    # Наследуем все методы от MockHikrobotThread
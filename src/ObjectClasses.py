from dataclasses import dataclass
from typing import Optional, List, Tuple

import cv2
import cv2 as cv
import numpy as np
from PySide6.QtCore import QThread, Signal, QMutex, QMutexLocker
from harvesters.core import Harvester
from utils import OpenCVToQtAdapter


@dataclass
class CameraParams:
    """Параметры камеры"""
    exposure: float = 10000.0  # мкс
    gain: float = 0.0  # дБ
    frame_rate: float = 30.0  # fps
    width: int = 0
    height: int = 0
    offset_x: int = 0
    offset_y: int = 0
    auto_exposure: bool = False
    auto_gain: bool = False
    auto_white_balance: bool = False


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


class HikrobotThread(QThread):
    frame_ready = Signal(object)
    error_occurred = Signal(str)
    params_changed = Signal(object)  # CameraParams

    def __init__(self, cti_file: Optional[str] = None, camera_index: int = 0):
        super().__init__()
        self.cti_file = cti_file
        self.camera_index = camera_index
        self.running = False
        self.harvester = None
        self.ia = None
        self.last_frame = None
        self._mutex = QMutex()
        self._params = CameraParams()
        self._node_map = None

    @staticmethod
    def get_devices(cti_file: Optional[str] = None) -> List[str]:
        """
        Возвращает список доступных устройств в виде строк

        Args:
            cti_file: Путь к CTI файлу

        Returns:
            List[str]: Список строк с описанием устройств
        """
        harvester = None
        try:
            harvester = Harvester()

            if cti_file:
                harvester.add_file(cti_file)
            else:
                harvester.add_file('/opt/mvIMPACT_Acquire/lib/x86_64/mvGenTLProducer.cti')

            harvester.update()

            devices = []
            for i, device_info in enumerate(harvester.device_info_list):
                device_str = f"Index {i}: {getattr(device_info, 'vendor', 'Unknown')} {getattr(device_info, 'model', 'Unknown')} (SN: {getattr(device_info, 'serial_number', 'Unknown')})"
                devices.append(device_str)

            return devices

        except Exception as e:
            print(f"Error getting devices: {e}")
            return []

        finally:
            if harvester:
                try:
                    harvester.reset()
                except Exception as e:
                    print(f"Error cleaning up harvester: {e}")
    # ==================== Формат Пикселей и режим захвата ====================
    def set_pixel_format(self, format_name: str = 'Mono8') -> bool:
        """
        Установка формата пикселей

        Args:
            format_name: 'Mono8', 'BayerRG8', 'RGB8', etc.
        """
        if not self._node_map:
            return False

        try:
            if hasattr(self._node_map, 'PixelFormat'):
                if hasattr(self._node_map.PixelFormat, 'symbolics'):
                    available = self._node_map.PixelFormat.symbolics

                    # Пробуем установить указанный формат
                    if format_name in available:
                        self._node_map.PixelFormat.value = format_name
                        print(f"  Pixel format: {format_name}")
                        return True

                    # Fallback: если Mono8 недоступен, пробуем BayerRG8
                    if format_name == 'Mono8' and 'BayerRG8' in available:
                        self._node_map.PixelFormat.value = 'BayerRG8'
                        print(f"  Pixel format: BayerRG8 (Mono8 not available)")
                        return True

            print(f"  Warning: Pixel format {format_name} not available")
        except Exception as e:
            print(f"Error setting pixel format: {e}")
        return False

    def get_pixel_format(self) -> str:
        """Получение текущего формата пикселей"""
        if not self._node_map:
            return ''

        try:
            if hasattr(self._node_map, 'PixelFormat'):
                return str(self._node_map.PixelFormat.value)
        except Exception as e:
            print(f"Error getting pixel format: {e}")
        return ''

    def get_available_pixel_formats(self) -> List[str]:
        """Получение списка доступных форматов пикселей"""
        if not self._node_map:
            return []

        try:
            if hasattr(self._node_map, 'PixelFormat'):
                if hasattr(self._node_map.PixelFormat, 'symbolics'):
                    return list(self._node_map.PixelFormat.symbolics)
        except Exception as e:
            print(f"Error getting available pixel formats: {e}")
        return []

    def set_acquisition_mode(self, mode: str = 'Continuous') -> bool:
        """
        Установка режима захвата

        Args:
            mode: 'Continuous', 'SingleFrame', 'MultiFrame'
        """
        if not self._node_map:
            return False

        try:
            if hasattr(self._node_map, 'AcquisitionMode'):
                self._node_map.AcquisitionMode.value = mode
                print(f"  Acquisition mode: {mode}")
                return True
        except Exception as e:
            print(f"Error setting acquisition mode: {e}")
        return False

    def get_acquisition_mode(self) -> str:
        """Получение текущего режима захвата"""
        if not self._node_map:
            return ''

        try:
            if hasattr(self._node_map, 'AcquisitionMode'):
                return str(self._node_map.AcquisitionMode.value)
        except Exception as e:
            print(f"Error getting acquisition mode: {e}")
        return ''

    def get_available_acquisition_modes(self) -> List[str]:
        """Получение списка доступных режимов захвата"""
        if not self._node_map:
            return []

        try:
            if hasattr(self._node_map, 'AcquisitionMode'):
                if hasattr(self._node_map.AcquisitionMode, 'symbolics'):
                    return list(self._node_map.AcquisitionMode.symbolics)
        except Exception as e:
            print(f"Error getting available acquisition modes: {e}")
        return []

    # ==================== Параметры экспозиции ====================

    def set_exposure(self, exposure_us: float) -> bool:
        """
        Установка времени экспозиции

        Args:
            exposure_us: Время экспозиции в микросекундах

        Returns:
            bool: Успех операции
        """
        if not self._node_map:
            return False

        try:
            # Отключаем автоэкспозицию
            if hasattr(self._node_map, 'ExposureAuto'):
                self._node_map.ExposureAuto.value = 'Off'

            if hasattr(self._node_map, 'ExposureTime'):
                self._node_map.ExposureTime.value = float(exposure_us)
                self._params.exposure = exposure_us
                self._params.auto_exposure = False
                return True
        except Exception as e:
            print(f"Error setting exposure: {e}")
        return False

    def get_exposure(self) -> float:
        """Получение текущего времени экспозиции в мкс"""
        if not self._node_map:
            return 0.0

        try:
            if hasattr(self._node_map, 'ExposureTime'):
                self._params.exposure = self._node_map.ExposureTime.value
                return self._params.exposure
        except Exception as e:
            print(f"Error getting exposure: {e}")
        return 0.0

    def get_exposure_range(self) -> Tuple[float, float]:
        """Получение диапазона экспозиции (min, max) в мкс"""
        if not self._node_map:
            return (0.0, 0.0)

        try:
            if hasattr(self._node_map, 'ExposureTime'):
                node = self._node_map.ExposureTime
                return (node.min, node.max)
        except Exception as e:
            print(f"Error getting exposure range: {e}")
        return (0.0, 0.0)

    def set_auto_exposure(self, enable: bool, mode: str = 'continuous') -> bool:
        """
        Включение/выключение автоэкспозиции

        Args:
            enable: Включить/выключить
            mode: 'off', 'once', 'continuous'
        """
        if not self._node_map:
            return False

        try:
            if hasattr(self._node_map, 'ExposureAuto'):
                if not enable:
                    self._node_map.ExposureAuto.value = 'Off'
                elif mode == 'once':
                    self._node_map.ExposureAuto.value = 'Once'
                else:
                    self._node_map.ExposureAuto.value = 'Continuous'

                self._params.auto_exposure = enable
                return True
        except Exception as e:
            print(f"Error setting auto exposure: {e}")
        return False

    # ==================== Параметры усиления ====================

    def set_gain(self, gain_db: float) -> bool:
        """
        Установка усиления

        Args:
            gain_db: Усиление в децибелах
        """
        if not self._node_map:
            return False

        try:
            # Отключаем автоусиление
            if hasattr(self._node_map, 'GainAuto'):
                self._node_map.GainAuto.value = 'Off'

            if hasattr(self._node_map, 'Gain'):
                self._node_map.Gain.value = float(gain_db)
                self._params.gain = gain_db
                self._params.auto_gain = False
                return True
        except Exception as e:
            print(f"Error setting gain: {e}")
        return False

    def get_gain(self) -> float:
        """Получение текущего усиления в дБ"""
        if not self._node_map:
            return 0.0

        try:
            if hasattr(self._node_map, 'Gain'):
                self._params.gain = self._node_map.Gain.value
                return self._params.gain
        except Exception as e:
            print(f"Error getting gain: {e}")
        return 0.0

    def get_gain_range(self) -> Tuple[float, float]:
        """Получение диапазона усиления (min, max) в дБ"""
        if not self._node_map:
            return (0.0, 0.0)

        try:
            if hasattr(self._node_map, 'Gain'):
                node = self._node_map.Gain
                return (node.min, node.max)
        except Exception as e:
            print(f"Error getting gain range: {e}")
        return (0.0, 0.0)

    def set_auto_gain(self, enable: bool, mode: str = 'continuous') -> bool:
        """Включение/выключение автоусиления"""
        if not self._node_map:
            return False

        try:
            if hasattr(self._node_map, 'GainAuto'):
                if not enable:
                    self._node_map.GainAuto.value = 'Off'
                elif mode == 'once':
                    self._node_map.GainAuto.value = 'Once'
                else:
                    self._node_map.GainAuto.value = 'Continuous'

                self._params.auto_gain = enable
                return True
        except Exception as e:
            print(f"Error setting auto gain: {e}")
        return False

    # ==================== Частота кадров ====================

    def set_frame_rate(self, fps: float) -> bool:
        """Установка частоты кадров"""
        if not self._node_map:
            return False

        try:
            # Включаем управление частотой кадров
            if hasattr(self._node_map, 'AcquisitionFrameRateEnable'):
                self._node_map.AcquisitionFrameRateEnable.value = True

            if hasattr(self._node_map, 'AcquisitionFrameRate'):
                self._node_map.AcquisitionFrameRate.value = float(fps)
                self._params.frame_rate = fps
                return True
        except Exception as e:
            print(f"Error setting frame rate: {e}")
        return False

    def get_frame_rate(self) -> float:
        """Получение текущей частоты кадров"""
        if not self._node_map:
            return 0.0

        try:
            # ResultingFrameRate - реальная частота кадров
            if hasattr(self._node_map, 'ResultingFrameRate'):
                return self._node_map.ResultingFrameRate.value
            elif hasattr(self._node_map, 'AcquisitionFrameRate'):
                return self._node_map.AcquisitionFrameRate.value
        except Exception as e:
            print(f"Error getting frame rate: {e}")
        return 0.0

    def get_frame_rate_range(self) -> Tuple[float, float]:
        """Получение диапазона частоты кадров"""
        if not self._node_map:
            return (0.0, 0.0)

        try:
            if hasattr(self._node_map, 'AcquisitionFrameRate'):
                node = self._node_map.AcquisitionFrameRate
                return (node.min, node.max)
        except Exception as e:
            print(f"Error getting frame rate range: {e}")
        return (0.0, 0.0)

    # ==================== Разрешение и ROI ====================

    def get_resolution(self) -> Tuple[int, int]:
        """Получение текущего разрешения (width, height)"""
        if not self._node_map:
            return (0, 0)

        try:
            width = self._node_map.Width.value if hasattr(self._node_map, 'Width') else 0
            height = self._node_map.Height.value if hasattr(self._node_map, 'Height') else 0

            self._params.width = width
            self._params.height = height

            return (width, height)
        except Exception as e:
            print(f"Error getting resolution: {e}")
        return (0, 0)

    def get_max_resolution(self) -> Tuple[int, int]:
        """Получение максимального разрешения"""
        if not self._node_map:
            return (0, 0)

        try:
            width = self._node_map.Width.max if hasattr(self._node_map, 'Width') else 0
            height = self._node_map.Height.max if hasattr(self._node_map, 'Height') else 0
            return (width, height)
        except Exception as e:
            print(f"Error getting max resolution: {e}")
        return (0, 0)

    def set_resolution(self, width: int, height: int) -> bool:
        """
        Установка разрешения

        ВАЖНО: Нужно остановить захват перед изменением!
        """
        if not self._node_map:
            return False

        try:
            was_running = self.running
            if was_running and self.ia:
                self.ia.stop()

            if hasattr(self._node_map, 'Width'):
                self._node_map.Width.value = width
            if hasattr(self._node_map, 'Height'):
                self._node_map.Height.value = height

            self._params.width = width
            self._params.height = height

            if was_running and self.ia:
                self.ia.start()

            return True
        except Exception as e:
            print(f"Error setting resolution: {e}")
        return False

    def set_roi(self, x: int, y: int, width: int, height: int) -> bool:
        """
        Установка области интереса (ROI)

        Args:
            x: Смещение по X
            y: Смещение по Y
            width: Ширина ROI
            height: Высота ROI
        """
        if not self._node_map:
            return False

        try:
            was_running = self.running
            if was_running and self.ia:
                self.ia.stop()

            # Сначала сбрасываем смещения
            if hasattr(self._node_map, 'OffsetX'):
                self._node_map.OffsetX.value = 0
            if hasattr(self._node_map, 'OffsetY'):
                self._node_map.OffsetY.value = 0

            # Устанавливаем размеры
            if hasattr(self._node_map, 'Width'):
                self._node_map.Width.value = width
            if hasattr(self._node_map, 'Height'):
                self._node_map.Height.value = height

            # Устанавливаем смещения
            if hasattr(self._node_map, 'OffsetX'):
                self._node_map.OffsetX.value = x
            if hasattr(self._node_map, 'OffsetY'):
                self._node_map.OffsetY.value = y

            self._params.width = width
            self._params.height = height
            self._params.offset_x = x
            self._params.offset_y = y

            if was_running and self.ia:
                self.ia.start()

            return True
        except Exception as e:
            print(f"Error setting ROI: {e}")
        return False

    def reset_roi(self) -> bool:
        """Сброс ROI на максимальное разрешение"""
        max_w, max_h = self.get_max_resolution()
        if max_w > 0 and max_h > 0:
            return self.set_roi(0, 0, max_w, max_h)
        return False

    # ==================== Баланс белого ====================

    def set_auto_white_balance(self, enable: bool, mode: str = 'continuous') -> bool:
        """Включение/выключение автоматического баланса белого"""
        if not self._node_map:
            return False

        try:
            if hasattr(self._node_map, 'BalanceWhiteAuto'):
                if not enable:
                    self._node_map.BalanceWhiteAuto.value = 'Off'
                elif mode == 'once':
                    self._node_map.BalanceWhiteAuto.value = 'Once'
                else:
                    self._node_map.BalanceWhiteAuto.value = 'Continuous'

                self._params.auto_white_balance = enable
                return True
        except Exception as e:
            print(f"Error setting auto white balance: {e}")
        return False

    # ==================== Гамма ====================

    def set_gamma(self, gamma: float) -> bool:
        """Установка гамма-коррекции камеры"""
        if not self._node_map:
            return False

        try:
            if hasattr(self._node_map, 'GammaEnable'):
                self._node_map.GammaEnable.value = True

            if hasattr(self._node_map, 'Gamma'):
                self._node_map.Gamma.value = float(gamma)
                return True
        except Exception as e:
            print(f"Error setting gamma: {e}")
        return False

    def set_gamma_enabled(self, enable: bool) -> bool:
        """Включение/выключение гамма-коррекции"""
        if not self._node_map:
            return False

        try:
            if hasattr(self._node_map, 'GammaEnable'):
                self._node_map.GammaEnable.value = enable
                return True
        except Exception as e:
            print(f"Error setting gamma enabled: {e}")
        return False

    # ==================== Триггер ====================

    def set_trigger_mode(self, enable: bool) -> bool:
        """Включение/выключение триггерного режима"""
        if not self._node_map:
            return False

        try:
            if hasattr(self._node_map, 'TriggerMode'):
                self._node_map.TriggerMode.value = 'On' if enable else 'Off'
                return True
        except Exception as e:
            print(f"Error setting trigger mode: {e}")
        return False

    def set_trigger_source(self, source: str = 'software') -> bool:
        """
        Установка источника триггера

        Args:
            source: 'software', 'line0', 'line1', 'line2'
        """
        if not self._node_map:
            return False

        try:
            if hasattr(self._node_map, 'TriggerSource'):
                sources = {
                    'software': 'Software',
                    'line0': 'Line0',
                    'line1': 'Line1',
                    'line2': 'Line2',
                }
                self._node_map.TriggerSource.value = sources.get(source.lower(), 'Software')
                return True
        except Exception as e:
            print(f"Error setting trigger source: {e}")
        return False

    def software_trigger(self) -> bool:
        """Программный триггер (если включен триггерный режим)"""
        if not self._node_map:
            return False

        try:
            if hasattr(self._node_map, 'TriggerSoftware'):
                self._node_map.TriggerSoftware.execute()
                return True
        except Exception as e:
            print(f"Error executing software trigger: {e}")
        return False

    # ==================== Получение всех параметров ====================

    def get_all_params(self) -> CameraParams:
        """Получение всех текущих параметров камеры"""
        if not self._node_map:
            return self._params

        self._params.exposure = self.get_exposure()
        self._params.gain = self.get_gain()
        self._params.frame_rate = self.get_frame_rate()

        w, h = self.get_resolution()
        self._params.width = w
        self._params.height = h

        return self._params

    def apply_params(self, params: CameraParams) -> bool:
        """Применение набора параметров"""
        success = True

        if params.auto_exposure:
            success &= self.set_auto_exposure(True)
        else:
            success &= self.set_exposure(params.exposure)

        if params.auto_gain:
            success &= self.set_auto_gain(True)
        else:
            success &= self.set_gain(params.gain)

        success &= self.set_frame_rate(params.frame_rate)

        if params.width > 0 and params.height > 0:
            success &= self.set_roi(
                params.offset_x, params.offset_y,
                params.width, params.height
            )

        return success

    # ==================== Основные методы ====================

    def run(self):
        try:
            self.harvester = Harvester()

            if self.cti_file:
                self.harvester.add_file(self.cti_file)
            else:
                self.harvester.add_file('/opt/MVS/lib/64/MvProducerU3V.cti')

            self.harvester.update()

            if len(self.harvester.device_info_list) == 0:
                self.error_occurred.emit('Cannot open camera - no devices found')
                return

            self.ia = self.harvester.create(self.camera_index)

            # Сохраняем node_map для управления параметрами
            self._node_map = self.ia.remote_device.node_map

            self._configure_camera()
            self.ia.start()

            self.running = True

            while self.running:
                try:
                    with self.ia.fetch(timeout=2.0) as buffer:
                        component = buffer.payload.components[0]
                        frame = np.array(component.data).reshape(component.height, component.width)

                        # Конвертация в черно-белое
                        gray = self._convert_to_grayscale(frame, str(component.data_format))

                        with QMutexLocker(self._mutex):
                            self.last_frame = gray.copy()

                        image = Image('', gray)
                        self.frame_ready.emit(image)

                except TimeoutError:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"Frame capture error: {e}")
                    continue

        except Exception as e:
            print(f"Camera error in run: {e}")
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(str(e))
        finally:
            self._cleanup()

    def _convert_to_grayscale(self, frame: np.ndarray, data_format: str) -> np.ndarray:
        """Конвертация кадра в черно-белое"""
        if len(frame.shape) == 2 and 'Bayer' not in data_format:
            return frame.astype(np.uint8)

        if 'Bayer' in data_format:
            if 'RG' in data_format:
                bgr = cv2.cvtColor(frame, cv2.COLOR_BAYER_RG2BGR)
            elif 'BG' in data_format:
                bgr = cv2.cvtColor(frame, cv2.COLOR_BAYER_BG2BGR)
            elif 'GR' in data_format:
                bgr = cv2.cvtColor(frame, cv2.COLOR_BAYER_GR2BGR)
            elif 'GB' in data_format:
                bgr = cv2.cvtColor(frame, cv2.COLOR_BAYER_GB2BGR)
            else:
                bgr = cv2.cvtColor(frame, cv2.COLOR_BAYER_RG2BGR)
            return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

        if len(frame.shape) == 3:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        return frame.astype(np.uint8)

    def _cleanup(self):
        """Очистка ресурсов"""
        self._node_map = None

        if self.ia:
            try:
                self.ia.stop()
                self.ia.destroy()
            except Exception as e:
                print(f"Camera error in cleanup: {e}")
            self.ia = None

        if self.harvester:
            try:
                self.harvester.reset()
            except Exception as e:
                print(f"Camera error in cleanup: {e}")
            self.harvester = None

    def _configure_camera(self):
        """Настройка параметров камеры"""
        try:
            print("Configuring camera parameters:")

            # 1. Отключаем триггерный режим
            if not self.set_trigger_mode(False):
                print("  Warning: Could not disable trigger mode")

            # 2. Устанавливаем максимальное разрешение
            if not self.reset_roi():
                print("  Warning: Could not set maximum resolution")
            else:
                print(f"  Resolution: {self._params.width}x{self._params.height} (maximum)")

            # 3. Устанавливаем формат пикселей (нужен отдельный метод)
            if not self.set_pixel_format('Mono8'):
                print("  Warning: Could not set pixel format")

            # 4. Устанавливаем экспозицию 1/30 сек = 33333 мкс
            if not self.set_exposure(33333.0):
                print("  Warning: Could not set exposure")
            else:
                print(f"  Exposure: {self._params.exposure} us (1/30 sec)")

            # 5. Устанавливаем усиление 10 дБ
            if not self.set_gain(0.0):
                print("  Warning: Could not set gain")
            else:
                print(f"  Gain: {self._params.gain} dB")

            # 6. Устанавливаем частоту кадров 30 fps
            if not self.set_frame_rate(30.0):
                print("  Warning: Could not set frame rate")
            else:
                print(f"  Frame rate: {self._params.frame_rate} fps")

            # 7. Режим захвата - непрерывный
            if not self.set_acquisition_mode('Continuous'):
                print("  Warning: Could not set acquisition mode")

            print("Camera configured successfully!")

        except Exception as e:
            print(f"Warning: Could not configure camera: {e}")


    def stop(self) -> Optional[Image]:
        """Остановка потока и возврат последнего кадра"""
        self.running = False

        if not self.wait(3000):
            print("Warning: Thread did not stop in time")
            self.terminate()
            self.wait()

        with QMutexLocker(self._mutex):
            last = self.last_frame
            self.last_frame = None

        if last is not None:
            return Image('', last)
        return None
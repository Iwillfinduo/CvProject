from PySide6.QtCore import (QCoreApplication, QMetaObject, Qt)
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QSizePolicy,
                               QVBoxLayout, QSpacerItem, QComboBox, QDialogButtonBox,
                               QDialog, QCheckBox, QGroupBox, QMessageBox)

from utils import PreprocessMethod


class ChooseCameraDialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"ChooseCameraDialog")
        Dialog.resize(247, 290)
        self.verticalLayout_2 = QVBoxLayout(Dialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.comboBox = QComboBox(Dialog)
        self.comboBox.setObjectName(u"comboBox")

        self.verticalLayout.addWidget(self.comboBox)

        self.verticalSpacer = QSpacerItem(30, 31, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        self.buttonBox.setSizePolicy(sizePolicy)
        self.buttonBox.setOrientation(Qt.Orientation.Vertical)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setCenterButtons(True)

        self.horizontalLayout.addWidget(self.buttonBox)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)

    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("ChooseCameraDialog", u"Choose Camera", None))
    # retranslateUi


class PreprocessMethodDialog(QDialog):
    """Диалог выбора методов предобработки для пакетной обработки изображений"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName(u"PreprocessMethodDialog")
        self.setMinimumWidth(400)

        self._checkboxes: dict[PreprocessMethod, QCheckBox] = {}
        self._selected_methods: list[PreprocessMethod] = []

        self._init_ui()
        self.retranslateUi()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        self._header_label = QLabel()
        self._header_label.setObjectName(u"headerLabel")
        self._header_label.setWordWrap(True)
        layout.addWidget(self._header_label)

        # Группа с чекбоксами
        self._group_box = QGroupBox()
        self._group_box.setObjectName(u"groupBox")
        group_layout = QVBoxLayout()

        for method in PreprocessMethod:
            cb = QCheckBox()
            cb.setObjectName(f"checkBox_{method.name}")
            # По умолчанию выбран основной метод
            if method == PreprocessMethod.GAMMA_BY_AREA:
                cb.setChecked(True)
            self._checkboxes[method] = cb
            group_layout.addWidget(cb)

        self._group_box.setLayout(group_layout)
        layout.addWidget(self._group_box)

        # Кнопки Select All / Deselect All
        toggle_layout = QHBoxLayout()

        self._select_all_btn = QPushButton()
        self._select_all_btn.setObjectName(u"selectAllButton")
        self._select_all_btn.clicked.connect(self._select_all)
        toggle_layout.addWidget(self._select_all_btn)

        self._deselect_all_btn = QPushButton()
        self._deselect_all_btn.setObjectName(u"deselectAllButton")
        self._deselect_all_btn.clicked.connect(self._deselect_all)
        toggle_layout.addWidget(self._deselect_all_btn)

        layout.addLayout(toggle_layout)

        # OK / Cancel
        button_layout = QHBoxLayout()

        self._ok_btn = QPushButton()
        self._ok_btn.setObjectName(u"okButton")
        self._ok_btn.setDefault(True)
        self._ok_btn.clicked.connect(self._on_accept)
        button_layout.addWidget(self._ok_btn)

        self._cancel_btn = QPushButton()
        self._cancel_btn.setObjectName(u"cancelButton")
        self._cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self._cancel_btn)

        layout.addLayout(button_layout)

    def retranslateUi(self):
        self.setWindowTitle(QCoreApplication.translate(
            "PreprocessMethodDialog", "Select Preprocessing Methods", None))

        self._header_label.setText(QCoreApplication.translate(
            "PreprocessMethodDialog",
            "Select one or more preprocessing methods.\n"
            "Each image will be processed by every selected method.", None))

        self._group_box.setTitle(QCoreApplication.translate(
            "PreprocessMethodDialog", "Preprocessing Methods", None))


        for method, cb in self._checkboxes.items():
            cb.setText(QCoreApplication.translate(
                "PreprocessMethodDialog", method.value, None))

        self._select_all_btn.setText(QCoreApplication.translate(
            "PreprocessMethodDialog", "Select All", None))

        self._deselect_all_btn.setText(QCoreApplication.translate(
            "PreprocessMethodDialog", "Deselect All", None))

        self._ok_btn.setText(QCoreApplication.translate(
            "PreprocessMethodDialog", "OK", None))

        self._cancel_btn.setText(QCoreApplication.translate(
            "PreprocessMethodDialog", "Cancel", None))

    def _select_all(self):
        for cb in self._checkboxes.values():
            cb.setChecked(True)

    def _deselect_all(self):
        for cb in self._checkboxes.values():
            cb.setChecked(False)

    def _on_accept(self):
        self._selected_methods = [
            method for method, cb in self._checkboxes.items() if cb.isChecked()
        ]
        if not self._selected_methods:
            QMessageBox.warning(
                self,
                QCoreApplication.translate("PreprocessMethodDialog", "Warning", None),
                QCoreApplication.translate(
                    "PreprocessMethodDialog",
                    "Please select at least one method.", None))
            return
        self.accept()

    def get_selected_methods(self) -> list[PreprocessMethod]:
        """Возвращает список выбранных методов после закрытия диалога"""
        return self._selected_methods
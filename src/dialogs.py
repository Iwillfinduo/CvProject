from PySide6.QtCore import (QCoreApplication, QMetaObject, Qt)
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QSizePolicy,
                               QVBoxLayout, QSpacerItem, QComboBox, QDialogButtonBox,
                               QDialog, QCheckBox, QGroupBox, QMessageBox)

from utils import PreprocessMethod


class ChooseCameraDialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
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
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
    # retranslateUi


class PreprocessMethodDialog(QDialog):
    """Диалог выбора методов предобработки для пакетной обработки изображений"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Preprocessing Methods")
        self.setMinimumWidth(400)

        self._checkboxes: dict[PreprocessMethod, QCheckBox] = {}
        self._selected_methods: list[PreprocessMethod] = []

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        header = QLabel("Select one or more preprocessing methods.\n"
                        "Each image will be processed by every selected method.")
        header.setWordWrap(True)
        layout.addWidget(header)

        # Группа с чекбоксами
        group = QGroupBox("Preprocessing Methods")
        group_layout = QVBoxLayout()

        for method in PreprocessMethod:
            cb = QCheckBox(method.value)
            # По умолчанию выбран основной метод
            if method == PreprocessMethod.GAMMA_BY_AREA:
                cb.setChecked(True)
            self._checkboxes[method] = cb
            group_layout.addWidget(cb)

        group.setLayout(group_layout)
        layout.addWidget(group)

        # Кнопки Select All / Deselect All
        toggle_layout = QHBoxLayout()

        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all)
        toggle_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self._deselect_all)
        toggle_layout.addWidget(deselect_all_btn)

        layout.addLayout(toggle_layout)

        # OK / Cancel
        button_layout = QHBoxLayout()

        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self._on_accept)
        button_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

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
            QMessageBox.warning(self, "Warning", "Please select at least one method.")
            return
        self.accept()

    def get_selected_methods(self) -> list[PreprocessMethod]:
        """Возвращает список выбранных методов после закрытия диалога"""
        return self._selected_methods

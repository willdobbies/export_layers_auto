# SPDX-License-Identifier: CC0-1.0

import krita
import re
from enum import Enum

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QLabel,
    QLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from .backend import ExportBackend, ExportConfig, ImageFormat


class ExportLayersDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

    def closeEvent(self, a0: QCloseEvent | None):
        if a0:
            a0.accept()


def camelCaseSplit(identifier) -> str:
    """
    Split a camel case string
    camelCaseString -> Camel Case String
    """
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    splits = [m.group(0) for m in matches]
    return " ".join([s.capitalize() for s in splits])

class ExportUI:
    """
    A QT Ui for displaying and manipulating ExportConfig objects
    """

    def __init__(self, backend : ExportBackend, config : ExportConfig):
        self.backend = backend
        self.widget_map = {}
        self._setup_dialog()
        
        self.config = config
        self.update_widgets()

    def _createWidget(
        self,
        name: str,
        widget: QWidget,
        label_text: str|None = "",
        section: QLayout | None = None,
    ):
        if not section:
            section = self.form_layout

        if label_text == "":
            label_text = camelCaseSplit(name) + ": "

        if isinstance(section, QFormLayout):
            section.addRow(label_text, widget)
        else:
            section.addWidget(widget)
        self.widget_map[name] = widget

    def addSectionHeader(self, title: str, section: QLayout | None = None):
        if not section:
            section = self.form_layout

        header_label = QLabel(title)
        header_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        if isinstance(section, QFormLayout):
            section.addRow(header_label)
        else:
            section.addWidget(header_label)
        return header_label

    def _createComboBox(self, values: list[str]) -> QComboBox:
        cb = QComboBox()
        for v in values:
            cb.addItem(v)
        return cb

    def _createEnumComboBox(self, enum: type[Enum]) -> QComboBox:
        return self._createComboBox([v.value for v in enum])

    def _setup_dialog(self):
        """
        Create the main dialog container.
        """
        self.main_dialog = ExportLayersDialog()
        self.main_layout = QVBoxLayout(self.main_dialog)
        self.main_dialog.setWindowFlags(Qt.WindowType.Popup)
        self.main_dialog.setWindowModality(Qt.WindowModality.NonModal)

        self.form_layout = QFormLayout()
        self.main_layout.addLayout(self.form_layout)

        self.addSectionHeader("File Naming")
        self._createWidget("layerNameDelimeter", QLineEdit())
        self._createWidget("prependDocumentName",  QCheckBox())

        self.addSectionHeader("Layer Selection")
        self._createWidget("ignoreFilterLayers",  QCheckBox())
        self._createWidget("ignoreInvisibleLayers",  QCheckBox())
        self._createWidget("exportGroupsMerged", QCheckBox())

        self.addSectionHeader("Export Options")
        self._createWidget("imageFormat", self._createEnumComboBox(ImageFormat))
        self._createWidget("cropToImageBounds", QCheckBox())
        self._createWidget("exportAnimations", QCheckBox())

        self.main_layout.addWidget(self._createSeperator())

        self.okCancel = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self._createWidget("_okCancel", self.okCancel, label_text=None)
        
        self.okCancel.accepted.connect(self.onConfirm)
        self.okCancel.rejected.connect(self.onClose)

    def onConfirm(self):
        self.update_config()
        self.backend.config = self.config
        self.backend.export(krita.Krita.instance().activeDocument())
        
    def onClose(self):
        self.main_dialog.close()

    def _createSeperator(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        return sep

    def show(self):
        """
        Show the config window
        """
        self.main_dialog.resize(500, 300)
        self.main_dialog.setWindowTitle("Export Layers")
        self.main_dialog.setSizeGripEnabled(True)
        self.main_dialog.show()
        self.main_dialog.activateWindow()

    def confirm_button(self) -> None:
        pass

    def _get_widget_prop(self, name: str):
        if not name in self.widget_map:
            raise ValueError(f"Unknown option {name}")

        widget = self.widget_map[name]

        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QLineEdit):
            return widget.text()
        else:
            raise TypeError(f"Unhandled widget type {type(widget)}")

    def _set_widget_prop(self, name: str, val):
        if not name in self.widget_map:
            raise ValueError(f"Unknown option {name}")

        widget = self.widget_map[name]

        if isinstance(widget, QCheckBox):
            widget.setChecked(val)
        elif isinstance(widget, QLineEdit):
            widget.setText(val)
        else:
            raise TypeError(f"Unhandled widget type {type(widget)}")

    def update_widgets(self):
        """Read internal config object, update widget values."""

        for name in self.config.__annotations__:
            val = getattr(self.config, name)
            self._set_widget_prop(name, val)
        
    def update_config(self):
        """Read widget values, apply them to internal config object."""
        for name in self.config.__annotations__:
            readVal = self._get_widget_prop(name)
            setattr(self.config, name, readVal)
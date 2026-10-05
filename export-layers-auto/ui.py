# SPDX-License-Identifier: CC0-1.0

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

from .backend import ExportConfig, ImageFormat


class ExportLayersDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

    def closeEvent(self, a0: QCloseEvent | None):
        if a0:
            a0.accept()


class ExportUI:
    """
    A QT Ui for displaying and manipulating ExportConfig objects
    """

    def __init__(self):
        self.widget_map = {}
        self._setup_dialog()
    
    def addWidget(self, name : str, widget : QWidget, section : QLayout|None = None):
        if(not section):
            section = self.main_layout
            
        section.addWidget(widget)
        self.widget_map[name] = widget

    def _createComboBox(self, values : list[str]) -> QComboBox:
        cb = QComboBox()
        for v in values:
            cb.addItem(v)
        return cb

    def _createEnumComboBox(self, enum : type[Enum]) -> QComboBox:
        return self._createComboBox([v.value for v in enum])

    #def addWidgetSection(self, name : str, layoutType = QVBoxLayout) -> QLayout:
    #    new_layout = layoutType()
    #    self.main_layout.addLayout(new_layout)
    #    new_layout.addWidget(QLabel(text=name))
    #    #new_layout = layoutType()
    #    #self.main_layout.addLayout(new_layout)
    #    return new_layout

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
        
        _ = self.form_layout
        
        #_ = self.addWidgetSection("File Naming")
        self.addWidget("layerNameDelimeter", QLineEdit("Layer Name Delimeter"), _)
        self.addWidget("prependDocumentName", QCheckBox("Prepend Document Name"), _)
        
        #_ = self.addWidgetSection("Layer Selection")
        self.addWidget("ignoreFilterLayers", QCheckBox("Ignore Filter Layers"), _)
        self.addWidget("ignoreInvisibleLayers", QCheckBox("Ignore Invisible Layers"), _)
        self.addWidget("exportGroupsMerged", QCheckBox("Export Groups Merged"), _)

        #_ = self.addWidgetSection("Export Options")
        self.addWidget("imageFormat",  self._createEnumComboBox(ImageFormat), _)
        self.addWidget("cropToImageBounds", QCheckBox("Crop To Image Bounds"), _)
        self.addWidget("exportAnimations", QCheckBox("Export Animations"), _)
        
        self.main_layout.addWidget(self._createSeperator())
        
        self.addWidget(
            "_okCancel", 
            QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel),
            _
        )

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

    def _get_widget_prop(self, name : str):
        if not name in self.widget_map:
            raise ValueError(f"Unknown option {name}")
            
        widget = self.widget_map[name]
        
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QLineEdit):
            return widget.text()
        else:
            raise TypeError(f"Unhandled widget type {type(widget)}")

    def _set_widget_prop(self, name : str, val):
        if not name in self.widget_map:
            raise ValueError(f"Unknown option {name}")
            
        widget = self.widget_map[name]
        
        if isinstance(widget, QCheckBox):
            widget.setChecked(val)
        elif isinstance(widget, QLineEdit):
            widget.setText(val)
        else:
            raise TypeError(f"Unhandled widget type {type(widget)}")

    def _apply_config(self, config : ExportConfig):
        """Read a config object, update widget values."""
        
        for name in config.__annotations__:
            val = getattr(config, name)
            self._set_widget_prop(name, val)

    def _read_config(self) -> ExportConfig:
        """Read widget values, return updated config."""
        newConfig = ExportConfig()
        for name in newConfig.__annotations__:
            readVal = self._get_widget_prop(name)
            setattr(newConfig, name, readVal)
        return newConfig

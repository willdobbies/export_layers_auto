# SPDX-License-Identifier: CC0-1.0

import krita
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from .backend import ExportBackend, ExportConfig


class ExportLayersDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

    def closeEvent(self, a0):
        if(a0):
            a0.accept()


class ExportUI:
    def __init__(self, backend: ExportBackend):
        self.backend = backend  # ExportBackend(self.config)
        self.config = backend.config

        self.mainDialog = ExportLayersDialog()
        self.mainLayout = QVBoxLayout(self.mainDialog)
        self.formLayout = QFormLayout()
        self.optionsLayout = QVBoxLayout()
        self.outputNameLayout = QVBoxLayout()
        self.sizingLayout = QVBoxLayout()

        self.cropToImageBounds = QCheckBox("Crop export size to layer content")
        self.exportGroupChildren = QCheckBox("Export group children")
        self.exportGroupsMerged = QCheckBox("Export groups merged")
        self.ignoreFilterLayers = QCheckBox("Ignore filter layers")
        self.ignoreInvisibleLayers = QCheckBox("Ignore invisible layers")
        self.layerNameDelimeter = QLineEdit("Layer name delimeter")
        self.prependDocumentName = QCheckBox("Prepend document name")

        self.imageFormat = QComboBox()

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        self.kritaInstance = krita.Krita.instance()

        self.setWidgetsFromConfig(self.config)

        self.buttonBox.accepted.connect(self.confirmButton)
        self.buttonBox.rejected.connect(self.mainDialog.close)

        self._updateDocument(self.kritaInstance.activeDocument())
        self.mainDialog.setWindowModality(Qt.NonModal)

    def setWidgetsFromConfig(self, config):
        for optionName in config.__annotations__:
            optionType = config.__annotations__[optionName]
            defaultValue = getattr(config, optionName)
            targetWidget = getattr(self, optionName)
            targetWidgetType = type(targetWidget)

            if not targetWidget:
                continue

            if optionType is bool and targetWidgetType is QCheckBox:
                getattr(self, optionName).setChecked(defaultValue)
            if optionType is str and targetWidgetType is QLineEdit:
                getattr(self, optionName).setText(defaultValue)

    def setConfigFromWidgets(self, config=ExportConfig()):
        for optionName in config.__annotations__:
            optionType = config.__annotations__[optionName]
            targetWidget = getattr(self, optionName)
            targetWidgetType = type(targetWidget)

            if not targetWidget:
                continue

            if optionType is bool and targetWidgetType is QCheckBox:
                setattr(config, optionName, targetWidget.isChecked())
            if optionType is str and targetWidgetType is QLineEdit:
                setattr(config, optionName, targetWidget.text())
        return config

    def initialize(self):
        self.formLayout.addRow("Output layer path delimeter:", self.outputNameLayout)
        self.outputNameLayout.addWidget(self.layerNameDelimeter)
        self.outputNameLayout.addWidget(self.prependDocumentName)

        self.formLayout.addRow("Layer selection:", self.optionsLayout)
        self.optionsLayout.addWidget(self.exportGroupChildren)
        self.optionsLayout.addWidget(self.exportGroupsMerged)
        self.optionsLayout.addWidget(self.ignoreFilterLayers)
        self.optionsLayout.addWidget(self.ignoreInvisibleLayers)

        self.formLayout.addRow("Image sizing:", self.sizingLayout)
        self.sizingLayout.addWidget(self.cropToImageBounds)

        self.formLayout.addRow("Images extension:", self.imageFormat)
        self.imageFormat.addItem("png")
        self.imageFormat.addItem("jpeg")

        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.mainLayout.addLayout(self.formLayout)
        self.mainLayout.addWidget(self.line)
        self.mainLayout.addWidget(self.buttonBox)

        self._updateDocument(self.kritaInstance.activeDocument())

        self.mainDialog.resize(500, 300)
        self.mainDialog.setWindowTitle("Export Layers")
        self.mainDialog.setSizeGripEnabled(True)
        self.mainDialog.show()
        self.mainDialog.activateWindow()

    def confirmButton(self):
        selectedDocument = self.currentDoc

        self.backend.config = self.setConfigFromWidgets(self.config)

        if not selectedDocument:
            self.msgBox = QMessageBox(self.mainDialog)
            self.msgBox.setText("Select one document.")
            self.msgBox.exec_()
        else:
            self.backend.export(selectedDocument)

    def _updateDocument(self, document):
        self.currentDoc = document

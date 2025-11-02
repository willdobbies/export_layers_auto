# SPDX-License-Identifier: CC0-1.0

from .backend import ExportBackend, ExportConfig
from PyQt5.QtCore import (Qt, QRect)
from PyQt5.QtWidgets import (QFormLayout, QListWidget, QHBoxLayout,
                             QDialogButtonBox, QVBoxLayout, QFrame,
                             QPushButton, QAbstractScrollArea, QLineEdit,
                             QMessageBox, QFileDialog, QCheckBox,
                             QComboBox, QDialog)
import os
import krita

class ExportLayersDialog(QDialog):
    def __init__(self, parent=None):
        super(ExportLayersDialog, self).__init__(parent)

    def closeEvent(self, event):
        event.accept()

class ExportUI(object):
    def __init__(self, config):
        self.config = config
        self.backend = ExportBackend(self.config)

        self.mainDialog = ExportLayersDialog()
        self.mainLayout = QVBoxLayout(self.mainDialog)
        self.formLayout = QFormLayout()
        self.optionsLayout = QVBoxLayout()
        self.outputNameLayout = QVBoxLayout()
        self.sizingLayout = QVBoxLayout()

        self.cropToImageBounds = QCheckBox( i18n("Crop export size to layer content"))
        self.exportGroupChildren = QCheckBox(i18n("Export group children"))
        self.exportGroupsMerged = QCheckBox(i18n("Export groups merged"))
        self.ignoreFilterLayers = QCheckBox( i18n("Ignore filter layers"))
        self.ignoreInvisibleLayers = QCheckBox( i18n("Ignore invisible layers"))
        self.layerNameDelimeter = QLineEdit ( i18n("Layer name delimeter") )
        self.prependDocumentName = QCheckBox( i18n("Prepend document name"))

        self.imageFormat = QComboBox()

        self.buttonBox = QDialogButtonBox( QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

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

            if(not targetWidget):
                continue

            if(optionType is bool and targetWidgetType is QCheckBox):
                getattr(self, optionName).setChecked(defaultValue)
            if(optionType is str and targetWidgetType is QLineEdit):
                getattr(self, optionName).setText(defaultValue)

    def setConfigFromWidgets(self, config=ExportConfig()):
        for optionName in config.__annotations__:
            optionType = config.__annotations__[optionName]
            targetWidget = getattr(self, optionName)
            targetWidgetType = type(targetWidget)

            if(not targetWidget):
                continue

            if(optionType is bool and targetWidgetType is QCheckBox):
                setattr(config, optionName, targetWidget.isChecked())
            if(optionType is str and targetWidgetType is QLineEdit):
                setattr(config, optionName, targetWidget.text())
        return config

    def initialize(self):
        self.formLayout.addRow(i18n("Output filename:"), self.outputNameLayout)
        self.outputNameLayout.addWidget(self.layerNameDelimeter)
        self.outputNameLayout.addWidget(self.prependDocumentName)

        self.formLayout.addRow(i18n("Layer selection:"), self.optionsLayout)
        self.optionsLayout.addWidget(self.exportGroupChildren)
        self.optionsLayout.addWidget(self.exportGroupsMerged)
        self.optionsLayout.addWidget(self.ignoreFilterLayers)
        self.optionsLayout.addWidget(self.ignoreInvisibleLayers)

        self.formLayout.addRow(i18n("Image sizing:"), self.sizingLayout)
        self.sizingLayout.addWidget(self.cropToImageBounds)

        self.formLayout.addRow(i18n("Images extension:"), self.imageFormat)
        self.imageFormat.addItem(i18n("png"))
        self.imageFormat.addItem(i18n("jpeg"))

        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.mainLayout.addLayout(self.formLayout)
        self.mainLayout.addWidget(self.line)
        self.mainLayout.addWidget(self.buttonBox)

        self._updateDocument(self.kritaInstance.activeDocument())

        self.mainDialog.resize(500, 300)
        self.mainDialog.setWindowTitle(i18n("Export Layers"))
        self.mainDialog.setSizeGripEnabled(True)
        self.mainDialog.show()
        self.mainDialog.activateWindow()

    def confirmButton(self):
        selectedDocument = self.currentDoc

        self.backend.config = self.setConfigFromWidgets(self.config)

        if not selectedDocument:
            self.msgBox = QMessageBox(self.mainDialog)
            self.msgBox.setText(i18n("Select one document."))
            self.msgBox.exec_()
        else:
            self.backend.export(selectedDocument)

    def _updateDocument(self, document):
        self.currentDoc = document

# SPDX-License-Identifier: CC0-1.0

from . import exportlayersdialog
from .exportbackend import ExportBackend, ExportConfig
from PyQt5.QtCore import (Qt, QRect)
from PyQt5.QtWidgets import (QFormLayout, QListWidget, QHBoxLayout,
                             QDialogButtonBox, QVBoxLayout, QFrame,
                             QPushButton, QAbstractScrollArea, QLineEdit,
                             QMessageBox, QFileDialog, QCheckBox,
                             QComboBox)
import os
import krita

class UIExportLayers(object):
    def __init__(self, config):
        self.config = config
        self.backend = ExportBackend(self.config)

        self.mainDialog = exportlayersdialog.ExportLayersDialog()
        self.mainLayout = QVBoxLayout(self.mainDialog)
        self.formLayout = QFormLayout()
        self.optionsLayout = QVBoxLayout()
        self.outputNameLayout = QVBoxLayout()

        self.exportFilterLayers = QCheckBox( i18n("Export filter layers"))
        self.batchMode = QCheckBox(i18n("Export in batchmode"))
        self.groupAsLayer = QCheckBox(i18n("Export groups as layers"))
        self.ignoreInvisibleLayers = QCheckBox( i18n("Ignore invisible layers"))
        self.cropToImageBounds = QCheckBox( i18n("Crop export size to layer content"))
        self.outputNameFormat = QLineEdit ( i18n("Output name format") )

        self.formatsComboBox = QComboBox()

        self.buttonBox = QDialogButtonBox( QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        self.kritaInstance = krita.Krita.instance()

        self.outputNameFormat.setText(self.config.nameFormat)
        self.batchMode.setChecked(self.config.batchMode)
        self.groupAsLayer.setChecked(self.config.groupAsLayer)
        self.cropToImageBounds.setChecked(self.config.cropToImageBounds)

        self.buttonBox.accepted.connect(self.confirmButton)
        self.buttonBox.rejected.connect(self.mainDialog.close)

        self._updateDocument(self.kritaInstance.activeDocument())
        self.mainDialog.setWindowModality(Qt.NonModal)

    def initialize(self):
        self.formatsComboBox.addItem(i18n("png"))
        self.formatsComboBox.addItem(i18n("jpeg"))

        self.optionsLayout.addWidget(self.exportFilterLayers)
        self.optionsLayout.addWidget(self.batchMode)
        self.optionsLayout.addWidget(self.groupAsLayer)
        self.optionsLayout.addWidget(self.ignoreInvisibleLayers)
        self.optionsLayout.addWidget(self.cropToImageBounds)

        self.outputNameLayout.addWidget(self.outputNameFormat)

        self.formLayout.addRow(i18n("Output name format:"), self.outputNameLayout)
        self.formLayout.addRow(i18n("Export options:"), self.optionsLayout)
        self.formLayout.addRow(i18n("Images extensions:"), self.formatsComboBox)

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

        self.config.nameFormat = self.outputNameFormat.text()
        self.config.batchMode = self.batchMode.isChecked()
        self.config.groupAsLayer = self.groupAsLayer.isChecked()
        self.config.cropToImageBounds = self.cropToImageBounds.isChecked()
        self.backend.config = self.config

        if not selectedDocument:
            self.msgBox = QMessageBox(self.mainDialog)
            self.msgBox.setText(i18n("Select one document."))
            self.msgBox.exec_()
        else:
            self.backend.export(selectedDocument)

    def _updateDocument(self, document):
        self.currentDoc = document

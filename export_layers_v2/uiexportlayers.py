# SPDX-License-Identifier: CC0-1.0

from . import exportlayersdialog
from PyQt5.QtCore import (Qt, QRect)
from PyQt5.QtWidgets import (QFormLayout, QListWidget, QHBoxLayout,
                             QDialogButtonBox, QVBoxLayout, QFrame,
                             QPushButton, QAbstractScrollArea, QLineEdit,
                             QMessageBox, QFileDialog, QCheckBox, QSpinBox,
                             QComboBox)
import os
import krita

class UIExportLayers(object):
    def __init__(self):
        self.mainDialog = exportlayersdialog.ExportLayersDialog()
        self.mainLayout = QVBoxLayout(self.mainDialog)
        self.formLayout = QFormLayout()
        self.resSpinBoxLayout = QFormLayout()
        self.documentLayout = QVBoxLayout()
        self.optionsLayout = QVBoxLayout()
        self.rectSizeLayout = QHBoxLayout()

        self.widgetDocuments = QListWidget()
        self.exportFilterLayersCheckBox = QCheckBox( i18n("Export filter layers"))
        self.batchmodeCheckBox = QCheckBox(i18n("Export in batchmode"))
        self.groupAsLayer = QCheckBox(i18n("Group as layer"))
        self.ignoreInvisibleLayersCheckBox = QCheckBox( i18n("Ignore invisible layers"))
        self.cropToImageBounds = QCheckBox( i18n("Adjust export size to layer content"))

        self.rectWidthSpinBox = QSpinBox()
        self.rectHeightSpinBox = QSpinBox()
        self.formatsComboBox = QComboBox()
        self.resSpinBox = QSpinBox()

        self.buttonBox = QDialogButtonBox( QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        self.kritaInstance = krita.Krita.instance()

        self.batchmodeCheckBox.setChecked(True)
        self.groupAsLayer.setChecked(True)
        self._setResolution(self.kritaInstance.activeDocument())
        self.buttonBox.accepted.connect(self.confirmButton)
        self.buttonBox.rejected.connect(self.mainDialog.close)
        self.cropToImageBounds.stateChanged.connect(self._toggleCropSize)

        self.mainDialog.setWindowModality(Qt.NonModal)
        self.widgetDocuments.setSizeAdjustPolicy( QAbstractScrollArea.AdjustToContents)

    def initialize(self):
        self.rectWidthSpinBox.setRange(1, 10000)
        self.rectHeightSpinBox.setRange(1, 10000)
        self.resSpinBox.setRange(20, 1200)

        self.formatsComboBox.addItem(i18n("png"))
        self.formatsComboBox.addItem(i18n("jpeg"))

        self.documentLayout.addWidget(self.widgetDocuments)

        self.optionsLayout.addWidget(self.exportFilterLayersCheckBox)
        self.optionsLayout.addWidget(self.batchmodeCheckBox)
        self.optionsLayout.addWidget(self.groupAsLayer)
        self.optionsLayout.addWidget(self.ignoreInvisibleLayersCheckBox)
        self.optionsLayout.addWidget(self.cropToImageBounds)

        self.resSpinBoxLayout.addRow(i18n("dpi:"), self.resSpinBox)

        self.rectSizeLayout.addWidget(self.rectWidthSpinBox)
        self.rectSizeLayout.addWidget(self.rectHeightSpinBox)
        self.rectSizeLayout.addLayout(self.resSpinBoxLayout)

        self.formLayout.addRow(i18n("Export options:"), self.optionsLayout)
        self.formLayout.addRow(i18n("Export size:"), self.rectSizeLayout)
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
        selectedPaths = [
            item.text() for item in self.widgetDocuments.selectedItems()]
        selectedDocument = self.currentDoc

        self.msgBox = QMessageBox(self.mainDialog)
        if not selectedDocument:
            self.msgBox.setText(i18n("Select one document."))
        else:
            self.export(selectedDocument)
            self.msgBox.setText(i18n("All layers have been exported."))
        self.msgBox.exec_()

    def mkdir(self, directory):
        target_directory = directory
        if (os.path.exists(target_directory)
                and os.path.isdir(target_directory)):
            return

        try:
            os.makedirs(target_directory)
        except OSError as e:
            raise e

    def export(self, document):
        Application.setBatchmode(self.batchmodeCheckBox.isChecked())

        docPath = document.fileName() if document.fileName() else '~/Untitled/Untitled.kra'  # noqa: E501
        docPathHead,docPathTail = os.path.split(docPath)
        docName, docExt = os.path.splitext(docPathTail)

        outDir = os.path.join(docPathHead, docName)

        self.mkdir(outDir)

        self._exportLayers(
            document.rootNode(),
            self.formatsComboBox.currentText(),
            outDir)

        Application.setBatchmode(True)

    def _exportLayers(self, parentNode, fileFormat, parentDir):
        """ This method get all sub-nodes from the current node and export then in
            the defined format."""

        for node in parentNode.childNodes():
            newDir = ''
            if node.type() == 'grouplayer' and not self.groupAsLayer.isChecked():
                newDir = os.path.join(parentDir, node.name())
                self.mkdir(newDir)
            elif (not self.exportFilterLayersCheckBox.isChecked()
                  and 'filter' in node.type()):
                continue
            elif (self.ignoreInvisibleLayersCheckBox.isChecked()
                  and not node.visible()):
                continue
            else:
                nodeName = node.name()
                _fileFormat = self.formatsComboBox.currentText()
                if '[jpeg]' in nodeName:
                    _fileFormat = 'jpeg'
                elif '[png]' in nodeName:
                    _fileFormat = 'png'

                if self.cropToImageBounds.isChecked():
                    bounds = QRect()
                else:
                    bounds = QRect(0, 0, self.rectWidthSpinBox.value(), self.rectHeightSpinBox.value())

                layerFileName = f'{parentDir}/{node.name()}.{_fileFormat}'

                node.save(layerFileName, self.resSpinBox.value() / 72.,
                          self.resSpinBox.value() / 72., krita.InfoObject(), bounds)

            if node.childNodes() and not self.groupAsLayer.isChecked():
                self._exportLayers(node, fileFormat, newDir)

    def _setResolution(self, document):
        self.rectWidthSpinBox.setValue(document.width())
        self.rectHeightSpinBox.setValue(document.height())
        self.resSpinBox.setValue(document.resolution())

    def _toggleCropSize(self):
        cropToLayer = self.cropToImageBounds.isChecked()
        self.rectWidthSpinBox.setDisabled(cropToLayer)
        self.rectHeightSpinBox.setDisabled(cropToLayer)

    def _updateDocument(self, document):
        self.currentDoc = document
        self._setResolution(self.currentDoc)

# SPDX-License-Identifier: CC0-1.0

from . import uiexportlayers
from .exportbackend import ExportBackend
import krita

class ExportLayersExtension(krita.Extension):

    def __init__(self, parent):
        super(ExportLayersExtension, self).__init__(parent)

    def setup(self):
        self.backend = ExportBackend()

    def createActions(self, window):
        aAuto = window.createAction("export_layers_auto", i18n("Export Layers Auto"))
        aAuto.setToolTip(i18n("Run export layers job in background using default settings"))
        aAuto.triggered.connect(self.exportAuto)

        aDialog = window.createAction("export_layers_dialog", i18n("Export Layers Dialog"))
        aDialog.setToolTip(i18n("Display export layers dialog"))
        aDialog.triggered.connect(self.exportDialog)

    def exportAuto(self):
        currentDocument = krita.Krita.instance().activeDocument()
        self.backend.export(currentDocument)

    def exportDialog(self):
        self.uiexportlayers = uiexportlayers.UIExportLayers()
        self.uiexportlayers.initialize()

#
#  SPDX-License-Identifier: GPL-3.0-or-later
#

from .ui import ExportUI
from .backend import ExportBackend, ExportConfig
import krita

class ExportLayersExtension(krita.Extension):
    def __init__(self, parent):
        super(ExportLayersExtension, self).__init__(parent)
        self.config = ExportConfig()

    def setup(self):
        self.backend = ExportBackend(self.config)

    def createActions(self, window):
        aAuto = window.createAction("export_layers_auto", i18n("Export Layers Auto"))
        aAuto.setToolTip(i18n("Run export layers job in background using default settings"))
        aAuto.triggered.connect(self.exportAuto)

        aDialog = window.createAction("export_layers_dialog", i18n("Export Layers Auto UI"))
        aDialog.setToolTip(i18n("Display export layers dialog"))
        aDialog.triggered.connect(self.exportDialog)

    def exportAuto(self):
        currentDocument = krita.Krita.instance().activeDocument()
        self.backend.export(currentDocument)

    def exportDialog(self):
        self.uiexportlayers = ExportUI(self.config)
        self.uiexportlayers.initialize()

Scripter.addExtension(ExportLayersExtension(krita.Krita.instance()))

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
        aCur = window.createAction("export-layers-auto-current", i18n("Export Layers Auto: Export Current Document"))
        aCur.setToolTip(i18n("Run export layers job in background using default settings"))
        aCur.triggered.connect(self.exportCurrent)

        aAll = window.createAction("export-layers-auto-all", i18n("Export Layers Auto: Export All Documents"))
        aAll.setToolTip(i18n("Run export layers job in background using default settings"))
        aAll.triggered.connect(self.exportAll)

        aUI = window.createAction("export-layers-ui", i18n("Export Layers Auto: Show UI"))
        aUI.setToolTip(i18n("Display export layers dialog"))
        aUI.triggered.connect(self.showUI)

    def exportCurrent(self):
        currentDocument = krita.Krita.instance().activeDocument()
        self.backend.export(currentDocument)

    def exportAll(self):
        all_jobs = []
        for document in krita.Krita.instance().documents():
            all_jobs += self.backend.generateJobs(document)

        self.backend.runJobs(all_jobs)

    def showUI(self):
        self.ui = ExportUI(self.config)
        self.ui.initialize()

## Add to Krita extensions (safely)
try:
    Scripter
except NameError:
    pass
else:
    Scripter.addExtension(ExportLayersExtension(krita.Krita.instance()))

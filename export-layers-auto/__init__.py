from collections.abc import Callable, Generator

import krita

from .backend import ExportBackend, ExportConfig
from .ui import ExportUI


class ExportLayersExtension(krita.Extension):
    def __init__(self, parent):
        super().__init__(parent)
        self.config = ExportConfig()
        self.id_prefix = "export-layers-auto"
        self.name_prefix = "Export Layers Auto:"

        self.instance : krita.Krita = krita.Krita.instance()

    def setup(self):
        self.backend = ExportBackend(self.instance, self.config)
        self.ui = ExportUI(self.backend, self.config)
        
    def _createAction(self, window, id : str, name : str, desc : str, func : Callable):
        aCur = window.createAction( 
            f"{self.id_prefix}-{id}",
            f"{self.name_prefix} {name}",
        )
        aCur.setToolTip( desc )
        aCur.triggered.connect(func)

    def createActions(self, window):
        self._createAction(
            window,
            id="current",
            name="Export Current Document",
            desc="Run export layers job in background using default settings",
            func=self.exportCurrent
        )
        
        self._createAction(
            window,
            id="all",
            name="Export All Documents",
            desc="Run export layers job in background using default settings",
            func=self.exportAll
        )
        
        self._createAction(
            window,
            id="show-ui",
            name="Show UI",
            desc="Display export layers dialog",
            func=self.showUI
        )

    @property
    def currentDocument(self) -> krita.Document:
        return self.instance.activeDocument()

    def allDocuments(self) -> Generator[krita.Document]:
        yield from self.instance.documents()

    def exportCurrent(self):
        self.backend.export(self.currentDocument)

    def exportAll(self):
        all_jobs = []
        for document in self.allDocuments():
            all_jobs += self.backend.generateJobs(document)

        self.backend.runJobs(all_jobs)

    def showUI(self):
        self.ui.update_widgets()
        self.ui.show()


## Add to Krita extensions (safely)
try:
    Scripter
except NameError:
    pass
else:
    Scripter.addExtension(ExportLayersExtension(krita.Krita.instance()))

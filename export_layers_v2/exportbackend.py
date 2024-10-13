from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import (Qt, QRect)
from dataclasses import dataclass
import os
import krita

@dataclass
class ExportBackend():
    batchMode : bool = True
    cropToImageBounds : bool = False
    groupAsLayer : bool = True
    exportFilterLayers : bool = False
    ignoreInvisibleLayers : bool = True
    imageFormat : str = "png"

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
        Application.setBatchmode(self.batchMode)

        self.width = document.width()
        self.height = document.height()
        self.res = document.resolution()

        docPath = document.fileName() if document.fileName() else '~/Untitled/Untitled.kra'
        docPathHead,docPathTail = os.path.split(docPath)
        docName, docExt = os.path.splitext(docPathTail)

        outDir = os.path.join(docPathHead, docName)

        self.mkdir(outDir)

        self._exportLayers(
            document.rootNode(),
            self.imageFormat,
            outDir)

        Application.setBatchmode(True)

        popup = QMessageBox()
        popup.setText(f"Exported layers to {outDir}") 
        popup.exec_()

    def _exportLayers(self, parentNode, fileFormat, parentDir):
        """ This method get all sub-nodes from the current node and export then in
            the defined format."""

        for node in parentNode.childNodes():
            newDir = ''
            if node.type() == 'grouplayer' and not self.groupAsLayer:
                newDir = os.path.join(parentDir, node.name())
                self.mkdir(newDir)
            elif (not self.exportFilterLayers and 'filter' in node.type()):
                continue
            elif (self.ignoreInvisibleLayers and not node.visible()):
                continue
            else:
                nodeName = node.name()
                _fileFormat = self.imageFormat
                if '[jpeg]' in nodeName:
                    _fileFormat = 'jpeg'
                elif '[png]' in nodeName:
                    _fileFormat = 'png'

                if self.cropToImageBounds:
                    bounds = QRect()
                else:
                    bounds = QRect(0, 0, self.width, self.height)

                layerFileName = f'{parentDir}/{node.name()}.{_fileFormat}'

                node.save(layerFileName, self.res / 72., self.res / 72., krita.InfoObject(), bounds)

            if node.childNodes() and not self.groupAsLayer:
                self._exportLayers(node, fileFormat, newDir)

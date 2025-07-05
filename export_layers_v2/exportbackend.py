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
    nameFormat : str = "{document_name} - {layer_name}"

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

        self.document = document

        docPath = document.fileName() if document.fileName() else '~/Untitled/Untitled.kra'
        docPathHead,docPathTail = os.path.split(docPath)
        docName, docExt = os.path.splitext(docPathTail)

        self.document_name = docName

        outDir = os.path.join(docPathHead, docName)

        self.mkdir(outDir)

        results = self._exportLayers(document.rootNode(), outDir)
        result_names = '\n'.join(results)

        Application.setBatchmode(True)

        popup = QMessageBox()
        popup.setText(f"Exported {len(results)} layers to {outDir}: \n {result_names}") 
        popup.exec_()

    def isLayerIgnored(self, node):
        if (not self.exportFilterLayers and 'filter' in node.type()):
            return True
        elif (self.ignoreInvisibleLayers and not node.visible()):
            return True
        return False

    def exportLayer(self, node, outname):
        nodeName = node.name()

        if self.cropToImageBounds:
            bounds = QRect()
        else:
            bounds = QRect(0, 0, self.width, self.height)

        try:
            node.save(outname, self.res / 72., self.res / 72., krita.InfoObject(), bounds)
        except Exception as e:
            print("Export error: {e}")
            return False

        return True

    def getOutname(self, node):
        self.nameFormat.replace("{document_name}", self.document_name)
        self.nameFormat.replace("{layer_name}", node.name())

        return f"{node.name()}.{self.imageFormat}"

    def _exportLayers(self, parentNode, parentDir):
        results = []
        for node in parentNode.childNodes():
            if(self.isLayerIgnored(node)):
                continue

            # Recursive make subdirectory + export group layer children
            if node.type() == 'grouplayer' and not self.groupAsLayer and node.childNodes():
                newDir = os.path.join(parentDir, node.name())
                self.mkdir(newDir)
                self._exportLayers(node, fileFormat, newDir)

            else:
                outname = f'{parentDir}/{self.getOutname(node)}'
                if(self.exportLayer(node, outname)):
                    results.append(outname)
        return results

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import (Qt, QRect)
from dataclasses import dataclass
import os
import krita

def mkdirSafe(directory):
    target_directory = directory
    if (os.path.exists(target_directory)
            and os.path.isdir(target_directory)):
        return

    try:
        os.makedirs(target_directory)
    except OSError as e:
        raise e

@dataclass
class ExportConfig():
    batchMode : bool = True
    cropToImageBounds : bool = False
    groupAsLayer : bool = True
    exportFilterLayers : bool = False
    ignoreInvisibleLayers : bool = True
    imageFormat : str = "png"
    nameFormat : str = "{document_name} - {layer_name}.{ext}"

class ExportBackend():
    def __init__(self, config):
        self.config = config

    def export(self, document):
        Application.setBatchmode(self.config.batchMode)

        document = document

        self.width = document.width()
        self.height = document.height()
        self.res = document.resolution()

        # Find root dir of document
        document_path = document.fileName() if document.fileName() else 'Untitled.kra'
        document_head, document_tail = os.path.split(document_path)
        self.document_name, document_ext = os.path.splitext(document_tail)

        mkdirSafe(document_head)

        results = self.exportLayers(document.rootNode(), document_head)
        result_names = '\n'.join(results)

        Application.setBatchmode(True)

        popup = QMessageBox()
        popup.setText(f"Exported {len(results)} layers to {document_head}: \n {result_names}") 
        popup.exec_()

    def isLayerIgnored(self, node):
        if (not self.config.exportFilterLayers and 'filter' in node.type()):
            return True
        elif (self.config.ignoreInvisibleLayers and not node.visible()):
            return True
        return False

    def exportLayer(self, node, outname):
        nodeName = node.name()

        if self.config.cropToImageBounds:
            bounds = QRect()
        else:
            bounds = QRect(0, 0, self.width, self.height)

        try:
            node.save(outname, self.res / 72., self.res / 72., krita.InfoObject(), bounds)
        except Exception as e:
            raise e
            return False

        return True

    def getOutname(self, node):
        return self.config.nameFormat.format(
            document_name = self.document_name,
            layer_name = node.name(),
            ext = self.config.imageFormat,
        )

    def exportLayers(self, parentNode, parentDir):
        results = []
        for node in parentNode.childNodes():
            if(self.isLayerIgnored(node)):
                continue

            # Recursive make subdirectory + export group layer children
            if node.type() == 'grouplayer' and not self.config.groupAsLayer and node.childNodes():
                #newDir = os.path.join(parentDir, node.name())
                #mkdirSafe(newDir)
                self.exportLayers(node, fileFormat, newDir)

            else:
                outname = f'{parentDir}/{self.getOutname(node)}'
                outname_head, outname_tail = os.path.split(outname)
                mkdirSafe(outname_head)
                if(self.exportLayer(node, outname)):
                    results.append(outname)
        return results

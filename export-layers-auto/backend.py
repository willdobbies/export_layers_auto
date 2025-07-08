from PyQt5.QtWidgets import (QMessageBox, QDialog, QApplication, QProgressDialog)
from PyQt5.QtCore import (Qt, QRect)
from dataclasses import dataclass
from functools import partial
import krita
import os

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
        all_jobs = self.generateJobs(document)
        self.runJobs(all_jobs)

    def generateJobs(self, document):
        Application.setBatchmode(self.config.batchMode)

        document = document

        self.width = document.width()
        self.height = document.height()
        self.res = document.resolution()

        # Find root dir of document
        document_path = document.fileName() if document.fileName() else 'Untitled.kra'
        document_head, document_tail = os.path.split(document_path)
        self.document_name, document_ext = os.path.splitext(document_tail)

        return self.exportLayers(document.rootNode(), document_head)

    def runJobs(self, jobs):
        progress = QProgressDialog("Exporting Layers...", "Cancel", 0, len(jobs))
        progress.setWindowModality(Qt.NonModal)

        progress.activateWindow()
        progress.show()

        for idx, job in enumerate(jobs):
            progress.setValue(idx)
            job()

        progress.setValue(len(jobs))
        progress.close()

        popup = QMessageBox()
        popup.setText(f"Exported {len(jobs)} layers") 
        popup.exec_()

    def isLayerIgnored(self, node):
        if (not self.config.exportFilterLayers and 'filter' in node.type()):
            return True
        elif (self.config.ignoreInvisibleLayers and not node.visible()):
            return True
        return False

    def exportLayer(self, node, path):
        nodeName = node.name()

        path_head, path_tail = os.path.split(path)
        mkdirSafe(path_head)

        if self.config.cropToImageBounds:
            bounds = QRect()
        else:
            bounds = QRect(0, 0, self.width, self.height)

        try:
            node.save(path, self.res / 72., self.res / 72., krita.InfoObject(), bounds)
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
        jobs = []
        for node in parentNode.childNodes():
            if(self.isLayerIgnored(node)):
                continue

            # Recursive make subdirectory + export group layer children
            if not self.config.groupAsLayer and node.type() == 'grouplayer' and node.childNodes():
                self.exportLayers(node, fileFormat, newDir)
            else:
                outname = f'{parentDir}/{self.getOutname(node)}'
                jobs.append(partial(self.exportLayer, node, outname))
        return jobs

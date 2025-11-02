from PyQt5.QtWidgets import (QMessageBox, QDialog, QApplication, QProgressDialog)
from PyQt5.QtCore import (Qt, QRect)
from dataclasses import dataclass
from functools import partial
import krita
import os

def mkdirSafe(directory):
    target_directory = directory

    try:
        os.makedirs(target_directory)
    except OSError as e:
        print(e)

@dataclass
class ExportConfig():
    cropToImageBounds : bool = False
    exportGroupChildren : bool = False
    exportGroupsMerged : bool = True
    ignoreFilterLayers : bool = True
    ignoreInvisibleLayers : bool = True
    imageFormat : str = "png"
    layerNameDelimeter : str = " - "
    prependDocumentName : bool = True

class ExportBackend():
    def __init__(self, config):
        self.config = config

    def export(self, document):
        all_jobs = self.generateJobs(document)
        self.runJobs(all_jobs)

    def prepend_outpath(self, outpath, document):
        directory,filename = os.path.split(document.fileName())
        basename,extension = os.path.splitext(filename)

        if(self.config.prependDocumentName):
            outpath = self.config.layerNameDelimeter.join([basename, outpath])

        return os.path.join(directory, outpath)

    def generateJobs(self, document):
        outpaths = self.getNodeOutPaths(document.rootNode())

        jobs = []
        for node,outpath in outpaths:
            outpath = self.prepend_outpath(outpath, document)

            newJob = partial(
                self.exportLayer,
                node=node,
                outpath=outpath,
                document=document,
            )

            jobs.append(newJob)

        return jobs

    def runJobs(self, jobs):
        Application.setBatchmode(True)

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

    def shouldProcessLayer(self, node):
        if (self.config.ignoreInvisibleLayers):
            if(not node.visible()):
                return False

        if (self.config.ignoreFilterLayers):
            if('filter' in node.type()):
                return False

        return True

    def getOutName(self, targetNode, parentChain):
        nameChain = [] + [node.name() for node in parentChain + [targetNode]]

        #if(self.config.createGroupDirectories):
        #    self.layerNameDelimeter = "/"

        outname = self.config.layerNameDelimeter.join(nameChain) + f".{self.config.imageFormat}"

        #if(self.config.createBaseDirectory):
        #    outname = self.document_name + "/" + outname

        return outname

    def exportLayer(self, node, outpath, document):

        head, tail = os.path.split(outpath)
        mkdirSafe(head)

        if self.config.cropToImageBounds:
            bounds = QRect()
        else:
            bounds = QRect(0, 0, document.width(), document.height())

        try:
            node.save(
                outpath, 
                document.resolution() / 72., 
                document.resolution() / 72., 
                krita.InfoObject(), 
                bounds
            )
        except Exception as e:
            raise e
            return False

        return True

    def getNodeOutPaths(self, targetNode, parentChain=[]):
        """
        Recursively get layers to process & their output paths

        :param parentNode: The node to export
        :param parentChain: The current chain of nodes leading to head
        :return: list of tuples containing (node to export, output path)
        """
        results = []

        if(not self.shouldProcessLayer(targetNode)):
            return results

        all_names = [node.name() for node in parentChain]
        print(targetNode.type())
        print(targetNode.parentNode())
        print(f"getNodeOutPaths: {targetNode.name()}", "ParentChain:", all_names, f"Children: {targetNode.childNodes()}")

        # Root node!
        if(targetNode.parentNode() == None):
            for childNode in targetNode.childNodes():
                results += self.getNodeOutPaths(childNode, [])
            return results

        if(targetNode.type() == 'grouplayer'):
            # Skip exporting the group layer 'heads' (merged contents of group layer)
            if(self.config.exportGroupsMerged):
                outName = self.getOutName(targetNode, parentChain)
                results.append((targetNode,outName))

            # Recursive export if encounter group layer and flatten opt is disabled
            if(self.config.exportGroupChildren):
                for childNode in targetNode.childNodes():
                    results += self.getNodeOutPaths(childNode, parentChain + [targetNode])

        else:
            # Regular single-layer export
            outName = self.getOutName(targetNode, parentChain)
            results.append((targetNode,outName))

        return results

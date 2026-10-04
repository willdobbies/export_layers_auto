from dataclasses import dataclass
from functools import partial
from pathlib import Path

import krita
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtWidgets import QProgressDialog


@dataclass
class ExportConfig:
    cropToImageBounds: bool = False
    exportGroupChildren: bool = False
    exportGroupsMerged: bool = True
    ignoreFilterLayers: bool = True
    ignoreInvisibleLayers: bool = True
    imageFormat: str = "png"
    layerNameDelimeter: str = "_"
    prependDocumentName: bool = True


@dataclass
class NodeExport:
    node: krita.Node
    path: Path


class ExportBackend:
    def __init__(self, instance: krita.Krita, config: ExportConfig):
        self.instance = instance
        self.config = config
        self.exported_memory = []

    def export(self, document: krita.Document):
        all_jobs = self.generateJobs(document)
        self.runJobs(all_jobs)

    def generateJobs(self, document: krita.Document) -> list[partial]:
        root = document.rootNode()
        if not root:
            return []
        targetNodes = self.getTargetNodes(root)
        print(f"Got {len(targetNodes)} target nodes")

        for n in targetNodes:
            print(f"- {self.getNodeNameChainStr(n)}")

        doc_basename = Path(document.fileName()).with_suffix("").name
        prefix = doc_basename if self.config.prependDocumentName else ""
        outpaths = [self.getNodeOutpath(n, prefix) for n in targetNodes]

        # ensure unique paths here

        to_process = zip(targetNodes, outpaths)

        jobs = []
        for node, outpath in to_process:
            newJob = partial(
                self.exportLayer,
                node=node,
                outpath=outpath,
                document=document,
            )

            jobs.append(newJob)

        return jobs

    def runJobs(self, jobs: list[partial]):
        self.instance.setBatchmode(True)
        count = len(jobs)

        progress = QProgressDialog(
            "Exporting Layers...",
            "Cancel",
            0,
            count,
            None,
            Qt.WindowType.Popup,
        )
        # progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setAutoClose(False)
        progress.show()

        for idx, job in enumerate(jobs):
            job()
            progress.setValue(idx)
        progress.setValue(count)

        progress.setLabelText(f"Exported {count} layers OK")
        progress.exec_()

    def getNodeNameChain(self, targetNode : krita.Node) -> list[str]:
        parentChain = self.getParentChain(targetNode)
        return [node.name() for node in parentChain]

    def getNodeOutpath(self, targetNode: krita.Node, prefix: str) -> Path:
        """
        Gets relative output path of a node export job
        """

        nameChain = self.getNodeNameChain(targetNode)[1:]
        if prefix:
            nameChain.insert(0, prefix)

        print(nameChain)

        delim = self.config.layerNameDelimeter
        ext = self.config.imageFormat

        outpath = Path(delim.join(nameChain)).with_suffix(f".{ext}")

        return outpath

    def getParentChain(self, targetNode: krita.Node) -> list[krita.Node]:
        """
        Traverse up a node parent linked list until root is hit
        """
        iter = targetNode
        chain = []
        while iter != None:
            chain.insert(0, iter)
            iter = iter.parentNode()

        return chain

    def exportLayer(self, node: krita.Node, outpath: Path, document: krita.Document):
        """
        Export layer image data to a given path
        :param node: Node (layer) to export
        :param outpath: Path to write out file. Warning, will overwrite existing files!
        :param document: The Krita document object node belongs to
        """

        outpath.parent.mkdir(exist_ok=True)

        if self.config.cropToImageBounds:
            bounds = QRect()
        else:
            bounds = QRect(0, 0, document.width(), document.height())

        print(f"Exporting '{outpath}'")
        node.save(
            str(outpath),
            document.resolution() / 72.0,
            document.resolution() / 72.0,
            krita.InfoObject(),
            bounds,
        )

    def layerIsIgnored(self, node: krita.Node) -> bool:
        if self.config.ignoreInvisibleLayers and not node.visible():
            return False

        if self.config.ignoreFilterLayers and "filter" in node.type():
            return False

        return node != None

    def getNodeNameChainStr(self, targetNode: krita.Node) -> str:
        return "/".join(self.getNodeNameChain(targetNode))

    def getTargetNodes(self, targetNode: krita.Node) -> list[krita.Node]:
        """
        Recursively finds all nodes to be exported during a job

        :param n: The node to scan
        :return: list of nodes to export
        """
        if not self.layerIsIgnored(targetNode):
            print("Ignoring", self.getNodeNameChainStr(targetNode))
            return []

        is_root = targetNode.parentNode() == None

        if (
            targetNode.type() == "grouplayer"
            and self.config.exportGroupsMerged
            and not is_root
        ):
            print("Add group layer", self.getNodeNameChainStr(targetNode))
            return [targetNode]

        results = []
        for n in targetNode.childNodes():
            print("Recurse parsing", self.getNodeNameChainStr(n))
            results += self.getTargetNodes(n)
        
        if(not is_root):
            results.append(targetNode)
        
        return results

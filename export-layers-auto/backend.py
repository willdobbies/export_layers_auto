import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory

import krita
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtWidgets import QProgressDialog


class ImageFormat(Enum):
    PNG = "png"
    JPG = "jpg"


@dataclass
class ExportConfig:
    cropToImageBounds: bool = False
    """
    Crop outputs to the bounds of individual layer content
    """
    
    exportGroupsMerged: bool = True
    """
    Create merged outputs for groups instead of recursively handling each.
    """
    
    ignoreFilterLayers: bool = True
    """
    Exclude filter layers from outputs
    """
    
    ignoreInvisibleLayers: bool = True
    """
    Exclude hidden/invisible layers from outputs
    """
    
    # imageFormat: ImageFormat = ImageFormat.PNG
    # """
    # Target image format of outputs
    # """
    
    layerNameDelimeter: str = "_"
    """
    Output paths are determined based on document layer heirarchy.
    This option determines what delimeter to use between parts of the name
    If '/', creates subfolders for layers.
    """
    
    prependDocumentName: bool = True
    """
    Prepend the document name to every output
    """
    
    exportAnimations: bool = True
    """
    Export frames for animated layers, and combine into video.
    Layers with 1+ keyframes will be exported as transparent, lossless webm files.
    Requires `ffmpeg` command to be available in system path.
    """


class ExportBackend:
    def __init__(self, instance: krita.Krita, config: ExportConfig):
        self.instance = instance
        self.config = config

    def export(self, document: krita.Document):
        all_jobs = self.generateJobs(document)
        self.runJobs(all_jobs)

    def generateJobs(self, document: krita.Document) -> list[partial]:
        """
        Set up export image jobs
        """

        root = document.rootNode()
        if not root:
            return []

        # Identify all nodes (layers which should be exported)
        targetNodes = self.getTargetNodes(root)
        print(f"Got {len(targetNodes)} target nodes")

        for n in targetNodes:
            print(f"- {'/'.join(self.getNodeNameChain(n))}")

        # Get path to target document being exported
        doc_path = Path(document.fileName())

        # Determine output filepaths from target nodes
        outpaths = [self.getNodeOutpath(n, doc_path) for n in targetNodes]

        # TODO: ensure unique paths here!

        to_process = zip(targetNodes, outpaths)

        # create the job functions (partials) to be run
        jobs = []
        for node, outpath in to_process:
            is_animated = (
                self.getLayerFrameCount(node, document.fullClipRangeEndTime()) > 1
                and self.config.exportAnimations
            )

            export_func = self.exportAnimatedLayer if is_animated else self.exportLayer

            newJob = partial(
                export_func,
                node=node,
                outpath=outpath,
                document=document,
            )

            jobs.append(newJob)

        return jobs

    def runJobs(self, jobs: list[partial]):
        """
        Run a collection of export jobs, set up as function partials. Display progress bar.
        """

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

    def getNodeNameChain(self, targetNode: krita.Node) -> list[str]:
        """
        Get list of node names from parent chain
        """
        parentChain = self.getParentChain(targetNode)
        return [node.name() for node in parentChain]

    def getNodeOutpath(self, targetNode: krita.Node, docPath: Path) -> Path:
        """
        Gets relative output path of a node export job
        """
        nameChain = self.getNodeNameChain(targetNode)[1:]

        # Derive prefix from document filename
        if self.config.prependDocumentName:
            prefix = docPath.with_suffix("").name
            nameChain.insert(0, prefix)

        # print(nameChain)

        delim = self.config.layerNameDelimeter
        ext = "png" #self.config.imageFormat

        outpath = Path(delim.join(nameChain)).with_suffix(f".{ext}")

        return docPath.parent / outpath

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

    def getBounds(self, document: krita.Document) -> QRect:
        if self.config.cropToImageBounds:
            return QRect()
        return QRect(0, 0, document.width(), document.height())

    def getResolution(self, document: krita.Document) -> tuple[float, float]:
        return (
            document.resolution() / 72.0,
            document.resolution() / 72.0,
        )

    def exportLayer(self, node: krita.Node, outpath: Path, document: krita.Document):
        """
        Export layer image data to a given path
        :param node: Node (layer) to export
        :param outpath: Path to write out file. Warning, will overwrite existing files!
        :param document: The Krita document object node belongs to
        """

        outpath.parent.mkdir(parents=True, exist_ok=True)

        xRes, yRes = self.getResolution(document)
        bounds = self.getBounds(document)

        print(f"Exporting '{outpath}'")
        node.save(
            str(outpath),
            xRes,
            yRes,
            krita.InfoObject(),
            bounds,
        )

    def exportAnimatedLayer(
        self, node: krita.Node, outpath: Path, document: krita.Document
    ):
        # Export frames to temp location
        xRes, yRes = self.getResolution(document)
        bounds = self.getBounds(document)

        total_frame_count = document.fullClipRangeEndTime()
        frame_padding = len(str(total_frame_count))

        tmpdir = TemporaryDirectory()
        # outpath = Path(tmpdir.name) / outpath.name
        tmpdir_path = Path(tmpdir.name)

        # export all frames to temp location
        frame_times = self.getLayerFrameTimes(node, total_frame_count)

        def get_frame_path(idx: int) -> Path:
            idx_str = str(idx).zfill(frame_padding)
            return tmpdir_path / f"frame_{idx_str}{outpath.suffix}"

        last_export_frame = 0
        for frame in range(total_frame_count):
            outpath_frame = get_frame_path(frame)

            if frame in frame_times:
                last_export_frame = frame
                print(f"Exporting (frame {frame}) - '{outpath_frame}'")
                document.setCurrentTime(frame)
                node.save(
                    str(outpath_frame),
                    xRes,
                    yRes,
                    krita.InfoObject(),
                    bounds,
                )
            else:
                prev_frame = get_frame_path(last_export_frame)
                print(
                    f"Copying dupe frame (frame {frame}) - '{prev_frame}' -> '{outpath_frame}'"
                )
                shutil.copy(prev_frame, outpath_frame)

        # run ffmpeg commmand to combine to lossless webm
        print("combining frames into lossless webm with FFmpeg")

        command = [
            "ffmpeg",
            "-hide_banner",
            "-y",
            "-y",
            "-r",
            str(document.framesPerSecond()),
            "-start_number",
            "0",
            "-start_number_range",
            "1",
            "-i",
            f"frame_%{frame_padding:02d}d.png",
            "-c:v",
            "libvpx-vp9",
            "-lossless",
            "1",
            str(outpath.with_suffix(".webm")),
        ]

        print(f"Command: {command}")

        subprocess.run(command, cwd=tmpdir_path, check=False)

    def layerIsIgnored(self, node: krita.Node) -> bool:
        """
        Determine whether a document layer should be ignored
        """
        if self.config.ignoreInvisibleLayers and not node.visible():
            return False

        if self.config.ignoreFilterLayers and "filter" in node.type():
            return False

        return node != None

    def getTargetNodes(self, targetNode: krita.Node) -> list[krita.Node]:
        """
        Recursively finds all nodes to be exported during a job

        :param n: The node to scan
        :return: list of nodes to export
        """
        if not self.layerIsIgnored(targetNode):
            return []

        is_root = targetNode.parentNode() == None

        if (
            targetNode.type() == "grouplayer"
            and self.config.exportGroupsMerged
            and not is_root
        ):
            return [targetNode]

        results = []
        for n in targetNode.childNodes():
            results += self.getTargetNodes(n)

        if not is_root:
            results.append(targetNode)

        return results

    def getLayerFrameTimes(self, node: krita.Node, total_frame_count: int) -> set[int]:
        """
        Returns unique set of indicies that layer has animation frames on
        :param node: layer to scan for frames. If targetting group layer, recursively scan child layers and combine results
        """
        hits = set()
        if node.type() == "grouplayer":
            for c in node.childNodes():
                hits |= self.getLayerFrameTimes(c, total_frame_count)
        else:
            for i in range(total_frame_count):
                if node.hasKeyframeAtTime(i):
                    hits.add(i)
        return hits

    def getLayerFrameCount(self, node: krita.Node, total_frame_count: int) -> int:
        return len(self.getLayerFrameTimes(node, total_frame_count))

    def isLayerAnimated(self, node: krita.Node) -> bool:
        if node.type() != "grouplayer":
            return node.animated()

        for c in node.childNodes():
            if self.isLayerAnimated(c):
                return True
        return False

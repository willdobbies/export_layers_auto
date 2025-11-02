import pytest
import time
from backend import ExportConfig, ExportBackend
from PyQt5.QtWidgets import QApplication, QWidget
import krita

@pytest.fixture
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

#def test_backend(app):
#    config = ExportConfig()
#    backend = ExportBackend(config)
#    backend.runJobs([
#        lambda: print("hi"),
#        #lambda: time.sleep(1),
#        lambda: print("Bye"),
#    ])

class DummyLayer():
    def __init__(self, nodeName="", children=[], parent=None, isVisible=True, layerType="normal"):
        self.nodeName = nodeName
        self.children = children
        for child in self.children:
            child.parent = self

        self.parent = parent 
        self.layerType = layerType
        self.isVisible = isVisible

    def name(self):
        return self.nodeName

    def parentNode(self):
        return self.parent
    
    def childNodes(self):
        return self.children

    def visible(self):
        return self.isVisible

    def type(self):
        return self.layerType

class DummyDocument():
    def __init__(self, root):
        self.root = root

    def fileName(self):
        return "/home/user/Documents/mydocument.kra"

    def rootNode(self):
        return self.root

    def width():
        return 1920

    def height():
        return 1080

    def resolution():
        return 90

@pytest.fixture
def dummy_layer_group():
    # Construct some dummy layers
    # Group/
    # - Layer 1
    # - Layer 2 (Hidden)
    # - Layer 3
    # - Layer 4 (Filter)
    layer1 = DummyLayer("Layer 1")
    layer2 = DummyLayer("Layer 2", isVisible=False)
    layer3 = DummyLayer("Layer 3")
    layer4 = DummyLayer("Filter", layerType="filter")
    group = DummyLayer("Group", children=[layer1,layer2,layer3,layer4], layerType="grouplayer")
    return DummyLayer("Root", children=[group], layerType="grouplayer")

def test_job_paths_default(app, dummy_layer_group):
    config = ExportConfig()
    backend = ExportBackend(config)

    outpaths = backend.getNodeOutPaths(dummy_layer_group)

    # Groups flattened. Should get a single image output
    assert(outpaths[0][1] == "Group.png")
    assert(len(outpaths) == 1)

def test_job_paths_no_flatten(app, dummy_layer_group):
    config = ExportConfig()
    backend = ExportBackend(config)

    backend.config.exportGroupChildren = True

    outpaths = backend.getNodeOutPaths(dummy_layer_group)

    # Groups flattened. Should get a single image output
    assert(outpaths[0][1] == "Group.png")
    assert(outpaths[1][1] == "Group - Layer 1.png")
    assert(outpaths[2][1] == "Group - Layer 3.png")
    assert(len(outpaths) == 3)

def test_job_paths_layer_folders(app, dummy_layer_group):
    config = ExportConfig()
    backend = ExportBackend(config)

    backend.config.exportGroupsMerged = False
    backend.config.exportGroupChildren = True
    backend.config.ignoreInvisibleLayers = False
    backend.config.layerNameDelimeter = "/"

    outpaths = backend.getNodeOutPaths(dummy_layer_group)

    # Groups flattened. Should get a single image output
    assert(outpaths[0][1] == "Group/Layer 1.png")
    assert(outpaths[1][1] == "Group/Layer 2.png")
    assert(outpaths[2][1] == "Group/Layer 3.png")
    assert(len(outpaths) == 3)

def test_document_export(app, dummy_layer_group, monkeypatch):
    config = ExportConfig()
    backend = ExportBackend(config)

    backend.config.exportGroupsMerged = False
    backend.config.exportGroupChildren = True
    backend.config.ignoreInvisibleLayers = False
    backend.config.prependDocumentName = True

    document = DummyDocument(root=dummy_layer_group)

    jobs = backend.generateJobs(document)

    assert(jobs[0].keywords['outpath'] == "/home/user/Documents/mydocument - Group - Layer 1.png")
    assert(jobs[1].keywords['outpath'] == "/home/user/Documents/mydocument - Group - Layer 2.png")
    assert(jobs[2].keywords['outpath'] == "/home/user/Documents/mydocument - Group - Layer 3.png")
    assert(len(jobs) == 3)

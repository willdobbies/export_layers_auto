import pytest
import time
from backend import ExportConfig, ExportBackend

@pytest.fixture
def app():
    app = QApplication.instance()
    if app is None:
        # if it does not exist then a QApplication is created
        app = QApplication([])
    return app

#def test_qt(app):
#    popup = QMessageBox()
#    popup.setText("FOOBAR") 
#    popup.exec_()

def test_backend(app):
    config = ExportConfig()
    backend = ExportBackend(config)
    backend.runJobs([
        lambda: print("hi"),
        lambda: time.sleep(1),
        lambda: print("Bye"),
    ])
    #assert(False)

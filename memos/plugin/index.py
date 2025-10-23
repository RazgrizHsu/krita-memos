"""
Krita Memos Plugin - Main Extension
"""

from krita import Extension, DockWidgetFactory, DockWidgetFactoryBase, Krita
from .docker import MemosDocker


class MemosExtension(Extension):

    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction(
            "memos_toggle",
            "Memos",
            "tools"
        )
        action.triggered.connect(self.toggleDocker)

    def toggleDocker(self):
        activeWin = Krita.instance().activeWindow()
        if activeWin:
            dockers = activeWin.dockers()
            for docker in dockers:
                if docker.objectName() == "memos_docker":
                    docker.setVisible(not docker.isVisible())
                    return


def createDockWidget():
    return Krita.instance().addDockWidgetFactory(
        DockWidgetFactory(
            "memos_docker",
            DockWidgetFactoryBase.DockRight,
            MemosDocker
        )
    )


from .log import lg

lg.log("=" * 50)
lg.log("Memos: Initializing...")
lg.log("=" * 50)

try:
    Krita.instance().addExtension(MemosExtension(Krita.instance()))
    lg.log("Extension registered")

    createDockWidget()
    lg.log("Docker registered")

    lg.log("=" * 50)
    lg.log("Memos: Ready")
    lg.log("=" * 50)
except Exception as e:
    lg.error(f"Failed to register plugin: {e}")
    import traceback
    traceback.print_exc()

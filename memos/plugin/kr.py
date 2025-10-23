import numpy as np
from PyQt5.QtCore import QByteArray
from krita import Krita


class OpLayer:

    @staticmethod
    def getActiveLayer():
        doc = Krita.instance().activeDocument()
        if doc is None:
            return None
        return doc.activeNode()

    @staticmethod
    def isLayerLocked(layer):
        if layer is None:
            return True
        return layer.locked()

    @staticmethod
    def getSelection():
        doc = Krita.instance().activeDocument()
        if doc is None:
            return None
        return doc.selection()

    @staticmethod
    def getSelectionBounds(selection):
        if selection is None:
            return None
        return {
            'x': selection.x(),
            'y': selection.y(),
            'width': selection.width(),
            'height': selection.height()
        }

    @staticmethod
    def getLayerBounds(layer):
        if layer is None:
            return None
        bounds = layer.bounds()
        return {
            'x': bounds.x(),
            'y': bounds.y(),
            'width': bounds.width(),
            'height': bounds.height()
        }

    @staticmethod
    def readPixelData(layer, x, y, w, h):
        if layer is None:
            return None

        pixelData = layer.pixelData(x, y, w, h)
        data = pixelData.data()

        arr = np.frombuffer(data, dtype=np.uint8)
        arr = arr.reshape((h, w, 4))

        return arr

    @staticmethod
    def writePixelData(layer, arr, x, y):
        if layer is None:
            return False

        h, w = arr.shape[:2]

        ba = QByteArray(arr.tobytes())
        layer.setPixelData(ba, x, y, w, h)

        return True

    @staticmethod
    def refreshDocument():
        doc = Krita.instance().activeDocument()
        if doc is None:
            return False

        try:
            rootNode = doc.rootNode()
            if rootNode is None:
                return False
            doc.refreshProjection()
            return True
        except:
            return False

    @staticmethod
    def readFullLayer(layer):
        if layer is None:
            return None, None

        bounds = OpLayer.getLayerBounds(layer)
        if bounds is None:
            return None, None

        arr = OpLayer.readPixelData(
            layer,
            bounds['x'],
            bounds['y'],
            bounds['width'],
            bounds['height']
        )

        return arr, bounds

    @staticmethod
    def writeFullLayer(layer, arr, bounds):
        success = OpLayer.writePixelData(
            layer,
            arr,
            bounds['x'],
            bounds['y']
        )

        if success:
            OpLayer.refreshDocument()

        return success

    @staticmethod
    def createLayer(name="New Layer"):
        doc = Krita.instance().activeDocument()
        if doc is None:
            return None

        activeNode = doc.activeNode()
        if activeNode is None:
            return None

        newLayer = doc.createNode(name, "paintLayer")
        parent = activeNode.parentNode()

        if parent:
            parent.addChildNode(newLayer, activeNode)
        else:
            doc.rootNode().addChildNode(newLayer, activeNode)

        return newLayer

    @staticmethod
    def duplicateLayer(layer, name=None):
        if layer is None:
            return None

        newLayer = layer.duplicate()

        if name:
            newLayer.setName(name)
        else:
            newLayer.setName(layer.name() + " (copy)")

        return newLayer


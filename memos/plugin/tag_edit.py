from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLineEdit, QCompleter, QLabel, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from .i18n import i18n


class TagChip(QFrame):
    removed = pyqtSignal(str)

    def __init__(self, tag, parent=None):
        super().__init__(parent)
        self.tag = tag

        layout = QHBoxLayout()
        layout.setContentsMargins(6, 3, 6, 3)
        layout.setSpacing(4)

        self.label = QLabel(f"#{tag}")
        font = self.label.font()
        font.setPointSize(font.pointSize() - 1)
        self.label.setFont(font)

        self.removeBtn = QPushButton("×")
        self.removeBtn.setFixedSize(14, 14)
        self.removeBtn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                font-weight: bold;
                font-size: 12px;
                padding: 0px;
                color: palette(text);
            }
            QPushButton:hover {
                color: red;
            }
        """)
        self.removeBtn.clicked.connect(lambda: self.removed.emit(self.tag))

        layout.addWidget(self.label)
        layout.addWidget(self.removeBtn)

        self.setLayout(layout)
        self.setStyleSheet("""
            QFrame {
                background-color: palette(button);
                border: 2px solid palette(mid);
                border-radius: 10px;
            }
        """)


class TagEdit(QWidget):
    tagsChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tags = []
        self.allTags = []

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(4)

        self.tagsLayout = QHBoxLayout()
        self.tagsLayout.setContentsMargins(0, 0, 0, 0)
        self.tagsLayout.setSpacing(4)
        self.tagsLayout.addStretch()
        mainLayout.addLayout(self.tagsLayout)

        self.input = QLineEdit()
        self.input.setPlaceholderText(i18n("Type tag and press Enter"))
        self.input.returnPressed.connect(self.addTagFromInput)

        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.input.setCompleter(self.completer)

        mainLayout.addWidget(self.input)

        self.setLayout(mainLayout)

    def setAvailableTags(self, tags):
        self.allTags = tags
        from PyQt5.QtCore import QStringListModel
        model = QStringListModel(tags)
        self.completer.setModel(model)

    def addTagFromInput(self):
        from .log import lg
        text = self.input.text().strip()
        if not text:
            return

        tag = text.lstrip("#").strip()
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.addTagChip(tag)
            lg.log(f"TagEdit: emitting tagsChanged after adding '{tag}'")
            self.tagsChanged.emit()

        self.input.clear()

    def addTagChip(self, tag):
        chip = TagChip(tag)
        chip.removed.connect(self.removeTag)
        self.tagsLayout.insertWidget(self.tagsLayout.count() - 1, chip)

    def removeTag(self, tag):
        from .log import lg
        self.tags.remove(tag)
        for i in range(self.tagsLayout.count()):
            widget = self.tagsLayout.itemAt(i).widget()
            if isinstance(widget, TagChip) and widget.tag == tag:
                widget.deleteLater()
                break
        lg.log(f"TagEdit: emitting tagsChanged after removing '{tag}'")
        self.tagsChanged.emit()

    def setTags(self, tags):
        self.clearTags()
        self.tags = tags[:]
        for tag in tags:
            self.addTagChip(tag)

    def getTags(self):
        return self.tags[:]

    def clearTags(self):
        self.tags = []
        while self.tagsLayout.count() > 0:
            item = self.tagsLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def clear(self):
        self.clearTags()
        self.input.clear()

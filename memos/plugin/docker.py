from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel,
    QLineEdit, QTextEdit, QListWidget, QListWidgetItem,
    QComboBox, QSplitter, QMessageBox, QApplication, QMenu
)
from PyQt5.QtCore import Qt, QTimer, QRect
from krita import DockWidget, Krita

from .memo import Memo, MemoStore
from .i18n import i18n
from .tag_edit import TagEdit


class MemoListItem(QWidget):
    def __init__(self, memo, parent=None):
        super().__init__(parent)
        self.memo = memo

        layout = QGridLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(0)

        from datetime import datetime
        from PyQt5.QtGui import QPalette
        dt = datetime.fromisoformat(memo.modified)
        dtStr = dt.strftime("%Y/%m/%d %H:%M:%S")

        self.dateLabel = QLabel(dtStr)

        palette = self.dateLabel.palette()
        textColor = palette.color(QPalette.WindowText)
        self.dateLabel.setStyleSheet(
            f"font-size: 9px; color: rgba({textColor.red()}, {textColor.green()}, {textColor.blue()}, 0.4);"
        )

        layout.addWidget(self.dateLabel, 0, 0)

        preview = memo.content[:50]
        if len(memo.content) > 50:
            preview += "..."

        self.contentLabel = QLabel(preview)
        layout.addWidget(self.contentLabel, 0, 1)

        self.copyBtn = QPushButton()
        self.copyBtn.setIcon(Krita.instance().icon("edit-copy"))
        self.copyBtn.setFixedSize(24, 24)
        self.copyBtn.setToolTip(i18n("Copy"))
        layout.addWidget(self.copyBtn, 0, 2)

        self.editBtn = QPushButton()
        self.editBtn.setIcon(Krita.instance().icon("document-edit"))
        self.editBtn.setFixedSize(24, 24)
        self.editBtn.setToolTip(i18n("Edit"))
        layout.addWidget(self.editBtn, 0, 3)

        self.deleteBtn = QPushButton("✕")
        self.deleteBtn.setFixedSize(24, 24)
        self.deleteBtn.setToolTip(i18n("Delete"))
        self.deleteBtn.setStyleSheet("""
            QPushButton {
                color: #ff7676;
                font-size: 16px;
                font-weight: bold;
                border: none;
                background: transparent;
            }
            QPushButton:hover {
                color: #ff0000;
            }
        """)
        layout.addWidget(self.deleteBtn, 0, 4)

        layout.setColumnStretch(1, 1)

        self.setLayout(layout)


class MemosDocker(DockWidget):

    def __init__(self):
        from .log import lg
        super().__init__()
        self.setWindowTitle(i18n("Memos"))

        self.store = MemoStore()
        self.currentMemo = None
        self.hasUnsavedChanges = False
        self.lastSavedContent = ""
        self.lastSavedTags = []
        self.deletedMemos = []

        self.autoSaveTimer = QTimer(self)
        self.autoSaveTimer.setSingleShot(True)
        self.autoSaveTimer.timeout.connect(self.onAutoSave)

        self.setupUI()
        self.connectSignals()
        self.connectKritaSignals()
        # lg.log("Docker __init__ complete")

    def setupUI(self):
        mainWidget = QWidget(self)
        self.setWidget(mainWidget)

        layout = QVBoxLayout()
        mainWidget.setLayout(layout)

        topLayout = QHBoxLayout()
        self.newBtn = QPushButton(i18n("New Memo"))
        self.newBtn.setIcon(Krita.instance().icon("document-new"))
        topLayout.addWidget(self.newBtn)

        self.searchInput = QLineEdit()
        self.searchInput.setPlaceholderText(i18n("Search..."))
        topLayout.addWidget(self.searchInput)

        topLayout.addWidget(QLabel(i18n("Tag:")))
        self.tagFilter = QComboBox()
        self.tagFilter.addItem(i18n("All"))
        topLayout.addWidget(self.tagFilter)

        layout.addLayout(topLayout)

        splitter = QSplitter(Qt.Vertical)

        self.memoList = QListWidget()
        self.memoList.setSpacing(1)
        self.memoList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.memoList.customContextMenuRequested.connect(self.showContextMenu)
        splitter.addWidget(self.memoList)

        self.editorWidget = QWidget()
        editorLayout = QGridLayout()
        self.editorWidget.setLayout(editorLayout)

        self.contentEdit = QTextEdit()
        self.contentEdit.setPlaceholderText(i18n("Memo content..."))
        editorLayout.addWidget(self.contentEdit, 0, 0)

        buttonsLayout = QVBoxLayout()
        buttonsLayout.setSpacing(4)

        self.copyBtn = QPushButton(i18n("Copy"))
        self.copyBtn.setIcon(Krita.instance().icon("edit-copy"))
        buttonsLayout.addWidget(self.copyBtn)

        self.saveBtn = QPushButton(i18n("Save"))
        self.saveBtn.setIcon(Krita.instance().icon("document-save"))
        buttonsLayout.addWidget(self.saveBtn)

        buttonsLayout.addStretch()

        from PyQt5.QtWidgets import QFrame
        buttonsFrame = QFrame()
        buttonsFrame.setLayout(buttonsLayout)
        editorLayout.addWidget(buttonsFrame, 0, 1, Qt.AlignTop)

        tagsRow = QHBoxLayout()
        tagsRow.addWidget(QLabel(i18n("Tags:")))
        self.tagsEdit = TagEdit()
        tagsRow.addWidget(self.tagsEdit, 1)
        editorLayout.addLayout(tagsRow, 1, 0)

        splitter.addWidget(self.editorWidget)
        layout.addWidget(splitter)

        self.editorWidget.hide()

    def connectSignals(self):
        self.searchInput.textChanged.connect(self.onSearchChanged)
        self.tagFilter.currentIndexChanged.connect(self.onFilterChanged)
        self.memoList.itemClicked.connect(self.onMemoSelected)
        self.newBtn.clicked.connect(self.onNew)
        self.copyBtn.clicked.connect(self.onCopy)
        self.saveBtn.clicked.connect(self.onSave)

        self.contentEdit.textChanged.connect(self.onContentChanged)
        self.tagsEdit.tagsChanged.connect(self.onContentChanged)

    def connectKritaSignals(self):
        from .log import lg
        app = Krita.instance()
        app.notifier().setActive(True)
        app.notifier().windowCreated.connect(self.onDocumentChanged)
        app.notifier().viewCreated.connect(self.onDocumentChanged)
        app.notifier().viewClosed.connect(self.onDocumentChanged)

        lg.log("Checking for active document on init...")
        self.onDocumentChanged()

    def onDocumentChanged(self):
        from .log import lg
        try:
            app = Krita.instance()
            doc = app.activeDocument()
            if doc:
                lg.log(f"Document changed: {doc.fileName()}")
                self.store.set_document(doc)
                self.currentMemo = None
                self.editorWidget.hide()
                self.memoList.clearSelection()
                self.refreshFilters()
                self.refreshList()
            else:
                lg.log("No active document")
        except Exception as e:
            lg.error(f"onDocumentChanged error: {e}")
            import traceback
            traceback.print_exc()

    def refreshFilters(self):
        self.tagFilter.blockSignals(True)

        curTag = self.tagFilter.currentText()

        self.tagFilter.clear()
        self.tagFilter.addItem(i18n("All"))
        for tag in self.store.get_hashtags():
            self.tagFilter.addItem(tag)

        idx = self.tagFilter.findText(curTag)
        if idx >= 0:
            self.tagFilter.setCurrentIndex(idx)

        self.tagFilter.blockSignals(False)
        self.tagsEdit.setAvailableTags(self.store.get_hashtags())

    def refreshList(self):
        self.memoList.clear()

        memos = self.store.memos[:]

        query = self.searchInput.text()
        if query:
            memos = [m for m in memos if m.matches(query)]

        tag = self.tagFilter.currentText()
        if tag and tag != i18n("All"):
            memos = [m for m in memos if tag in m.hashtags]

        for memo in reversed(memos):
            item = QListWidgetItem()
            item.setData(Qt.UserRole, memo.uid)
            self.memoList.addItem(item)

            widget = MemoListItem(memo)
            widget.deleteBtn.clicked.connect(lambda checked, m=memo: self.onDeleteMemo(m))
            widget.copyBtn.clicked.connect(lambda checked, m=memo: self.onCopyMemo(m))
            widget.editBtn.clicked.connect(lambda checked, m=memo: self.onEditMemo(m))
            item.setSizeHint(widget.sizeHint())
            self.memoList.setItemWidget(item, widget)

        totalCount = len(self.store.memos)
        self.setWindowTitle(f"{i18n('Memos')} ({totalCount})")

    def onSearchChanged(self):
        self.refreshList()

    def onFilterChanged(self):
        self.refreshList()

    def onMemoSelected(self, item):
        pass

    def onEditMemo(self, memo):
        self.autoSaveTimer.stop()
        self.currentMemo = memo
        self.contentEdit.setText(memo.content)
        self.tagsEdit.setTags(memo.hashtags)
        self.lastSavedContent = memo.content
        self.lastSavedTags = memo.hashtags[:]
        self.hasUnsavedChanges = False
        self.editorWidget.show()

    def onContentChanged(self):
        from .log import lg
        lg.log("onContentChanged called")
        self.hasUnsavedChanges = True
        self.autoSaveTimer.stop()

        if self.currentMemo is None:
            content = self.contentEdit.toPlainText().strip()
            if content:
                lg.log("New memo: creating immediately")
                self.createNewMemo()
            else:
                self.autoSaveTimer.start(300)
        else:
            self.autoSaveTimer.start(300)

    def createNewMemo(self):
        from .log import lg
        try:
            app = Krita.instance()
            doc = app.activeDocument()

            if not doc:
                lg.log("Create memo skipped: no document")
                return

            if doc != self.store.doc:
                self.store.set_document(doc)

            content = self.contentEdit.toPlainText().strip()
            hashtags = self.tagsEdit.getTags()

            if not content:
                return

            lg.log("Creating new memo")
            memo = Memo(content, hashtags)
            self.store.add(memo)
            self.currentMemo = memo

            self.lastSavedContent = content
            self.lastSavedTags = hashtags[:]
            self.hasUnsavedChanges = False

            self.refreshFilters()
            self.refreshList()
            lg.log("New memo created")
        except Exception as e:
            lg.error(f"Create memo failed: {e}")
            import traceback
            traceback.print_exc()

    def onAutoSave(self):
        from .log import lg
        try:
            if not self.hasUnsavedChanges:
                return

            if not self.currentMemo:
                return

            app = Krita.instance()
            doc = app.activeDocument()

            if not doc:
                lg.log("AutoSave skipped: no document")
                return

            if doc != self.store.doc:
                self.store.set_document(doc)

            content = self.contentEdit.toPlainText().strip()
            hashtags = self.tagsEdit.getTags()

            if content == self.lastSavedContent and hashtags == self.lastSavedTags:
                self.hasUnsavedChanges = False
                return

            if not content:
                self.hasUnsavedChanges = False
                return

            lg.log(f"AutoSave: Updating memo {self.currentMemo.uid}")
            self.store.update(self.currentMemo.uid, content, hashtags)

            self.lastSavedContent = content
            self.lastSavedTags = hashtags[:]
            self.hasUnsavedChanges = False

            self.refreshFilters()
            self.refreshList()
            lg.log("AutoSave completed")
        except Exception as e:
            lg.error(f"AutoSave failed: {e}")
            import traceback
            traceback.print_exc()

    def onNew(self):
        from .log import lg
        lg.log("onNew called")
        self.autoSaveTimer.stop()
        self.currentMemo = None
        self.hasUnsavedChanges = False
        self.lastSavedContent = ""
        self.lastSavedTags = []
        self.contentEdit.clear()
        self.tagsEdit.clear()
        self.editorWidget.show()
        self.contentEdit.setFocus()
        lg.log("onNew completed")

    def onCopy(self):
        from .log import lg
        try:
            content = self.contentEdit.toPlainText()
            if content:
                clipboard = QApplication.clipboard()
                clipboard.setText(content)
        except Exception as e:
            lg.error(f"Copy failed: {e}")

    def onCopyMemo(self, memo):
        from .log import lg
        try:
            if memo and memo.content:
                clipboard = QApplication.clipboard()
                clipboard.setText(memo.content)
        except Exception as e:
            lg.error(f"Copy memo failed: {e}")

    def onSave(self):
        from .log import lg
        lg.log("onSave called")
        self.autoSaveTimer.stop()
        if self.hasUnsavedChanges:
            self.saveMemo()
        self.editorWidget.hide()
        self.currentMemo = None
        self.memoList.clearSelection()

    def onDeleteMemo(self, memo):
        reply = QMessageBox.question(
            self,
            i18n("Confirm"),
            i18n("Delete this memo?"),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.deletedMemos.append(memo)
            self.store.delete(memo.uid)
            if self.currentMemo and self.currentMemo.uid == memo.uid:
                self.currentMemo = None
                self.editorWidget.hide()
            self.refreshFilters()
            self.refreshList()

    def showContextMenu(self, pos):
        from .log import lg
        try:
            menu = QMenu(self)

            undoAction = menu.addAction(Krita.instance().icon("edit-undo"), i18n("Undo Delete"))
            undoAction.setEnabled(len(self.deletedMemos) > 0)

            item = self.memoList.itemAt(pos)
            deleteAction = None
            if item:
                deleteAction = menu.addAction(Krita.instance().icon("edit-delete"), i18n("Delete"))

            action = menu.exec_(self.memoList.mapToGlobal(pos))

            if action == undoAction:
                self.onUndoDelete()
            elif action == deleteAction and item:
                uid = item.data(Qt.UserRole)
                memo = self.store.get(uid)
                if memo:
                    self.deletedMemos.append(memo)
                    self.store.delete(uid)
                    if self.currentMemo and self.currentMemo.uid == uid:
                        self.currentMemo = None
                        self.editorWidget.hide()
                    self.refreshFilters()
                    self.refreshList()

        except Exception as e:
            lg.error(f"Context menu error: {e}")
            import traceback
            traceback.print_exc()

    def onUndoDelete(self):
        if self.deletedMemos:
            memo = self.deletedMemos.pop()
            self.store.memos.append(memo)
            self.store.save()
            self.refreshFilters()
            self.refreshList()

    def canvasChanged(self, canvas):
        self.onDocumentChanged()

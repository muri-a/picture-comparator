from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QMainWindow

from picture_comparator.view.main_window_ui import Ui_MainWindow


class MainWindow(QMainWindow):
    DeleteModifierTriggered = Signal(bool)
    DeleteKeyPressed = Signal()

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.splitter.setStretchFactor(0, 1)
        self.ui.splitter.setStretchFactor(1, 4)
        self.ui.splitter_2.setStretchFactor(0, 4)
        self.ui.splitter_2.setStretchFactor(1, 1)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Control:
            self.DeleteModifierTriggered.emit(True)
        event.accept()

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Control:
            self.DeleteModifierTriggered.emit(False)
        elif event.key() == Qt.Key_Delete:
            self.DeleteKeyPressed.emit()
        event.accept()

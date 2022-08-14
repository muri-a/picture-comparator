from PySide6.QtWidgets import QDialog

from picture_comparator.view.renamer_ui import Ui_Renamer


class RenamerDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.ui = Ui_Renamer()
        self.ui.setupUi(self)

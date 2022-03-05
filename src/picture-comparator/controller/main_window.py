from PySide6.QtCore import Slot
from PySide6.QtWidgets import QApplication

from controller.action_buttons import ActionButtonsController
from controller.group_list import GroupList
from controller.matches import MatchesController
from controller.settings import Settings
from model.image_info import ImageInfo
from model.search_engine import SearchEngine
from view.main_window import MainWindow


class MainWindowController:
    def __init__(self, settings: Settings):
        self.settings: Settings = settings
        self.window = MainWindow()
        self.search_engine = SearchEngine(settings)
        self.action_buttons = ActionButtonsController(self)

        self.group_list = GroupList(self)
        self.matches = MatchesController(self)

        self.window.ui.action_quit.triggered.connect(self.exit_application)
        self.window.ui.list_thumbs_button.clicked.connect(self.set_list_thumbs)
        self.window.ui.stacked_thumbs_button.clicked.connect(self.set_stack_thumbs)
        self.search_engine.ImageFound.connect(self.image_found)

    def start(self):
        self.window.show()
        self.search_engine.start_comparison()

    def set_list_thumbs(self):
        self.window.ui.list_thumbs_button.setDown(True)
        self.window.ui.stacked_thumbs_button.setDown(False)
        self.window.ui.matches_stack.setCurrentIndex(0)

    def set_stack_thumbs(self):
        self.window.ui.list_thumbs_button.setDown(False)
        self.window.ui.stacked_thumbs_button.setDown(True)
        self.window.ui.matches_stack.setCurrentIndex(1)

    @Slot()
    def image_found(self, image: ImageInfo):
        self.window.ui.statusbar.showMessage(f"Image found: {image.path}")

    @Slot()
    def exit_application(self):
        QApplication.quit()

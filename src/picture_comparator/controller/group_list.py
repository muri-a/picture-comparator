from typing import Optional, List

from PySide6.QtCore import QItemSelection, QItemSelectionModel, Slot
from PySide6.QtWidgets import QPushButton, QMessageBox

from picture_comparator.controller.action_buttons import ActionButtonsController
from picture_comparator.controller.comparator import Comparator
from picture_comparator.model.display_settings import DisplayMode
from picture_comparator.model.group_selection_model import GroupSelectionModel
from picture_comparator.model.image_group import ImageGroup
from picture_comparator.model.image_info import ImageInfo
from picture_comparator.model.watched_list import WatchedList
from picture_comparator.view.group_list_view import GroupListView
from picture_comparator.view.main_window_ui import Ui_MainWindow


class GroupList:
    def __init__(self, main_window_controller):
        from picture_comparator.controller.main_window import MainWindowController
        self.main_window_controller: MainWindowController = main_window_controller
        self.comparator = Comparator(main_window_controller)
        self.action_buttons: ActionButtonsController = main_window_controller.action_buttons
        self.delete_button: QPushButton = self.ui.delete_button
        self.display_settings = self.action_buttons.display_settings

        self.list_view: GroupListView = self.ui.current_group_list_view
        self.image_group: Optional[ImageGroup] = None
        self.images = WatchedList([])
        self.list_view.model().set_list(self.images)
        self.list_view.set_display_settings(self.display_settings)

        self.selection: GroupSelectionModel = self.list_view.selectionModel()
        self.selection.selectionChanged.connect(self.selection_changed)
        self.selection.markingChanged.connect(self.markings_changed)

        self.action_buttons.DisplayModeChanged.connect(self.display_mode_changed)
        self.delete_button.clicked.connect(self.delete_marked)
        self.main_window_controller.window.DeleteKeyPressed.connect(self.delete_marked)

    @property
    def ui(self) -> Ui_MainWindow:
        return self.main_window_controller.window.ui

    def set_group(self, image_group: ImageGroup):
        with self.selection.select_manually:
            self.selection.clear()
        image_group.clear_markings()
        self.image_group = image_group
        self.images.replace(image_group)
        self.comparator.clear()
        self.update_selection()

    def update_selection(self):
        index = self.list_view.model().createIndex(0, 0)
        selection = QItemSelection(index, index)
        self.selection.select(selection, QItemSelectionModel.Select)

    def selection_changed(self, selected, deselected):
        # Workaround for marking images as selected
        if not self.image_group:
            return
        for image in self.image_group:
            image.selected = False
        for index in self.selection.selection().indexes():
            index.data().selected = True
        images = [index.data() for index in self.selection.selection().indexes()]
        images.sort(key=lambda i: i.path)
        self.comparator.set_images(images, False)

    def display_mode_changed(self, display_mode: DisplayMode):
        self.update_selection()

    def markings_changed(self, markings: List[ImageInfo]):
        self.delete_button.setEnabled(bool(markings))

    @Slot()
    def delete_marked(self, *args):
        if self.image_group and self.image_group.has_marked():
            to_remove = self.image_group.marked_for_deletion()
            files_list = ''
            for file in to_remove:
                files_list += file.path + "\n"
            reply = QMessageBox.warning(self.main_window_controller.window, "Move to the trash?",
                                        f"Do you want to remove marked files?\n{files_list}",
                                        QMessageBox.Apply | QMessageBox.Cancel)
            if reply == QMessageBox.Apply:
                self.image_group.delete_marked()
                if len(self.image_group):
                    self.images.remove_multiple(to_remove)
                    self.update_selection()
                else:
                    # No images to compare. Drop current match group.
                    self.main_window_controller.matches.remove_current_match()

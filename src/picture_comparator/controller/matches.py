from typing import List, Optional

from PySide6.QtCore import Slot, Qt, QItemSelection, QItemSelectionModel

from picture_comparator.controller.group_list import GroupList
from picture_comparator.model.image_group import ImageGroup
from picture_comparator.model.search_engine import SearchEngine
from picture_comparator.model.utils import first
from picture_comparator.model.watched_list import WatchedList, WatchedListModel
from picture_comparator.view.main_window_ui import Ui_MainWindow
from picture_comparator.view.matches_view import MatchesListView


class MatchesController:
    def __init__(self, main_window_controller):
        self.main_window_controller = main_window_controller
        self.current_matches_view = self.ui.full_view_page
        self.list_view: MatchesListView = self.main_window_controller.window.ui.full_view_page
        self.list_view_model = WatchedListModel()
        self.image_groups: Optional[WatchedList] = None

        self.search_engine.ResultsReady.connect(self.results_ready)
        self.list_view.setModel(self.list_view_model)
        self.list_view.selectionModel().selectionChanged.connect(self.result_changed)

    @property
    def ui(self) -> Ui_MainWindow:
        return self.main_window_controller.window.ui

    @property
    def search_engine(self) -> SearchEngine:
        return self.main_window_controller.search_engine

    @property
    def group_list(self) -> GroupList:
        return self.main_window_controller.group_list

    @Slot()
    def results_ready(self, groups: List[ImageGroup]):
        self.image_groups = WatchedList(groups)
        self.main_window_controller.window.ui.statusbar.showMessage(f"Search finished.")
        self.list_view_model.set_list(self.image_groups)

    @Slot()
    def result_changed(self, current: QItemSelection, _: QItemSelection):
        if current.count():
            image_group: ImageGroup = current.indexes()[0].data(Qt.DisplayRole)
            self.group_list.set_group(image_group)

    def remove_current_match(self):
        selected = first(self.list_view.selectionModel().selection().indexes())
        index = selected.row()
        if index + 1 == self.list_view_model.rowCount():
            index -= 1
        self.image_groups.remove(selected.data())
        i = self.list_view_model.createIndex(index, 0)
        new_selection = QItemSelection(i, i)
        self.list_view.selectionModel().select(new_selection, QItemSelectionModel.ClearAndSelect)

import math
from typing import List, Optional

from PySide6.QtCore import Slot, Qt, QItemSelection, QItemSelectionModel
from PySide6.QtWidgets import QHBoxLayout, QLabel

from picture_comparator.controller.group_list import GroupList
from picture_comparator.controller.log import LogController
from picture_comparator.model.image_group import ImageGroup
from picture_comparator.model.log_engine import LogMessage, LogType
from picture_comparator.model.search_engine import SearchEngine
from picture_comparator.model.utils import first
from picture_comparator.model.watched_list import WatchedList, WatchedListModel
from picture_comparator.view.main_window_ui import Ui_MainWindow
from picture_comparator.view.matches_view import MatchesListView


class MatchesController:
    GROUPS_PER_PAGE = 20

    def __init__(self, main_window_controller):
        self.main_window_controller = main_window_controller
        self.current_matches_view = self.ui.full_view_page
        self.pager: QHBoxLayout = self.ui.pager_layout
        self.pager_labels: List[QLabel] = []
        self.list_view: MatchesListView = self.main_window_controller.window.ui.full_view_page
        self.list_view_model = WatchedListModel()
        self.log: LogController = self.main_window_controller.log

        self.all_groups: List[ImageGroup] = []
        self.current_page: int = 0
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

    @property
    def pages_count(self) -> int:
        return math.ceil(len(self.all_groups) / self.GROUPS_PER_PAGE)

    @Slot()
    def results_ready(self, groups: List[ImageGroup]):
        self.all_groups = groups
        self.image_groups = WatchedList(groups[:self.GROUPS_PER_PAGE])
        self.log.log_message(LogMessage(LogType.INFO, "Search finished.", True))
        self.list_view_model.set_list(self.image_groups)
        # Prepare pager
        pages = self.pages_count
        if pages > 1 or True:
            for i in range(pages):
                label = QLabel(f'<a href="{i}">{i + 1}</a>')
                if i == 0:
                    label.setEnabled(False)
                self.pager.addWidget(label)
                self.pager_labels.append(label)
                label.linkActivated.connect(self.page_changed)

    @Slot()
    def page_changed(self, page: str):
        new_page = int(page)
        for i, page in enumerate(self.pager_labels):
            page.setEnabled(i != new_page)
        page_start = new_page * self.GROUPS_PER_PAGE
        self.image_groups.replace(self.all_groups[page_start: page_start + self.GROUPS_PER_PAGE])
        self.current_page = new_page

    @Slot()
    def result_changed(self, current: QItemSelection, _: QItemSelection):
        if current.count():
            image_group: ImageGroup = current.indexes()[0].data(Qt.DisplayRole)
            self.group_list.set_group(image_group)

    def remove_current_match(self):
        selected = first(self.list_view.selectionModel().selection().indexes())
        index = selected.row()
        # remove the same match group from "all"
        page_start = self.current_page * self.GROUPS_PER_PAGE
        global_index = self.current_page * self.GROUPS_PER_PAGE + index
        del self.all_groups[global_index]

        if self.pages_count < len(self.pager_labels):
            # Remove last page
            self.pager.removeWidget(self.pager_labels[-1])
            del self.pager_labels[-1]
            if self.current_page == self.pages_count:
                self.page_changed(str(self.current_page - 1))
                return

        if index == len(self.all_groups):
            index -= 1
        self.image_groups.remove(selected.data())

        self.image_groups.replace(self.all_groups[page_start: page_start + self.GROUPS_PER_PAGE])

        i = self.list_view_model.createIndex(index, 0)
        new_selection = QItemSelection(i, i)
        self.list_view.selectionModel().select(new_selection, QItemSelectionModel.ClearAndSelect)

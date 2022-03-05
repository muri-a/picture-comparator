from typing import List

from controller.action_buttons import ActionButtonsController
from model.image_info import ImageInfo


class Comparator:
    def __init__(self, main_window_controller):
        self.main_window_controller = main_window_controller
        self.action_buttons: ActionButtonsController = main_window_controller.action_buttons
        self.compare_widget = main_window_controller.window.ui.compare_widget
        self.images = []
        self.action_buttons.ShowInfoChanged.connect(self.update_view)
        self.action_buttons.ShowZoomChanged.connect(self.update_view)

    def set_images(self, images: List[ImageInfo], group_changed: bool):
        self.images = images
        self.compare_widget.set_display_settings(self.action_buttons.display_settings)
        self.compare_widget.set_images(images, group_changed)

    def update_view(self):
        self.compare_widget.update()

from typing import List

from PySide6.QtCore import QSettings


class Settings:
    """Helps to interact with settings."""
    def __init__(self, args):
        self.qt_settings = QSettings('armas', 'picture_comparator')
        self.directories: List[str] = args.directories
        self.scan_subdirectories: bool = not args.no_subdirs
        # self.join_similar_groups: bool = True

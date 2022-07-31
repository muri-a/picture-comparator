#!/bin/sh

pyside6-uic src/picture_comparator/design/directory_picker.ui > src/picture_comparator/view/directory_picker_ui.py
pyside6-uic src/picture_comparator/design/main_window.ui > src/picture_comparator/view/main_window_ui.py
pyside6-uic src/picture_comparator/design/log.ui > src/picture_comparator/view/log_ui.py
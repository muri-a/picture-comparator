#!/bin/sh

pyside6-uic src/picture_comparator_muri/design/directory_picker.ui > src/picture_comparator_muri/view/directory_picker_ui.py
pyside6-uic src/picture_comparator_muri/design/log.ui > src/picture_comparator_muri/view/log_ui.py
pyside6-uic src/picture_comparator_muri/design/main_window.ui > src/picture_comparator_muri/view/main_window_ui.py
pyside6-uic src/picture_comparator_muri/design/renamer.ui > src/picture_comparator_muri/view/renamer_ui.py
pyside6-uic src/picture_comparator_muri/design/manual_rename.ui > src/picture_comparator_muri/view/manual_rename_ui.py

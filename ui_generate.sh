#!/bin/sh

pyside6-uic src/picture-comparator/design/directory_picker.ui > src/picture-comparator/view/directory_picker_ui.py
pyside6-uic src/picture-comparator/design/main_window.ui > src/picture-comparator/view/main_window_ui.py
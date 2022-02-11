from PyQt5.Qt import QMainWindow

from .ui import Ui_main_window


def _update_window(win: QMainWindow) -> QMainWindow:
    win.setFixedSize(win.width(), win.height())  # set the fixed size of window
    return win


def update_main_window(win: QMainWindow) -> QMainWindow:
    ui: Ui_main_window = Ui_main_window()
    ui.setupUi(win)
    win.ui = ui

    win = _update_window(win)
    return win

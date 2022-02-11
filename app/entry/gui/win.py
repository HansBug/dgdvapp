import sys

from PyQt5.QtWidgets import QApplication, QMainWindow

from ...gui import update_main_window


def run_gui():
    app = QApplication([])

    main_window = QMainWindow()
    update_main_window(main_window)
    main_window.show()

    sys.exit(app.exec_())

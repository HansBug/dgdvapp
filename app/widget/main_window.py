import sys

from PyQt5 import QtGui
from PyQt5.Qt import QMainWindow, Qt

from .dialog_config import DialogConfig
from .form_generate import FormGenerate
from .form_log_process import FormLogProcess
from ..ui import UIMainWindow


class AppMainWindow(QMainWindow, UIMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)
        self._init()

    def _init(self):
        self._init_this_application()
        self._init_mdi_area()
        self._init_open_generate()
        self._init_open_log_process()

    def _init_open_generate(self):
        def _show_form():
            form = FormGenerate()
            sub_window = self.mdi_area.addSubWindow(form)
            sub_window.setFixedSize(sub_window.width(), sub_window.height())
            sub_window.setMaximumSize(sub_window.width(), sub_window.height())
            sub_window.setWindowFlags(sub_window.windowFlags() & ~Qt.WindowMaximizeButtonHint)
            sub_window.show()

        self.action_data_generation.triggered.connect(_show_form)

    def _init_open_log_process(self):
        def _show_form():
            form = FormLogProcess()
            sub_window = self.mdi_area.addSubWindow(form)
            sub_window.setFixedSize(sub_window.width(), sub_window.height())
            sub_window.setMaximumSize(sub_window.width(), sub_window.height())
            sub_window.setWindowFlags(sub_window.windowFlags() & ~Qt.WindowMaximizeButtonHint)
            sub_window.show()

        self.action_log_processing.triggered.connect(_show_form)

    def _init_this_application(self):
        self.action_application.triggered.connect(self._event_open_dialog_config)

    def _init_mdi_area(self):
        self.setCentralWidget(self.mdi_area)

    def _event_open_dialog_config(self):
        dialog = DialogConfig(self)
        dialog.exec_()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        sys.exit(0)

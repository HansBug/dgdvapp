import sys

from PyQt5 import QtGui
from PyQt5.Qt import QMainWindow

from .dialog_config import DialogConfig
from .form_generate import FormGenerate
from ..ui import UIMainWindow


class AppMainWindow(QMainWindow, UIMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)
        self.setFixedSize(self.width(), self.height())
        self._init()

    def _init(self):
        self._init_this_application()
        self._init_open_generate()

    def _init_open_generate(self):
        form = FormGenerate()

        def _show_form():
            form.show()

        self.button_datagene.clicked.connect(_show_form)
        self.action_data_generation.triggered.connect(_show_form)

    def _init_this_application(self):
        self.action_application.triggered.connect(self._event_open_dialog_config)

    def _event_open_dialog_config(self):
        dialog = DialogConfig(self)
        dialog.exec_()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        sys.exit(0)

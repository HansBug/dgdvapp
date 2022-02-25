import sys

from PyQt5 import QtGui
from PyQt5.Qt import QMainWindow, Qt

from .dialog_config import DialogConfig
from .form_anova import FormANOVA
from .form_boxplot import FormBoxplot
from .form_generate import FormGenerate
from .form_log_process import FormLogProcess
from .form_message_logging import FormMessageLogging
from .form_metrics import FormMetrics
from .form_scatter import FormScatter
from .form_spearmanr import FormSpearmanr
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
        self._init_open_metrics()
        self._init_open_message_logging()
        self._init_open_spearman()
        self._init_open_anova()
        self._init_open_scatter()
        self._init_open_boxplot()

    def _init_open_generate(self):
        # noinspection DuplicatedCode
        def _show_form():
            form = FormGenerate()
            sub_window = self.mdi_area.addSubWindow(form)
            sub_window.setFixedSize(sub_window.width(), sub_window.height())
            sub_window.setMaximumSize(sub_window.width(), sub_window.height())
            sub_window.setWindowFlags(sub_window.windowFlags() & ~Qt.WindowMaximizeButtonHint)
            sub_window.show()

        self.action_data_generation.triggered.connect(_show_form)

    def _init_open_log_process(self):
        # noinspection DuplicatedCode
        def _show_form():
            form = FormLogProcess()
            sub_window = self.mdi_area.addSubWindow(form)
            sub_window.setFixedSize(sub_window.width(), sub_window.height())
            sub_window.setMaximumSize(sub_window.width(), sub_window.height())
            sub_window.setWindowFlags(sub_window.windowFlags() & ~Qt.WindowMaximizeButtonHint)
            sub_window.show()

        self.action_log_processing.triggered.connect(_show_form)

    def _init_open_metrics(self):
        # noinspection DuplicatedCode
        def _show_form():
            form = FormMetrics()
            sub_window = self.mdi_area.addSubWindow(form)
            sub_window.setFixedSize(sub_window.width(), sub_window.height())
            sub_window.setMaximumSize(sub_window.width(), sub_window.height())
            sub_window.setWindowFlags(sub_window.windowFlags() & ~Qt.WindowMaximizeButtonHint)
            sub_window.show()

        self.action_result_metrics.triggered.connect(_show_form)

    def _init_open_message_logging(self):
        # noinspection DuplicatedCode
        def _show_form():
            form = FormMessageLogging()
            sub_window = self.mdi_area.addSubWindow(form)
            sub_window.setFixedSize(sub_window.width(), sub_window.height())
            sub_window.setMaximumSize(sub_window.width(), sub_window.height())
            sub_window.setWindowFlags(sub_window.windowFlags() & ~Qt.WindowMaximizeButtonHint)
            sub_window.show()

        self.action_message_logging.triggered.connect(_show_form)

    def _init_open_spearman(self):
        # noinspection DuplicatedCode
        def _show_form():
            form = FormSpearmanr()
            sub_window = self.mdi_area.addSubWindow(form)
            sub_window.setFixedSize(sub_window.width(), sub_window.height())
            sub_window.setMaximumSize(sub_window.width(), sub_window.height())
            sub_window.setWindowFlags(sub_window.windowFlags() & ~Qt.WindowMaximizeButtonHint)
            sub_window.show()

        self.action_spearman.triggered.connect(_show_form)

    def _init_open_anova(self):
        # noinspection DuplicatedCode
        def _show_form():
            form = FormANOVA()
            sub_window = self.mdi_area.addSubWindow(form)
            sub_window.setFixedSize(sub_window.width(), sub_window.height())
            sub_window.setMaximumSize(sub_window.width(), sub_window.height())
            sub_window.setWindowFlags(sub_window.windowFlags() & ~Qt.WindowMaximizeButtonHint)
            sub_window.show()

        self.action_anova.triggered.connect(_show_form)

    def _init_open_scatter(self):
        # noinspection DuplicatedCode
        def _show_form():
            form = FormScatter()
            sub_window = self.mdi_area.addSubWindow(form)
            sub_window.setFixedSize(sub_window.width(), sub_window.height())
            sub_window.setMaximumSize(sub_window.width(), sub_window.height())
            sub_window.setWindowFlags(sub_window.windowFlags() & ~Qt.WindowMaximizeButtonHint)
            sub_window.show()

        self.action_scatter.triggered.connect(_show_form)

    def _init_open_boxplot(self):
        # noinspection DuplicatedCode
        def _show_form():
            form = FormBoxplot()
            sub_window = self.mdi_area.addSubWindow(form)
            sub_window.setFixedSize(sub_window.width(), sub_window.height())
            sub_window.setMaximumSize(sub_window.width(), sub_window.height())
            sub_window.setWindowFlags(sub_window.windowFlags() & ~Qt.WindowMaximizeButtonHint)
            sub_window.show()

        self.action_boxplot.triggered.connect(_show_form)

    def _init_this_application(self):
        self.action_application.triggered.connect(self._event_open_dialog_config)

    def _init_mdi_area(self):
        self.setCentralWidget(self.mdi_area)

    def _event_open_dialog_config(self):
        dialog = DialogConfig(self)
        dialog.exec_()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        sys.exit(0)

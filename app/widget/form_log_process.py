import os
from enum import IntEnum, unique

import qtawesome as qta
from PyQt5.Qt import QWidget, Qt, QFileDialog, QStandardItemModel, QStandardItem, QIcon, QHeaderView, QMessageBox, \
    QThread, pyqtSignal
from hbutils.model import int_enum_loads

from ..process import walk_log_directories, log_process
from ..ui import UIFormLogProcess


@int_enum_loads(enable_int=False, name_preprocess=str.upper, )
@unique
class ProcessingStatus(IntEnum):
    PENDING = 0
    WAITING = 1
    PROCESSING = 2
    COMPLETED = 3
    ERROR = 4

    @property
    def text(self):
        return self.name.lower().capitalize()

    @property
    def icon(self) -> QIcon:
        if self == self.PENDING:
            return qta.icon('fa5.sticky-note')
        elif self == self.WAITING:
            return qta.icon('fa.clock-o', color='yellow')
        elif self == self.PROCESSING:
            return qta.icon('fa.hourglass-1', color='blue')
        elif self == self.COMPLETED:
            return qta.icon('fa.check', color='green')
        elif self == self.ERROR:
            return qta.icon('fa.remove', color='red')
        else:
            raise ValueError(f'Unknown status - {repr(self)}.')


class FormLogProcess(QWidget, UIFormLogProcess):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)
        self._init()

    def _init(self):
        self._init_window_size()
        self._init_table()
        self._init_open_dialog()
        self._init_start()

    def _init_window_size(self):
        self.setFixedSize(self.width(), self.height())
        self.setMaximumSize(self.width(), self.height())
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)

    def _init_table(self):
        self.table_processing.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def _init_open_dialog(self):
        def _open_directory():
            directory = QFileDialog.getExistingDirectory(self)
            if directory:
                self.button_open.setEnabled(False)
                self.button_start.setEnabled(False)

                try:
                    self.label_path.setText(directory)
                    model = QStandardItemModel(0, 2)
                    model.setHorizontalHeaderLabels(['Path', 'Status'])

                    cnt = 0
                    for p in walk_log_directories(directory):
                        relpath = os.path.relpath(p, start=directory)
                        path = QStandardItem(relpath)
                        path.setFlags(Qt.ItemIsEnabled)
                        status = QStandardItem(ProcessingStatus.PENDING.text)
                        status.setFlags(Qt.ItemIsEnabled)
                        status.setIcon(ProcessingStatus.PENDING.icon)
                        model.appendRow([path, status])
                        cnt += 1

                    self.table_processing.setModel(model)
                    self.table_processing.setProperty('directory', directory)
                    self.table_processing.setProperty('total_count', cnt)
                    self.progress_status.setMaximum(cnt if cnt > 0 else 1)
                    self.progress_status.setValue(0)
                    self.button_start.setEnabled(cnt > 0)

                finally:
                    self.button_open.setEnabled(True)

        self.button_open.clicked.connect(_open_directory)

    def _init_start(self):
        class _ProcessThread(QThread):
            init = pyqtSignal(int, QStandardItemModel)
            before_loop = pyqtSignal(int, int, QStandardItemModel)
            after_loop = pyqtSignal(int, int, QStandardItemModel)
            deinit = pyqtSignal(int)

            def __init__(self, parent, directory: str, total_count: int, model: QStandardItemModel):
                QThread.__init__(self, parent)
                self.directory = directory
                self.total_count = total_count
                self.model = model

            def run(self) -> None:
                self.init.emit(self.total_count, self.model)
                for i in range(self.total_count):
                    self.before_loop.emit(i, self.total_count, self.model)

                    relpath = self.model.item(i, 0).text()
                    path = os.path.join(self.directory, relpath)
                    log_process(path, force=True)

                    self.after_loop.emit(i, self.total_count, self.model)

                self.deinit.emit(self.total_count)

        def _init(total_count, model):
            self.button_open.setEnabled(False)
            self.button_start.setEnabled(False)

            for i in range(total_count):
                status = model.item(i, 1)
                waiting = ProcessingStatus.WAITING
                status.setText(waiting.text)
                status.setIcon(waiting.icon)
                model.setItem(i, 1, status)

        def _before_loop(i, total_count, model):
            status = model.item(i, 1)
            processing = ProcessingStatus.PROCESSING
            status.setText(processing.text)
            status.setIcon(processing.icon)
            model.setItem(i, 1, status)
            self.label_status.setText(f'Running - {repr(i + 1)} / {repr(total_count)} ...')

        def _after_loop(i, total_count, model):
            status = model.item(i, 1)
            completed = ProcessingStatus.COMPLETED
            status.setText(completed.text)
            status.setIcon(completed.icon)
            model.setItem(i, 1, status)
            self.progress_status.setValue(i + 1)

        def _deinit(total_count):
            self.label_status.setText('Completed.')
            self.button_open.setEnabled(True)
            self.button_start.setEnabled(True)
            QMessageBox.information(self, 'Log Processing', 'Completed!')

        def _process():
            directory = self.table_processing.property('directory')
            total_count = self.table_processing.property('total_count')
            model = self.table_processing.model()

            thread = _ProcessThread(self, directory, total_count, model)
            thread.init.connect(_init)
            thread.before_loop.connect(_before_loop)
            thread.after_loop.connect(_after_loop)
            thread.deinit.connect(_deinit)
            thread.start()

        self.button_start.clicked.connect(_process)

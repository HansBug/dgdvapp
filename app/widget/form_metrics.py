import csv
import os
from types import MethodType
from typing import List

from PyQt5.Qt import QWidget, Qt, QStandardItemModel, QFileDialog, QStandardItem, QMessageBox, QThread, pyqtSignal, \
    QListWidgetItem, QListWidget

from .models import ProcessingStatus
from ..process import METRICS_LIST, walk_log_directories, get_all_metrics
from ..ui import UIFormMetrics


class FormMetrics(QWidget, UIFormMetrics):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)
        self._init()

    def _init(self):
        self._init_window_size()
        self._init_list_metrics()
        self._init_table()
        self._init_open_dialog()
        self._init_start()
        self._init_export()

    def _init_window_size(self):
        self.setFixedSize(self.width(), self.height())
        self.setMaximumSize(self.width(), self.height())
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)

    def _init_list_metrics(self):
        for name in METRICS_LIST:
            item = QListWidgetItem(self.list_metrics)
            item.setText(name)
            item.setCheckState(Qt.Checked)

        def _get_enabled_metrics(self_: QListWidget) -> List[str]:
            metrics = []
            for i in range(self_.count()):
                item_ = self_.item(i)
                if item_.checkState() == Qt.Checked:
                    metrics.append(item_.text())

            return metrics

        self.list_metrics.get_enabled_metrics = MethodType(_get_enabled_metrics, self.list_metrics)

    def _init_table(self):
        self.table_result.setSortingEnabled(True)

        metrics = self.list_metrics.get_enabled_metrics()
        model = QStandardItemModel(0, len(metrics) + 2)
        model.setHorizontalHeaderLabels(['Path', 'Status', *metrics])
        self.table_result.setModel(model)

    def _init_open_dialog(self):
        def _open_directory():
            directory = QFileDialog.getExistingDirectory(self)
            if directory:
                self.button_open.setEnabled(False)
                self.button_start.setEnabled(False)
                self.button_export.setEnabled(False)

                try:
                    self.label_path.setText(directory)
                    metrics = self.list_metrics.get_enabled_metrics()
                    model = QStandardItemModel(0, len(metrics) + 2)
                    model.setHorizontalHeaderLabels(['Path', 'Status', *metrics])

                    cnt = 0
                    for p in walk_log_directories(directory):
                        relpath = os.path.relpath(p, start=directory)
                        path = QStandardItem(relpath)
                        path.setFlags(Qt.ItemIsEnabled)
                        status = QStandardItem(ProcessingStatus.PENDING.text)
                        status.setFlags(Qt.ItemIsEnabled)
                        status.setIcon(ProcessingStatus.PENDING.icon)
                        model.appendRow([
                            path, status
                        ])
                        cnt += 1

                    self.table_result.setModel(model)
                    self.table_result.setProperty('directory', directory)
                    self.table_result.setProperty('total_count', cnt)
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
            after_loop = pyqtSignal(int, int, QStandardItemModel, dict)
            deinit = pyqtSignal(int)

            def __init__(self, parent, directory: str, total_count: int,
                         model: QStandardItemModel, metrics: List[str]):
                QThread.__init__(self, parent)
                self.directory = directory
                self.total_count = total_count
                self.model = model
                self.metrics = metrics

            def run(self) -> None:
                self.init.emit(self.total_count, self.model)
                for i in range(self.total_count):
                    self.before_loop.emit(i, self.total_count, self.model)

                    relpath = self.model.item(i, 0).text()
                    result = get_all_metrics(os.path.join(self.directory, relpath), metrics=self.metrics)

                    self.after_loop.emit(i, self.total_count, self.model, result)

                self.deinit.emit(self.total_count)

        def _init(total_count, model):
            self.button_open.setEnabled(False)
            self.button_start.setEnabled(False)
            self.button_export.setEnabled(False)
            self.table_result.setSortingEnabled(False)

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

        def _after_loop(i, total_count, model, result: dict):
            status = model.item(i, 1)
            completed = ProcessingStatus.COMPLETED
            status.setText(completed.text)
            status.setIcon(completed.icon)
            model.setItem(i, 1, status)
            self.progress_status.setValue(i + 1)

            metrics = self.list_metrics.get_enabled_metrics()
            for index, name in enumerate(metrics):
                model.setItem(i, index + 2, QStandardItem(str(result[name])))

        def _deinit(total_count):
            self.label_status.setText('Completed.')
            self.button_open.setEnabled(True)
            self.button_start.setEnabled(True)
            self.button_export.setEnabled(True)
            self.table_result.setSortingEnabled(True)
            QMessageBox.information(self, 'Log Processing', 'Completed!')

        def _process():
            directory = self.table_result.property('directory')
            total_count = self.table_result.property('total_count')
            model = self.table_result.model()

            metrics = self.list_metrics.get_enabled_metrics()
            thread = _ProcessThread(self, directory, total_count, model, metrics)
            thread.init.connect(_init)
            thread.before_loop.connect(_before_loop)
            thread.after_loop.connect(_after_loop)
            thread.deinit.connect(_deinit)
            thread.start()

        self.button_start.clicked.connect(_process)

    def _init_export(self):
        def _export():
            filename_str, filename_ok = QFileDialog.getSaveFileName(
                self, 'Result Export',
                filter='*.csv', initialFilter='*.csv'
            )
            if filename_ok:
                metrics = self.list_metrics.get_enabled_metrics()
                with open(filename_str, 'w', newline='') as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(['Path', *metrics])

                    m = len(metrics)
                    model = self.table_result.model()
                    total_count = self.table_result.property('total_count')
                    for i in range(total_count):
                        writer.writerow([
                            model.item(i, 0).text(),
                            *[model.item(i, j + 2).text() for j in range(m)]
                        ])

                QMessageBox.information(self, 'Result Export', 'Completed!')

        self.button_export.clicked.connect(_export)

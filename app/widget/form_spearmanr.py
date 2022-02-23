import csv
import math
from threading import Lock
from types import MethodType

import pandas
import pandas as pd
import scipy.stats
from PyQt5.Qt import QWidget, Qt, QFileDialog, QStandardItemModel, QStandardItem, QMessageBox, QHeaderView, \
    QModelIndex, QTableView, QThread, pyqtSignal, QBrush, QColor
from hbutils.color import Color
from hbutils.reflection import nested_for

from .models import NameStatus
from ..ui import UIFormSpearmanr


class FormSpearmanr(QWidget, UIFormSpearmanr):
    def __init__(self):
        QWidget.__init__(self)
        self.__lock = Lock()
        self.setupUi(self)
        self._init()

    def _init(self):
        self._init_window_size()
        self._init_tabs()
        self._init_open_csv()
        self._init_table_items()
        self._init_analysis()
        self._init_export()

    def _init_window_size(self):
        self.setFixedSize(self.width(), self.height())
        self.setMaximumSize(self.width(), self.height())
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)

    def _init_tabs(self):
        self.tabs_pages.setCurrentIndex(0)

    def _init_open_csv(self):
        def _open():
            filename, _ = QFileDialog.getOpenFileName(
                self, 'Load Data', filter='*.csv', initialFilter='*.csv')
            if filename:
                df = pd.read_csv(filename)

                n = len(df)
                names = [name for name in df.columns]
                m = len(names)
                model = QStandardItemModel(n, m)
                model.setHorizontalHeaderLabels(names)

                for i in range(n):
                    for j, name in enumerate(names):
                        item = QStandardItem(str(df[name][i]))
                        item.setFlags(Qt.ItemIsEnabled)
                        model.setItem(i, j, item)

                self.table_data.setProperty('data', df)
                self.table_data.setModel(model)
                self.table_data.setSortingEnabled(True)

                names_model = QStandardItemModel(m, 2)
                names_model.setHorizontalHeaderLabels(['Name', 'Status'])
                for i in range(m):
                    item_name = QStandardItem(str(names[i]))
                    item_name.setEditable(False)
                    names_model.setItem(i, 0, item_name)

                    nothing = NameStatus.NOTHING
                    item_status = QStandardItem(nothing.icon, nothing.text)
                    item_status.setEditable(False)
                    item_status.setData(nothing)
                    names_model.setItem(i, 1, item_status)

                self.table_items.setModel(names_model)
                self.button_analysis.setEnabled(True)

                QMessageBox.information(self, 'Load Data', 'Completed!')

        self.button_open.clicked.connect(_open)

    def _init_table_items(self):
        names_model = QStandardItemModel(0, 2)
        names_model.setHorizontalHeaderLabels(['Name', 'Status'])
        self.table_items.setModel(names_model)

        def _dbl_click(index: QModelIndex):
            model = self.table_items.model()
            if index.column() == 1:
                item: QStandardItem = model.item(index.row(), index.column())
                next_status = item.data().next
                item.setText(next_status.text)
                item.setIcon(next_status.icon)
                item.setData(next_status)
                item.setFlags(Qt.ItemIsEnabled)
                model.setItem(index.row(), index.column(), item)

        self.table_items.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_items.setSortingEnabled(True)
        self.table_items.doubleClicked.connect(_dbl_click)

        def _get_names(self_: QTableView):
            model = self_.model()
            x, y = [], []
            for i in range(model.rowCount()):
                item_name = model.item(i, 0)
                name = item_name.text()

                item_status = model.item(i, 1)
                if item_status.data() == NameStatus.INDEPENDENT:
                    x.append(name)
                elif item_status.data() == NameStatus.DEPENDENT:
                    y.append(name)

            return x, y

        self.table_items.get_names = MethodType(_get_names, self.table_items)

    def _init_analysis(self):
        class _AnalysisThread(QThread):
            init = pyqtSignal(int, list, list)
            before_loop = pyqtSignal(str, str, int, int, int, int)
            after_loop = pyqtSignal(str, str, int, int, int, int, float, float)
            deinit = pyqtSignal(int)

            def __init__(self, parent, df: pandas.DataFrame,
                         x_names, y_names):
                QThread.__init__(self, parent)
                self.df = df
                self.x_names = x_names
                self.y_names = y_names
                self.xi_names = {name: i for i, name in enumerate(x_names)}
                self.yi_names = {name: i for i, name in enumerate(y_names)}

            # noinspection PyUnresolvedReferences
            def run(self) -> None:
                total = len(self.x_names) * len(self.y_names)
                self.init.emit(total, self.x_names, self.y_names)

                for i, (xname, yname) in enumerate(nested_for(self.x_names, self.y_names)):
                    xi, yi = self.xi_names[xname], self.yi_names[yname]
                    self.before_loop.emit(xname, yname, i, total, xi, yi)
                    rho, pval = scipy.stats.spearmanr(self.df[xname], self.df[yname])
                    self.after_loop.emit(xname, yname, i, total, xi, yi, rho, pval)

                self.deinit.emit(total)

        # noinspection PyUnusedLocal
        def _init(total, x_names, y_names):
            self.__lock.acquire()
            result = QStandardItemModel(len(x_names), len(y_names))
            result.setVerticalHeaderLabels(x_names)
            result.setHorizontalHeaderLabels(y_names)
            self.table_analysis.setModel(result)
            self.table_analysis.setProperty('x_names', x_names)
            self.table_analysis.setProperty('y_names', y_names)
            self.button_analysis.setEnabled(False)
            self.button_export.setEnabled(False)

        # noinspection PyUnusedLocal
        def _before_loop(xname, yname, i, total, xi, yi):
            pass

        def _color_choose(rho):
            if math.isnan(rho):
                return str(Color.from_hls(2 / 3, 0.985, 1.0))
            else:
                return str(Color.from_hls(
                    (1 - rho) / 6,
                    (3 * (abs(rho) - 1) ** 2 + 5) / 8,
                    1.0
                ))

        # noinspection PyUnusedLocal
        def _after_loop(xname, yname, i, total, xi, yi, rho, pval):
            model: QStandardItemModel = self.table_analysis.model()
            item = QStandardItem('nan' if math.isnan(rho) else '%.4f' % (rho,))
            item.setData(rho)
            item.setFlags(Qt.ItemIsEnabled)
            item.setBackground(QBrush(QColor(_color_choose(rho))))
            model.setItem(xi, yi, item)

        # noinspection PyUnusedLocal
        def _deinit(total):
            self.tabs_pages.setCurrentIndex(1)
            self.button_analysis.setEnabled(True)
            self.button_export.setEnabled(True)
            self.__lock.release()
            QMessageBox.information(self, 'Analysis', 'Completed!')

        # noinspection PyUnresolvedReferences
        def _analysis():
            x_names, y_names = self.table_items.get_names()
            df = self.table_data.property('data')

            thread = _AnalysisThread(self, df, x_names, y_names)
            thread.init.connect(_init)
            thread.deinit.connect(_deinit)
            thread.before_loop.connect(_before_loop)
            thread.after_loop.connect(_after_loop)
            thread.start()

        self.button_analysis.clicked.connect(_analysis)

    def _init_export(self):
        def _export():
            with self.__lock:
                filename_str, filename_ok = QFileDialog.getSaveFileName(
                    self, 'Export Analysis', filter='*.csv', initialFilter='*.csv')
                if filename_ok:
                    self.button_analysis.setEnabled(False)
                    self.button_export.setEnabled(False)
                    with open(filename_str, 'w', newline='') as csv_file:
                        x_names = self.table_analysis.property('x_names')
                        y_names = self.table_analysis.property('y_names')
                        writer = csv.writer(csv_file)
                        writer.writerow(['', *y_names])

                        model = self.table_analysis.model()
                        for xi, xname in enumerate(x_names):
                            writer.writerow([xname, *(model.item(xi, j).data() for j in range(len(y_names)))])

                    self.button_analysis.setEnabled(True)
                    self.button_export.setEnabled(True)
                    QMessageBox.information(self, 'Export Analysis', 'Completed!')

        self.button_export.clicked.connect(_export)

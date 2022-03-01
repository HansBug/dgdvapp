import csv
import math
from threading import Lock
from types import MethodType

import pandas as pd
import qtawesome as qta
from PyQt5.Qt import QWidget, Qt, QFileDialog, QStandardItemModel, QStandardItem, QMessageBox, QHeaderView, \
    QTableView, QModelIndex, QColor, QBrush
from hbutils.color import Color
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm

from .dialog_multiple_choice import DialogMultipleChoice
from .models import DependentNameStatus
from ..ui import UIFormANOVA


def _get_sigmoid():
    def sigmoid(x):
        return 1 / (1 + math.exp(-x))

    def anti_sigmoid(y):
        return -math.log(1 / y - 1) / math.log(math.e)

    x1 = -math.log(0.05) / math.log(10)
    x2 = -math.log(0.01) / math.log(10)
    xe1 = anti_sigmoid(0.2)
    xe2 = anti_sigmoid(0.8)
    k = (xe2 - xe1) / (x2 - x1)
    b = xe1 - k * x1

    def s2(x):
        return sigmoid(k * x + b)

    return s2


class FormANOVA(QWidget, UIFormANOVA):
    def __init__(self):
        QWidget.__init__(self)
        self.__lock = Lock()
        self.setupUi(self)
        self._init()

    def _init(self):
        self._init_window_size()
        self._init_tabs()
        self._init_open_csv()
        self._init_table_independent()
        self._init_ind_add()
        self._init_ind_del()
        self._init_ind_clear()
        self._init_table_dependent()
        self._init_button_analysis()
        self._init_button_export()

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
                self.table_data.setProperty('names', names)
                self.table_data.setModel(model)
                self.table_data.setSortingEnabled(True)

                d_model = QStandardItemModel(0, 1)
                d_model.setHorizontalHeaderLabels(['Independent'])
                self.table_independents.setModel(d_model)
                self.button_ind_add.setEnabled(True)
                self.button_ind_del.setEnabled(False)
                self.button_ind_clear.setEnabled(True)

                ind_model = QStandardItemModel(0, 2)
                ind_model.setHorizontalHeaderLabels(['Dependent', 'Status'])
                for name in names:
                    item_name = QStandardItem(name)
                    item_name.setEditable(False)
                    nothing = DependentNameStatus.NOTHING
                    item_status = QStandardItem(nothing.icon, nothing.text)
                    item_status.setEditable(False)
                    item_status.setData(nothing)
                    ind_model.appendRow([item_name, item_status])

                self.table_dependents.setModel(ind_model)

                self.button_analysis.setEnabled(True)
                QMessageBox.information(self, 'Load Data', 'Completed!')

        self.button_open.clicked.connect(_open)

    def _init_table_independent(self):
        d_model = QStandardItemModel(0, 1)
        d_model.setHorizontalHeaderLabels(['Independent'])
        self.table_independents.setModel(d_model)
        self.table_independents.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        def _get_independents(self_: QTableView):
            model = self_.model()
            result = []
            for i in range(model.rowCount()):
                item: QStandardItem = model.item(i, 0)
                result.append(item.data())

            return result

        self.table_independents.get_independents = MethodType(_get_independents, self.table_independents)

    def _init_ind_add(self):
        def _no_less_than_1(d: DialogMultipleChoice):
            return len(d.chosen()) > 0 and tuple(d.chosen()) not in self.table_independents.get_independents()

        def _add():
            names = self.table_data.property('names')
            chosen, ok = DialogMultipleChoice.get_chosen(
                self, 'Add Dependent', 'Selection of dependent (no less than 1 column)',
                names, _no_less_than_1,
            )
            if ok:
                model: QStandardItemModel = self.table_independents.model()
                item = QStandardItem(','.join(chosen))
                item.setEditable(False)
                item.setData(tuple(chosen))
                model.appendRow(item)
                self.button_ind_del.setEnabled(True)

        self.button_ind_add.setIcon(qta.icon('msc.add'))
        self.button_ind_add.clicked.connect(_add)
        self.button_ind_add.setEnabled(False)

    def _init_ind_del(self):
        def _del():
            index = self.table_independents.currentIndex()
            model = self.table_independents.model()
            model.removeRow(index.row())

            if model.rowCount() == 0:
                self.button_ind_del.setEnabled(False)

        self.button_ind_del.setIcon(qta.icon('msc.remove'))
        self.button_ind_del.clicked.connect(_del)
        self.button_ind_del.setEnabled(False)

    def _init_ind_clear(self):
        def _clear():
            if QMessageBox.warning(self, 'Clear All Dependents',
                                   'All dependents will be cleared, continue?') == QMessageBox.Ok:
                d_model = QStandardItemModel(0, 1)
                d_model.setHorizontalHeaderLabels(['Dependent'])
                self.table_independents.setModel(d_model)
                self.button_ind_del.setEnabled(False)

        self.button_ind_clear.setIcon(qta.icon('msc.close'))
        self.button_ind_clear.clicked.connect(_clear)
        self.button_ind_clear.setEnabled(False)

    def _init_table_dependent(self):
        model = QStandardItemModel(0, 2)
        model.setHorizontalHeaderLabels(['Dependent', 'Status'])
        self.table_dependents.setModel(model)

        def _dbl_click(index: QModelIndex):
            model_ = self.table_dependents.model()
            if index.column() == 1:
                item: QStandardItem = model_.item(index.row(), index.column())
                next_status = item.data().next
                item.setText(next_status.text)
                item.setIcon(next_status.icon)
                item.setData(next_status)
                item.setFlags(Qt.ItemIsEnabled)
                model_.setItem(index.row(), index.column(), item)

        self.table_dependents.doubleClicked.connect(_dbl_click)
        self.table_dependents.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        def _get_dependents(self_: QTableView):
            model_ = self_.model()
            deps = []
            for i in range(model_.rowCount()):
                item_name = model_.item(i, 0)
                name = item_name.text()

                item_status = model_.item(i, 1)
                if item_status.data() == DependentNameStatus.DEPENDENT:
                    deps.append(name)

            return deps

        self.table_dependents.get_dependents = MethodType(_get_dependents, self.table_dependents)

    def _init_button_analysis(self):
        _sigmoid = _get_sigmoid()

        def _color(pr: float):
            if math.isnan(pr):
                return str(Color.from_hls(2 / 3, 0.985, 1.0))
            else:
                try:
                    _log10 = -math.log(pr) / math.log(10)
                except ValueError:
                    _log10 = +math.inf

                sv = _sigmoid(_log10)
                return str(Color.from_hls(1 / 6, (3 * (sv - 1) ** 2 + 5) / 8, 1.0))

        def _analysis():
            independents = self.table_independents.get_independents()
            dependents = self.table_dependents.get_dependents()

            model = QStandardItemModel(len(independents), len(dependents))
            model.setHorizontalHeaderLabels(dependents)
            model.setVerticalHeaderLabels(
                list(map(lambda x: ':'.join(map(lambda x_: 'C(%s)' % (x_,), x)), independents)))
            self.table_analysis.setModel(model)

            df: pd.DataFrame = self.table_data.property('data')
            names = self.table_data.property('names')
            new_names = {'name_%d' % (i,) for i in range(len(names))}
            name_to_new = dict(zip(names, new_names))

            dfx = pd.DataFrame({new_name: df[name] for name, new_name in name_to_new.items()})
            tail_str = ' + '.join(
                map(lambda x: ' * '.join(map(lambda x_: 'C(%s)' % (name_to_new[x_],), x)), independents))
            for j, dep in enumerate(dependents):
                sentence = '%s ~ %s' % (name_to_new[dep], tail_str)
                try:
                    anova_result = anova_lm(ols(sentence, data=dfx).fit())['PR(>F)']
                except ValueError:
                    anova_result = [math.nan] * len(independents)

                for i in range(len(independents)):
                    pr = anova_result[i]
                    item = QStandardItem('%.3e' % (pr,) if not math.isnan(pr) else str(pr))
                    item.setEditable(False)
                    item.setData(pr)
                    item.setBackground(QBrush(QColor(_color(pr))))
                    model.setItem(i, j, item)

            self.tabs_pages.setCurrentIndex(1)
            self.button_export.setEnabled(True)

        self.button_analysis.clicked.connect(_analysis)

    def _init_button_export(self):
        def _export():
            with self.__lock:
                filename, _ = QFileDialog.getSaveFileName(
                    self, 'Export Analysis', filter='*.csv', initialFilter='*.csv')
                if filename:
                    self.button_analysis.setEnabled(False)
                    self.button_export.setEnabled(False)
                    with open(filename, 'w', newline='') as csv_file:
                        model: QStandardItemModel = self.table_analysis.model()
                        m = model.columnCount()
                        n = model.rowCount()

                        writer = csv.writer(csv_file)
                        writer.writerow(['', *(
                            model.horizontalHeaderItem(i).text() for i in range(m)
                        )])
                        for i in range(n):
                            writer.writerow([
                                model.verticalHeaderItem(i).text(),
                                *(str(model.item(i, j).data()) for j in range(m))
                            ])

                    self.button_analysis.setEnabled(True)
                    self.button_export.setEnabled(True)
                    QMessageBox.information(self, 'Export Analysis', 'Completed!')

        self.button_export.clicked.connect(_export)

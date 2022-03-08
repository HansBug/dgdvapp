import csv
import math
from threading import Lock
from types import MethodType
from typing import List

import pandas as pd
import qtawesome as qta
from PyQt5.Qt import QWidget, Qt, QFileDialog, QStandardItemModel, QStandardItem, QMessageBox, QHeaderView, \
    QTableView, QModelIndex, QColor, QBrush, QThread, pyqtSignal
from hbutils.color import Color
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm

from .dialog_multiple_choice import DialogMultipleChoice
from .models import DependentNameStatus
from ..ui import UIFormANOVA


def _get_sigmoid(x1, y1, x2, y2):
    def sigmoid(x):
        return 1 / (1 + math.exp(-x))

    def anti_sigmoid(y):
        return -math.log(1 / y - 1)

    # x1 = -math.log(0.05) / math.log(10)
    # x2 = -math.log(0.01) / math.log(10)
    xe1 = anti_sigmoid(y1)
    xe2 = anti_sigmoid(y2)
    k = (xe2 - xe1) / (x2 - x1)
    b = xe1 - k * x1

    return lambda x: sigmoid(k * x + b)


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
                self, '加载数据', filter='*.csv', initialFilter='*.csv')
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
                d_model.setHorizontalHeaderLabels(['自变量'])
                self.table_independents.setModel(d_model)
                self.button_ind_add.setEnabled(True)
                self.button_ind_del.setEnabled(False)
                self.button_ind_clear.setEnabled(True)

                ind_model = QStandardItemModel(0, 2)
                ind_model.setHorizontalHeaderLabels(['因变量', '状态'])
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
                QMessageBox.information(self, '加载数据', '加载完毕')

        self.button_open.clicked.connect(_open)

    def _init_table_independent(self):
        d_model = QStandardItemModel(0, 1)
        d_model.setHorizontalHeaderLabels(['自变量'])
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
                self, '添加自变量', '请选择自变量 (至少选择一项，且不可与现有自变量重复)',
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
            if QMessageBox.warning(self, '清除所有自变量',
                                   '所有自变量将被清除，是否继续？') == QMessageBox.Ok:
                d_model = QStandardItemModel(0, 1)
                d_model.setHorizontalHeaderLabels(['自变量'])
                self.table_independents.setModel(d_model)
                self.button_ind_del.setEnabled(False)

        self.button_ind_clear.setIcon(qta.icon('msc.close'))
        self.button_ind_clear.clicked.connect(_clear)
        self.button_ind_clear.setEnabled(False)

    def _init_table_dependent(self):
        model = QStandardItemModel(0, 2)
        model.setHorizontalHeaderLabels(['因变量', '状态'])
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
        class _AnalysisThread(QThread):
            init = pyqtSignal(int)
            before_loop = pyqtSignal(int, int, str)
            after_loop = pyqtSignal(int, int, str, object, object, int, int)
            deinit = pyqtSignal(int)

            def __init__(self, parent, independents, dependents,
                         model: QStandardItemModel, df: pd.DataFrame, names: List[str]):
                QThread.__init__(self, parent)
                self.independents = independents
                self.dependents = dependents
                self.model = model
                self.df = df
                self.names = names

            def run(self) -> None:
                n = len(self.dependents)
                m = len(self.independents)
                self.init.emit(n)
                new_names = {'name_%d' % (i,) for i in range(len(self.names))}
                name_to_new = dict(zip(self.names, new_names))

                dfx = pd.DataFrame({new_name: self.df[name] for name, new_name in name_to_new.items()})
                total_rows = len(dfx)
                tail_str = ' + '.join(
                    map(lambda x: ' * '.join(map(lambda x_: 'C(%s)' % (name_to_new[x_],), x)), self.independents))
                for j, dep in enumerate(self.dependents):
                    self.before_loop.emit(j, n, dep)

                    new_dep = name_to_new[dep]
                    sentence = '%s ~ %s' % (new_dep, tail_str)
                    dfxc = dfx[dfx[new_dep] >= 0.0]
                    valid_rows = len(dfxc)
                    try:
                        anova_result = anova_lm(ols(sentence, data=dfxc).fit())
                        pr_result = anova_result['PR(>F)']
                    except ValueError:
                        anova_result = None
                        pr_result = [math.nan] * m

                    self.after_loop.emit(j, n, dep, anova_result, pr_result, valid_rows, total_rows)

                self.deinit.emit(n)

        _sigmoid_vl = _get_sigmoid(
            -math.log(0.05) / math.log(10), 0.2,
            -math.log(0.01) / math.log(10), 0.8,
        )

        def _color(pr: float):
            if math.isnan(pr):
                return str(Color.from_hls(2 / 3, 0.985, 1.0))
            else:
                try:
                    _log10 = -math.log(pr) / math.log(10)
                except ValueError:
                    _log10 = +math.inf

                svl = _sigmoid_vl(_log10)
                return str(Color.from_hls((1 - svl) / 6, (3 * (svl - 1) ** 2 + 5) / 8, 1.0))

        def _analysis():
            independents = self.table_independents.get_independents()
            dependents = self.table_dependents.get_dependents()

            model = QStandardItemModel(len(independents), len(dependents))
            self.table_analysis.setModel(model)

            df: pd.DataFrame = self.table_data.property('data')
            names = self.table_data.property('names')

            def _init(total):
                self.__lock.acquire()
                model.setHorizontalHeaderLabels(dependents)
                model.setVerticalHeaderLabels(
                    list(map(lambda x: ':'.join(map(lambda x_: 'C(%s)' % (x_,), x)), independents)))
                self.button_analysis.setEnabled(False)
                self.button_export.setEnabled(False)
                self.tabs_pages.setCurrentIndex(1)

            def _before_loop(j, total, dep):
                pass

            def _after_loop(j, total, dep, anova_result, pr_result, valid_rows, total_rows):
                for i in range(len(independents)):
                    indep = model.verticalHeaderItem(i).text()

                    pr = pr_result[i]
                    item = QStandardItem('%.3e' % (pr,) if not math.isnan(pr) else str(pr))
                    item.setEditable(False)
                    item.setData(pr)
                    item.setBackground(QBrush(QColor(_color(pr))))
                    if anova_result is not None:
                        item.setToolTip(f'{dep} ~ {indep}\n'
                                        f'有效 / 总量: {valid_rows} / {total_rows}\n'
                                        f'df: {anova_result["df"][i]}\n'
                                        f'sum_sq: {anova_result["sum_sq"][i]}\n'
                                        f'mean_sq: {anova_result["mean_sq"][i]}\n'
                                        f'F: {anova_result["F"][i]}\n'
                                        f'PR(>F): {anova_result["PR(>F)"][i]}')
                    else:
                        item.setToolTip(f'{dep} ~ {indep}\n'
                                        f'有效 / 总量: {valid_rows} / {total_rows}\n'
                                        f'方差分析结果非法')
                    model.setItem(i, j, item)

            def _deinit(total):
                self.button_analysis.setEnabled(True)
                self.button_export.setEnabled(True)
                self.__lock.release()
                QMessageBox.information(self, '数据分析', '分析完毕！')

            _thread = _AnalysisThread(self, independents, dependents,
                                      model, df, names)
            _thread.init.connect(_init)
            _thread.before_loop.connect(_before_loop)
            _thread.after_loop.connect(_after_loop)
            _thread.deinit.connect(_deinit)
            _thread.start()

        self.button_analysis.clicked.connect(_analysis)

    def _init_button_export(self):
        def _export():
            with self.__lock:
                filename, _ = QFileDialog.getSaveFileName(
                    self, '分析结果导出', filter='*.csv', initialFilter='*.csv')
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
                    QMessageBox.information(self, '分析结果导出', '导出完毕！')

        self.button_export.clicked.connect(_export)

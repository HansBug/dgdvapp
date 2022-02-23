from threading import Lock

import pandas as pd
import qtawesome as qta
from PyQt5.Qt import QWidget, Qt, QFileDialog, QStandardItemModel, QStandardItem, QMessageBox, QHeaderView

from .dialog_multiple_choice import DialogMultipleChoice
from ..ui import UIFormANOVA


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
        self._init_table_dependent()
        self._init_ind_add()
        self._init_ind_del()
        self._init_ind_clear()
        self._init_table_independent()

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
                d_model.setHorizontalHeaderLabels(['Dependent'])
                self.table_dependents.setModel(d_model)
                self.button_ind_add.setEnabled(True)
                self.button_ind_del.setEnabled(False)
                self.button_ind_clear.setEnabled(True)

                ind_model = QStandardItemModel(0, 2)
                ind_model.setHorizontalHeaderLabels(['Independent', 'Status'])
                self.table_independents.setModel(ind_model)

                QMessageBox.information(self, 'Load Data', 'Completed!')

        self.button_open.clicked.connect(_open)

    def _init_table_dependent(self):
        d_model = QStandardItemModel(0, 1)
        d_model.setHorizontalHeaderLabels(['Dependent'])
        self.table_dependents.setModel(d_model)
        self.table_dependents.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def _init_ind_add(self):
        def _no_less_than_1(d: DialogMultipleChoice):
            return len(d.chosen()) > 0

        def _add():
            names = self.table_data.property('names')
            chosen, ok = DialogMultipleChoice.get_chosen(
                self, 'Add Dependent', 'Selection of dependent (no less than 1 column)',
                names, _no_less_than_1,
            )
            if ok:
                model: QStandardItemModel = self.table_dependents.model()
                item = QStandardItem(','.join(chosen))
                item.setEditable(False)
                item.setData(chosen)
                model.appendRow(item)
                self.button_ind_del.setEnabled(True)

        self.button_ind_add.setIcon(qta.icon('msc.add'))
        self.button_ind_add.clicked.connect(_add)
        self.button_ind_add.setEnabled(False)

    def _init_ind_del(self):
        def _del():
            index = self.table_dependents.currentIndex()
            model = self.table_dependents.model()
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
                self.table_dependents.setModel(d_model)
                self.button_ind_del.setEnabled(False)

        self.button_ind_clear.setIcon(qta.icon('msc.close'))
        self.button_ind_clear.clicked.connect(_clear)
        self.button_ind_clear.setEnabled(False)

    def _init_table_independent(self):
        ind_model = QStandardItemModel(0, 2)
        ind_model.setHorizontalHeaderLabels(['Independent', 'Status'])
        self.table_independents.setModel(ind_model)
        self.table_independents.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

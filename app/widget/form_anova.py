from threading import Lock

import pandas as pd
import qtawesome as qta
from PyQt5.Qt import QWidget, Qt, QFileDialog, QStandardItemModel, QStandardItem, QMessageBox

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
        self._init_ind_add()
        self._init_ind_del()
        self._init_ind_clear()

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

                QMessageBox.information(self, 'Load Data', 'Completed!')

        self.button_open.clicked.connect(_open)

    def _init_ind_add(self):
        self.button_ind_add.setIcon(qta.icon('msc.add'))

    def _init_ind_del(self):
        self.button_ind_del.setIcon(qta.icon('msc.remove'))

    def _init_ind_clear(self):
        self.button_ind_clear.setIcon(qta.icon('msc.close'))

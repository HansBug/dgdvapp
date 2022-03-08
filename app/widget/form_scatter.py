from threading import Lock

import pandas as pd
import pyqtgraph as pg
import pyqtgraph.exporters
from PyQt5.Qt import QWidget, Qt, QFileDialog, QStandardItemModel, QStandardItem, QMessageBox, QModelIndex, \
    QHeaderView

from ..ui import UIFormScatter


class FormScatter(QWidget, UIFormScatter):
    def __init__(self):
        QWidget.__init__(self)
        self.__lock = Lock()
        self.setupUi(self)
        self._init()

    def _init(self):
        self._init_window_size()
        self._init_tabs()
        self._init_button_open()
        self._init_combo_x()
        self._init_combo_y()
        self._init_widget_graph()
        self._init_button_display()
        self._init_table_selected()
        self._init_button_export()

    def _init_window_size(self):
        self.setFixedSize(self.width(), self.height())
        self.setMaximumSize(self.width(), self.height())
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)

    def _init_tabs(self):
        self.tabs_pages.setCurrentIndex(0)

    def _init_button_open(self):
        def _open():
            filename, _ = QFileDialog.getOpenFileName(
                self, '加载数据', filter='*.csv', initialFilter='*.csv')
            if filename:
                with self.__lock:
                    self.button_open.setEnabled(False)
                    self.button_display.setEnabled(False)

                    df = pd.read_csv(filename)

                    n = len(df)
                    names = [name for name in df.columns]
                    m = len(names)
                    model = QStandardItemModel(n, m)
                    model.setHorizontalHeaderLabels(names)

                    for i in range(n):
                        for j, name in enumerate(names):
                            item = QStandardItem(str(df[name][i]))
                            item.setEditable(False)
                            model.setItem(i, j, item)

                    self.table_data.setProperty('data', df)
                    self.table_data.setProperty('names', names)
                    self.table_data.setModel(model)

                    self.combo_x.clear()
                    for name in names:
                        self.combo_x.addItem(name)

                    self.combo_y.clear()
                    for name in names:
                        self.combo_y.addItem(name)

                    data_okay = len(names) > 0 and len(df) > 0
                    self.button_open.setEnabled(True)
                    self.combo_x.setEnabled(data_okay)
                    self.combo_y.setEnabled(data_okay)
                    self.button_display.setEnabled(data_okay)
                    model = QStandardItemModel(0, 2)
                    model.setHorizontalHeaderLabels([self.combo_x.currentText(), self.combo_y.currentText()])
                    self.table_selected.setModel(model)
                    self.button_export.setEnabled(False)
                    graph = self.widget_graph.property('graph')
                    if graph is not None:
                        graph.deleteLater()
                    QMessageBox.information(self, '加载数据', '数据加载完毕！')

        self.button_open.clicked.connect(_open)

    def _init_combo_x(self):
        self.combo_x.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def _init_combo_y(self):
        self.combo_y.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def _init_widget_graph(self):
        self.widget_graph.setProperty('graph', None)

    def _init_button_display(self):
        def _click():
            with self.__lock:
                xname = self.combo_x.currentText()
                yname = self.combo_y.currentText()

                df = self.table_data.property('data')[[xname, yname]]
                dfc = df[(df[xname] >= 0.0) & (df[yname] >= 0.0)]
                self.button_export.setEnabled(False)
                graph = self.widget_graph.property('graph')
                if graph is not None:
                    graph.deleteLater()

                view = pg.GraphicsLayoutWidget(self.widget_graph, show=True,
                                               size=(self.widget_graph.width(), self.widget_graph.height()))
                view.addLabel(yname, angle=-90, rowspan=1)
                w1 = view.addPlot()
                view.nextRow()
                view.addLabel(xname, col=1, rowspan=1)
                self.widget_graph.setProperty('graph', view)

                clicked_pen = pg.mkPen('b', width=2)
                last_clicked = []

                def _point_click(plot, points):
                    nonlocal last_clicked
                    for p in last_clicked:
                        p.resetPen()
                    for p in points:
                        p.setPen(clicked_pen)
                    last_clicked = points

                    model_ = QStandardItemModel(0, 2)
                    model_.setHorizontalHeaderLabels([xname, yname])
                    self.table_selected.setModel(model_)
                    for i, point in enumerate(points):
                        pos = point.pos()
                        data = point.data()

                        item_x = QStandardItem('%.6f' % pos.x())
                        item_x.setEditable(False)
                        item_x.setData(data)
                        model_.setItem(i, 0, item_x)

                        item_y = QStandardItem('%.6f' % pos.y())
                        item_y.setEditable(False)
                        item_y.setData(data)
                        model_.setItem(i, 1, item_y)

                s1 = pg.ScatterPlotItem(size=10, pen=pg.mkPen(None), brush=pg.mkBrush(255, 255, 255, 120))

                s1.addPoints([{'pos': (r[xname], r[yname]), 'data': i} for i, r in dfc.iterrows()])
                s1.sigClicked.connect(_point_click)
                w1.addItem(s1)

                self.tabs_pages.setCurrentIndex(1)
                self.label_valid_total.setText(f'有效 / 总量: {len(dfc)} / {len(df)}')
                model = QStandardItemModel(0, 2)
                model.setHorizontalHeaderLabels([xname, yname])
                self.table_selected.setModel(model)
                self.button_export.setEnabled(True)
                QMessageBox.information(self, '散点图显示', '显示完毕！')

        self.button_display.clicked.connect(_click)

    def _init_table_selected(self):
        def _dbl_click(index: QModelIndex):
            model_ = self.table_selected.model()
            item: QStandardItem = model_.item(index.row(), index.column())
            origin_index = item.data()

            self.tabs_pages.setCurrentIndex(0)
            self.table_data.selectRow(origin_index)

        model = QStandardItemModel(0, 2)
        model.setHorizontalHeaderLabels(['<x>', '<y>'])
        self.table_selected.setModel(model)
        self.table_selected.doubleClicked.connect(_dbl_click)
        self.table_selected.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def _init_button_export(self):
        def _export():
            with self.__lock:
                view: pg.GraphicsLayoutWidget = self.widget_graph.property('graph')

                filename, filter_ = QFileDialog.getSaveFileName(
                    self, '图像导出',
                    filter='SVG矢量图片 (*.svg);;PNG图片 (*.png)',
                    initialFilter='SVG矢量图片 (*.svg)',
                )
                if 'svg' in filter_:
                    exporter = pg.exporters.SVGExporter(view.scene())
                elif 'png' in filter_:
                    exporter = pg.exporters.ImageExporter(view.scene())
                else:
                    raise ValueError(f'无法识别的文件格式 - {filter_}.')

                exporter.export(filename)
                QMessageBox.information(self, '图像导出', '图像导出完毕！')

        self.button_export.clicked.connect(_export)

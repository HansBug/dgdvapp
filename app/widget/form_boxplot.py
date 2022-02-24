import functools
import math
import os
from operator import itemgetter
from threading import Lock

import numpy as np
import pandas as pd
import pyqtgraph as pg
import pyqtgraph.exporters
from PyQt5 import QtGui
from PyQt5.Qt import QPointF, QRectF, Qt, pyqtSignal
from PyQt5.Qt import QWidget, QFileDialog, QStandardItemModel, QStandardItem, QMessageBox

from ..ui import UIFormBoxplot


def _q_value(s, name):
    values = s[name]
    q1, q2, q3 = np.percentile(values, (25, 50, 75), interpolation='midpoint')
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    min_ = min(values)
    max_ = max(values)
    mean_ = np.mean(values)
    std_ = np.std(values)
    errors = s[(s[name] > upper) | (s[name] < lower)][name]
    return (lower, q1, q2, q3, upper), (min_, max_, mean_, std_), list(errors)


def get_box_group(frame, x, y) -> pd.Series:
    return frame.groupby([x]).apply(functools.partial(_q_value, name=y))


class CandlestickItem(pg.GraphicsObject):
    boxClicked = pyqtSignal(float, tuple, tuple, list)

    def __init__(self, data):
        pg.GraphicsObject.__init__(self)
        self.data = data
        self.picture = QtGui.QPicture()
        self.x_min, self.x_max = +math.inf, -math.inf
        self.y_min, self.y_max = +math.inf, -math.inf

        self.boxs = []

        self.gen_picture()

    def gen_picture(self):
        self.picture = QtGui.QPicture()
        self.boxs = []
        p = QtGui.QPainter(self.picture)

        try:
            sx = sorted(map(itemgetter(0), self.data))
            try:
                dx = min([xb - xa for xa, xb in zip(sx[:-1], sx[1:])])
            except ValueError:
                dx = 1

            w, sw, kw = dx * 0.7, dx * 0.55, dx * 0.35
            old_brush = p.brush()
            for x, (lower, q1, q2, q3, upper), (min_, max_, mean_, std_), es in self.data:
                _y_min, _y_max = lower, upper
                iqr = q3 - q1

                p.setPen(pg.mkPen('w'))
                p.setBrush(old_brush)
                if q3 != upper:
                    p.drawLine(QPointF(x, q3), QPointF(x, upper))
                if q1 != lower:
                    p.drawLine(QPointF(x, q1), QPointF(x, lower))
                p.drawLine(QPointF(x - sw / 2, upper), QPointF(x + sw / 2, upper))
                p.drawLine(QPointF(x - sw / 2, lower), QPointF(x + sw / 2, lower))

                p.setPen(pg.mkPen('w'))
                p.setBrush(pg.mkBrush('#999999'))
                p.drawRect(QRectF(x - w / 2, q1, w, q2 - q1))
                p.drawRect(QRectF(x - w / 2, q2, w, q3 - q2))

                if min_ >= q1 - 3 * iqr:
                    _y_min = min(_y_min, min_)
                p.setPen(pg.mkPen('g'))
                p.drawLine(QPointF(x - sw / 2, min_), QPointF(x + sw / 2, min_))

                if max_ <= q3 + 3 * iqr:
                    _y_max = max(_y_max, max_)
                p.setPen(pg.mkPen('r'))
                p.drawLine(QPointF(x - sw / 2, max_), QPointF(x + sw / 2, max_))

                p.setPen(pg.mkPen('b'))
                p.drawLine(QPointF(x - sw / 2, mean_), QPointF(x + sw / 2, mean_))

                self.x_min = min(self.x_min, x - w / 2)
                self.x_max = max(self.x_max, x + w / 2)
                self.y_min = min(self.y_min, _y_min)
                self.y_max = max(self.y_max, _y_max)
                self.boxs.append(
                    (
                        (x - w / 2, q1, w, q3 - q1),
                        x,
                        (lower, q1, q2, q3, upper),
                        (min_, max_, mean_, std_),
                        es
                    )
                )

        finally:
            p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QRectF(self.picture.boundingRect())

    def mouseClickEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            px, py = ev.pos().x(), ev.pos().y()
            data = None
            for (x_, y_, w_, h_), x, qs, mx, es in self.boxs:
                if x_ <= px <= x_ + w_ and y_ <= py <= y_ + h_:
                    data = (x, qs, mx, es)
                    break

            if data is not None:
                ev.accept()
                x, qs, mx, es = data
                self.boxClicked.emit(x, qs, mx, es)
            else:
                ev.ignore()
        else:
            ev.ignore()


class FormBoxplot(QWidget, UIFormBoxplot):
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
        self._init_button_export()
        self._init_button_show_errors()

    def _init_window_size(self):
        self.setFixedSize(self.width(), self.height())
        self.setMaximumSize(self.width(), self.height())
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)

    def _init_tabs(self):
        self.tabs_pages.setCurrentIndex(0)

    def _init_button_open(self):
        def _open():
            filename, _ = QFileDialog.getOpenFileName(
                self, 'Load Data', filter='*.csv', initialFilter='*.csv')
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
                    self.button_export.setEnabled(False)
                    graph = self.widget_graph.property('graph')
                    if graph is not None:
                        graph.deleteLater()
                    QMessageBox.information(self, 'Load Data', 'Completed!')

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

                series: pd.Series = get_box_group(dfc, xname, yname)
                item = CandlestickItem([(x, qs, mx, es) for x, (qs, mx, es) in series.items()])

                def _box_click(x, qs, mx, es):
                    lower, q1, q2, q3, upper = qs
                    min_, max_, mean_, std_ = mx

                    self.label_x_value.setText(f'{xname}: {x}')
                    self.label_valid_total.setText(f'valid / total: {len(dfc)} / {len(df)}')
                    self.label_max.setText(f'Maximum: {max_}')
                    self.label_min.setText(f'Minimum: {min_}')
                    self.label_mean.setText(f'Mean: {mean_}')
                    self.label_std.setText(f'Std Dev.: {std_}')
                    self.label_qs.setText(f'q1 / q2 / q3: %.3f / %.3f / %.3f' % (q1, q2, q3))
                    self.label_bound.setText(f'Lower / Upper: %.4f / %.4f' % (lower, upper))
                    self.label_errors.setText(f'Error values: {len(es)}')
                    self.label_errors.setProperty('es', es)
                    self.button_show_errors.setEnabled(True)

                item.boxClicked.connect(_box_click)
                w1.addItem(item)

                dx = item.x_max - item.x_min
                w1.setXRange(item.x_min - dx * 0.1, item.x_max + dx * 0.1)

                dy = item.y_max - item.y_min
                w1.setYRange(item.y_min - dy * 0.1, item.y_max + dy * 0.1)

                self.tabs_pages.setCurrentIndex(1)
                self.label_valid_total.setText(f'valid / total: {len(dfc)} / {len(df)}')
                self.button_export.setEnabled(True)
                QMessageBox.information(self, 'Display Scatter', 'Completed!')

        self.button_display.clicked.connect(_click)

    def _init_button_export(self):
        def _export():
            with self.__lock:
                view: pg.GraphicsLayoutWidget = self.widget_graph.property('graph')

                filename, filter_ = QFileDialog.getSaveFileName(
                    self, 'Export Image',
                    filter='SVG Image (*.svg);;PNG Image (*.png)',
                    initialFilter='SVG Image (*.svg)',
                )
                if 'svg' in filter_:
                    exporter = pg.exporters.SVGExporter(view.scene())
                elif 'png' in filter_:
                    exporter = pg.exporters.ImageExporter(view.scene())
                else:
                    raise ValueError(f'Invalid filter - {filter_}.')

                exporter.export(filename)
                QMessageBox.information(self, 'Export Image', 'Completed!')

        self.button_export.clicked.connect(_export)

    def _init_button_show_errors(self):
        def _click():
            es = self.label_errors.property('es')
            QMessageBox.information(self, 'Error Values',
                                    f'Error values ({len(es)} in total):\n'
                                    f'{os.linesep.join(map(str, sorted(es)))}')

        self.button_show_errors.clicked.connect(_click)

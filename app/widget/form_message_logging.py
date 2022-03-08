import math
from threading import Lock
from typing import List, Tuple, Mapping

import pandas as pd
from PyQt5.Qt import QWidget, Qt, QFileDialog, QStandardItemModel, QStandardItem, QMessageBox, QPoint, QMenu, QAction, \
    QModelIndex, QThread, pyqtSignal, QColor
from hbutils.color import Color, rnd_colors

from .models import MessageType
from ..process import msgdata_trans
from ..ui import UIFormMessageLogging


class FormMessageLogging(QWidget, UIFormMessageLogging):
    def __init__(self):
        QWidget.__init__(self)
        self.__lock = Lock()
        self.setupUi(self)
        self._init()

    def _init(self):
        self._init_window_size()
        self._init_button_open()
        self._init_list_items()
        self._init_slide_start_time()
        self._init_slide_end_time()
        self._init_table_messages()
        self._init_button_logging()
        self._init_progress_status()
        self._init_button_export()

    def _init_window_size(self):
        self.setFixedSize(self.width(), self.height())
        self.setMaximumSize(self.width(), self.height())
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)

    def _init_button_open(self):
        def _open():
            filename, _ = QFileDialog.getOpenFileName(
                self, '打开消息日志文件',
                filter='消息日志文件 (msgData*.dat);;'
                       '其他数据文件 (*.data)',
                initialFilter='消息日志文件 (msgData*.dat)'
            )
            if filename:
                with self.__lock:
                    df = msgdata_trans(filename)
                    rows = len(df)

                    receivers = set(df['receive_id'])
                    senders = set(df['send_id'])
                    participants = sorted(receivers | senders)

                    model = QStandardItemModel(0, 1)
                    model.setHorizontalHeaderLabels(["参与者列表"])
                    for p in participants:
                        item = QStandardItem(str(p))
                        item.setData(p)
                        item.setEditable(False)
                        item.setCheckState(Qt.Unchecked)
                        item.setCheckable(True)
                        model.appendRow(item)

                    self.list_items.setModel(model)

                    data_okay = (rows > 0) and (len(participants) > 0)
                    self.button_logging.setEnabled(data_okay)
                    if data_okay:
                        max_time = math.ceil(max(df['time']))
                        min_time = math.floor(min(df['time']))

                        self.slider_start_time.setEnabled(True)
                        self.slider_start_time.setMinimum(min_time)
                        self.slider_start_time.setMaximum(max_time)
                        self.slider_start_time.setValue(min_time)
                        self.edit_start_time.setEnabled(True)
                        self.edit_start_time.setText(str(min_time))

                        self.slider_end_time.setEnabled(True)
                        self.slider_end_time.setMinimum(min_time)
                        self.slider_end_time.setMaximum(max_time)
                        self.slider_end_time.setValue(max_time)
                        self.edit_end_time.setEnabled(True)
                        self.edit_end_time.setText(str(max_time))

                    else:
                        self.slider_start_time.setEnabled(False)
                        self.slider_start_time.setMinimum(0.0)
                        self.slider_start_time.setMaximum(10.0)
                        self.slider_start_time.setValue(0.0)
                        self.edit_start_time.setEnabled(False)
                        self.edit_start_time.setText('')

                        self.slider_end_time.setEnabled(False)
                        self.slider_end_time.setMinimum(0.0)
                        self.slider_end_time.setMaximum(10.0)
                        self.slider_end_time.setValue(0.0)
                        self.edit_end_time.setEnabled(False)
                        self.edit_end_time.setText('')

                    self.setProperty('data', df)
                    QMessageBox.information(self, '打开消息日志文件',
                                            f'加载完毕!\n'
                                            f'已检测并加载{rows}条消息，包含{len(participants)}个参与实体。')

        self.button_open.clicked.connect(_open)

    def _init_list_items(self):
        def _show_menu(curpos: QPoint):
            model_: QStandardItemModel = self.list_items.model()
            menu = QMenu(self.list_items)
            index: QModelIndex = self.list_items.indexAt(curpos)

            item = model_.item(index.row(), index.column()) if index else None
            if item is not None:
                pass

            def _set_all_state(state):
                for i in range(model_.rowCount()):
                    item_: QStandardItem = model_.item(i, 0)
                    item_.setCheckState(state)
                    model_.setItem(i, 0, item_)

            action_select_all = QAction('全选(&A)', menu)
            action_select_all.triggered.connect(lambda: _set_all_state(Qt.Checked))
            menu.addAction(action_select_all)

            action_unselect_all = QAction('全不选(&D)', menu)
            action_unselect_all.triggered.connect(lambda: _set_all_state(Qt.Unchecked))
            menu.addAction(action_unselect_all)

            dest_point = self.list_items.mapToGlobal(curpos)
            menu.exec_(dest_point)

        self.list_items.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_items.customContextMenuRequested.connect(_show_menu)

        model = QStandardItemModel(0, 1)
        self.list_items.setModel(model)

    def _init_slide_start_time(self):
        def _changed():
            v = self.slider_start_time.value()
            self.edit_start_time.setText(str(v))
            self.slider_end_time.setValue(max(v, self.slider_end_time.value()))

        self.slider_start_time.valueChanged.connect(_changed)

    def _init_slide_end_time(self):
        def _changed():
            v = self.slider_end_time.value()
            self.edit_end_time.setText(str(v))
            self.slider_start_time.setValue(min(v, self.slider_start_time.value()))

        self.slider_end_time.valueChanged.connect(_changed)

    def _init_table_messages(self):
        model = QStandardItemModel(0, 4)
        model.setHorizontalHeaderLabels(['发送时间', '发送者ID', '接受者ID', '发送状态'])
        self.table_messages.setModel(model)

    def _init_button_logging(self):
        def _get_participants() -> Tuple[List[int], Mapping[int, Color]]:
            model: QStandardItemModel = self.list_items.model()
            ids = []
            for i in range(model.rowCount()):
                item: QStandardItem = model.item(i, 0)
                if item.checkState() == Qt.Checked:
                    ids.append(int(item.data()))

            ncnt = len(ids)
            map_ = {}
            cs = rnd_colors(ncnt, 0.9, 0.8)
            for i in range(model.rowCount()):
                item: QStandardItem = model.item(i, 0)
                if item.checkState() == Qt.Checked:
                    nc = next(cs)
                    idx = int(item.data())
                    map_[idx] = nc
                    item.setBackground(QColor(str(nc)))
                else:
                    item.setBackground(QColor('white'))

                model.setItem(i, 0, item)

            return ids, map_

        def _get_start_and_end() -> Tuple[float, float]:
            start_time = self.slider_start_time.value()
            end_time = self.slider_end_time.value()
            return start_time, end_time

        class _LoggingThread(QThread):
            init = pyqtSignal(int)
            loop = pyqtSignal(int, int, object)
            deinit = pyqtSignal(int)

            def __init__(self, parent, dfc: pd.DataFrame):
                QThread.__init__(self, parent)
                self.dfc = dfc

            def run(self) -> None:
                total_rows = len(self.dfc)
                self.init.emit(total_rows)

                for i, (_, row) in enumerate(self.dfc.iterrows()):
                    self.loop.emit(i, total_rows, row)

                self.deinit.emit(total_rows)

        def _show():
            pids, cmap = _get_participants()
            pid_set = set(pids)
            start_time, end_time = _get_start_and_end()

            df: pd.DataFrame = self.property('data')
            dfc = df[(df['time'] >= start_time) & (df['time'] <= end_time)
                     & (df['send_id'].isin(pid_set)) & (df['receive_id'].isin(pid_set))]
            self.table_messages.setProperty('data', dfc)

            model = QStandardItemModel(0, 4)
            model.setHorizontalHeaderLabels(['发送时间', '发送者ID', '接受者ID', '发送状态'])
            self.table_messages.setModel(model)

            def _init(total):
                self.__lock.acquire()
                self.button_export.setEnabled(False)
                self.progress_status.setMinimum(0)
                self.progress_status.setMaximum(total)
                self.progress_status.setValue(0)
                self.progress_status.setVisible(True)

            def _loop(i, total, row):
                item_time = QStandardItem(str(row['time']))
                item_time.setTextAlignment(Qt.AlignCenter)
                item_time.setEditable(False)

                send_id = int(row['send_id'])
                item_send = QStandardItem(str(send_id))
                item_send.setTextAlignment(Qt.AlignCenter)
                item_send.setEditable(False)
                item_send.setBackground(QColor(str(cmap[send_id])))

                receive_id = int(row['receive_id'])
                item_receive = QStandardItem(str(receive_id))
                item_receive.setTextAlignment(Qt.AlignCenter)
                item_receive.setEditable(False)
                item_receive.setBackground(QColor(str(cmap[receive_id])))

                type_ = MessageType.loads(int(row['type']))
                item_type = QStandardItem(type_.text)
                item_type.setIcon(type_.icon)
                item_type.setEditable(False)

                model.appendRow([item_time, item_send, item_receive, item_type])
                self.progress_status.setValue(i)

            def _deinit(total):
                self.button_export.setEnabled(True)
                self.__lock.release()
                QMessageBox.information(self, '消息日志查询', f'查询完毕!\n共计{total}条消息已被加载。')
                self.progress_status.setVisible(False)

            thread = _LoggingThread(self, dfc)
            thread.init.connect(_init)
            thread.loop.connect(_loop)
            thread.deinit.connect(_deinit)
            thread.start()

        self.button_logging.clicked.connect(_show)

    def _init_progress_status(self):
        self.progress_status.setVisible(False)

    def _init_button_export(self):
        def _export():
            dfc: pd.DataFrame = self.table_messages.property('data')
            filename, _ = QFileDialog.getSaveFileName(self, '消息日志导出',
                                                      filter='*.csv', initialFilter='*.csv')
            if filename:
                with self.__lock:
                    dfc.to_csv(filename)
                    QMessageBox.information(self, '消息日志导出',
                                            f'导出完毕!\n'
                                            f'已导出共计{len(dfc)}条消息。')

        self.button_export.clicked.connect(_export)

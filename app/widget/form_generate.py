import csv
import json
import os
from enum import IntEnum, unique
from json import JSONDecodeError
from typing import List, Optional, Dict, Tuple

import qtawesome as qta
from PyQt5.Qt import QWidget, QInputDialog, QToolButton, QMenu, QAction, QPoint, Qt, QMessageBox, QTableWidgetItem, \
    QTableWidget, QThread, pyqtSignal, QFileDialog, QHeaderView
from hbutils.model import int_enum_loads
from hbutils.string import plural_word
from hbutils.testing import AETGGenerator, MatrixGenerator, BaseGenerator
from natsort import natsorted

from .widget_edit_collection import WidgetEditCollection
from ..ui import UIFormGenerate


@int_enum_loads(enable_int=False, name_preprocess=str.upper)
@unique
class GenerateMethod(IntEnum):
    AETG = 1
    MATRIX = 2


_PROPERTY_CONFIG = [
    {
        'name': 'initial_num', 'init': 20,
        'type': 'int', 'min': 1, 'max': 1000,
    },
    {
        'name': 'loc_offset', 'init': 20,
        'type': 'int', 'min': -500, 'max': 500,
    },
    {
        'name': 'loc_err', 'init': 0.1,
        'type': 'float', 'min': 0.0, 'max': 1.0,
    },
    {
        'name': 'angle_error', 'init': 10.0,
        'type': 'float', 'min': -10.0, 'max': 10.0,
    },
    {
        'name': 'perception', 'multiple': True, 'init': [0.2, 0.5, 0.8],
        'type': 'float', 'min': 0.0, 'max': 1.0,
    },
    {
        'name': 'lost_possibility', 'multiple': True, 'init': [0.2, 0.5, 0.8],
        'type': 'float', 'min': 0.0, 'max': 1.0,
    },
    {
        'name': 'fuck', 'multiple': True, 'init': [3, 5],
        'type': 'int', 'min': 1, 'max': 5,
    },
]


class FormGenerate(QWidget, UIFormGenerate):
    def __init__(self, config: Optional[List[Dict]] = None):
        QWidget.__init__(self)
        self._property_config: List[Dict] = config or _PROPERTY_CONFIG
        self._collection: Optional[WidgetEditCollection] = None

        self.setupUi(self)
        self._init()

    @classmethod
    def open_config(cls, parent) -> Tuple[bool, Optional['FormGenerate']]:
        filename, _ = QFileDialog.getOpenFileName(parent, '加载参数配置', filter='*.json', initialFilter='*.json')
        if filename:
            try:
                print(filename)
                with open(filename, 'r') as sf:
                    _config = json.load(sf)
            except (IOError, PermissionError, JSONDecodeError) as err:
                QMessageBox.critical(parent, '加载配置错误', f'加载配置出现错误，错误信息：{os.linesep}{err!r}.')
                return False, None

            return True, cls(_config)
        else:
            return False, None

    def _init(self):
        self._init_window_size()
        self._init_widget_properties()
        self._init_table_control_type()
        self._init_table_result()
        self._init_button_generate()

    def _init_window_size(self):
        self.setFixedSize(self.width(), self.height())
        self.setMaximumSize(self.width(), self.height())
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)

    def _init_widget_properties(self):
        self._collection = WidgetEditCollection.parse_json(
            self._property_config, self.widget_properties,
            height=self.widget_properties.height() - 10,
            width=self.widget_properties.width() - 15,
        )
        self._collection.textChanged.connect(lambda w, v, vv: self._update_enablement())

    def _init_table_control_type(self):
        table = self.table_control_type
        table.setColumnCount(2)
        table.setProperty('data', [])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        def _edit_item_time(row):
            data: list = table.property('data')
            item_str_lines = data[row]['time']
            time_str, time_ok = QInputDialog.getMultiLineText(
                self, '修改指令时间',
                '请编辑指令时间 (每行一条，不小于0):', os.linesep.join(item_str_lines)
            )

            if time_ok:
                time_items = natsorted(set(filter(bool, map(str.strip, time_str.splitlines()))))

                ti_time = QTableWidgetItem(','.join(map(str, time_items)))
                ti_time.setFlags(Qt.ItemIsEnabled)
                table.setItem(row, 0, ti_time)

                data[row]['time'] = time_items
                table.setProperty('data', data)

        def _edit_item_control(row):
            data: list = table.property('data')
            control_lines = data[row]['control']
            control_str, control_ok = QInputDialog.getMultiLineText(
                self, '修改控制指令',
                '请修改控制指令 (依次为gap,type,R1,R2,R3，用英文逗号分隔，每行一条):',
                os.linesep.join([','.join(ld) for ld in control_lines])
            )

            if control_ok:
                control_lines = filter(bool, map(str.strip, control_str.splitlines()))
                control_items = []
                for lineno, line in enumerate(control_lines, 1):
                    try:
                        gap, type_, r1, r2, r3 = map(str.strip, line.split(',', maxsplit=4))
                    except ValueError:
                        QMessageBox.critical(
                            self, '添加控制指令',
                            f'第{repr(lineno)}行指令信息非法 - {repr(line)}.'
                        )
                        return
                    else:
                        control_items.append((gap, type_, r1, r2, r3))

                ti_control = QTableWidgetItem('(' + plural_word(len(control_items), 'command') + ')')
                ti_control.setFlags(Qt.ItemIsEnabled)
                table.setItem(row, 1, ti_control)

                data[row]['control'] = control_items
                table.setProperty('data', data)

        def _edit_cell(row, column):
            if column == 0:
                _edit_item_time(row)
            elif column == 1:
                _edit_item_control(row)
            else:
                raise ValueError(f'非法行信息 - {repr(column)}.')

        table.cellDoubleClicked.connect(_edit_cell)

        def _add_item(time_items, control_items):
            row_cnt = table.rowCount()
            data: list = table.property('data')
            table.insertRow(row_cnt)

            time_items = list(map(str, time_items))
            control_items = [(str(gap), str(type_), str(r1), str(r2), str(r3))
                             for gap, type_, r1, r2, r3 in control_items]

            ti_time = QTableWidgetItem(','.join(map(str, time_items)))
            ti_time.setFlags(Qt.ItemIsEnabled)
            table.setItem(row_cnt, 0, ti_time)
            ti_control = QTableWidgetItem('(' + plural_word(len(control_items), 'command') + ')')
            ti_control.setFlags(Qt.ItemIsEnabled)
            table.setItem(row_cnt, 1, ti_control)

            data.insert(row_cnt, {
                'time': time_items,
                'control': control_items,
            })
            table.setProperty('data', data)
            self.edit_control_num.setText(str(len(data)))

        def _validate_time(tstr):
            try:
                v = int(tstr)
                assert 0 <= v
            except (ValueError, AssertionError):
                QMessageBox.critical(self, '添加控制指令', f'非法时间信息 - {repr(tstr)}.')
                return None
            else:
                return tstr

        def _validate_timelines(tm_str):
            time_items = natsorted(set(filter(bool, map(str.strip, tm_str.splitlines()))))
            for item in time_items:
                if not _validate_time(item):
                    return None

            return time_items

        def _add_new_item():
            time_str, time_ok = QInputDialog.getMultiLineText(self, '添加控制指令', '请输入指令时间 (每行一条，不小于0):')
            if time_ok and _validate_timelines(time_str) is not None:
                time_items = _validate_timelines(time_str)
                control_str, control_ok = QInputDialog.getMultiLineText(
                    self, '添加控制指令',
                    '请输入控制指令 (依次为gap,type,R1,R2,R3，用英文逗号分隔，每行一条):'
                )
                if control_ok:
                    control_lines = filter(bool, map(str.strip, control_str.splitlines()))
                    control_items = []
                    for lineno, line in enumerate(control_lines, 1):
                        try:
                            gap, type_, r1, r2, r3 = map(str.strip, line.split(',', maxsplit=4))
                        except ValueError:
                            QMessageBox.critical(
                                self, '添加控制指令',
                                f'第{repr(lineno)}行指令信息非法 - {repr(line)}.'
                            )
                            return
                        else:
                            control_items.append((gap, type_, r1, r2, r3))

                    _add_item(time_items, control_items)

        def _del_one_item(item: QTableWidgetItem):
            row = item.row()
            data: list = table.property('data')
            if QMessageBox.warning(
                    self, '删除指令信息',
                    f'第{repr(row)}行指令信息将被删除，是否继续？',
                    QMessageBox.Ok | QMessageBox.Cancel,
            ) == QMessageBox.Ok:
                data.pop(row)
                table.removeRow(row)

                table.setProperty('data', data)
                self.edit_control_num.setText(str(len(data)))

        def _clear_all_items():
            data: list = table.property('data')
            if QMessageBox.warning(
                    self, '删除全部指令信息',
                    f'全部指令信息将被删除，是否继续？',
                    QMessageBox.Ok | QMessageBox.Cancel
            ) == QMessageBox.Ok:
                data.clear()
                table.setRowCount(0)

                table.setProperty('data', data)
                self.edit_control_num.setText(str(len(data)))

        def _show_menu(curpos: QPoint):
            menu = QMenu(table)
            item = table.itemAt(curpos)

            if item is not None:
                row = item.row()
                action_del_item = QAction(qta.icon('msc.remove'), f'删除第{repr(row)}条指令信息(&D)', menu)
                action_del_item.triggered.connect(lambda: _del_one_item(item))
                menu.addAction(action_del_item)

                menu.addSeparator()

            action_add_item = QAction(qta.icon('msc.add'), '添加新指令信息(&A)', menu)
            action_add_item.triggered.connect(_add_new_item)
            menu.addAction(action_add_item)

            action_clear = QAction(qta.icon('msc.clear-all'), '删除全部指令信息(&C)', menu)
            action_clear.triggered.connect(_clear_all_items)
            menu.addAction(action_clear)

            dest_point = table.mapToGlobal(curpos)
            menu.exec_(dest_point)

        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(_show_menu)

        _add_item(
            [0],
            [
                (20, 1, 90, 0, 0),
                (20, 2, 85, 40, 0),
                (20, 4, 50, 300, 50),
                (20, 4, 70, 80, 60),
                (20, 5, 60, 100, 0),
                (35, 3, 140, 100, 70),
                (50, 1, 200, 0, 0),
                (50, 2, 200, 150, 0),
                (50, 3, 200, 150, 100),
                (50, 3, 210, 200, 100),
                (70, 2, 450, 200, 0),
                (70, 3, 210, 200, 200),
                (70, 5, 110, 300, 0),
                (90, 1, 305, 0, 0),
                (90, 2, 330, 300, 0),
                (90, 4, 200, 210, 200),
                (90, 4, 200, 400, 200),
                (90, 5, 145, 400, 0),
                (90, 5, 270, 270, 0),
                (110, 1, 400, 0, 0),
            ]
        )
        _add_item(
            [45, 50, 60, 70, 75, 80, 100, 120],
            [
                (20, 0, 0, 0, 0),
                (20, 1, 90, 0, 0),
                (35, 0, 0, 0, 0),
                (50, 0, 0, 0, 0),
                (50, 1, 200, 0, 0),
                (50, 2, 200, 150, 0),
                (50, 3, 200, 150, 100),
                (70, 0, 0, 0, 0),
                (70, 2, 450, 200, 0),
                (70, 3, 210, 200, 200),
                (90, 0, 0, 0, 0),
                (90, 1, 305, 0, 0),
                (90, 2, 330, 300, 0),
                (90, 4, 200, 210, 200),
                (110, 1, 400, 0, 0),
            ]
        )

    def _table_result_set_title(self, title: List[str]):
        table: QTableWidget = self.table_result
        table.setColumnCount(len(title))
        for i, name in enumerate(title):
            table.setHorizontalHeaderItem(i, QTableWidgetItem(name))

    def _table_result_add_line(self, values):
        table: QTableWidget = self.table_result
        row_cnt = table.rowCount()
        table.insertRow(row_cnt)
        for i, value in enumerate(values):
            table.setItem(row_cnt, i, QTableWidgetItem(str(value)))

    def _init_table_result(self):
        table: QTableWidget = self.table_result
        table.setSortingEnabled(True)
        self._table_result_set_title(
            [
                *(prop['name'] for prop in self._property_config),
                'control_num'
            ]
        )

        def _export_to_csv():
            filename, _ = QFileDialog.getSaveFileName(self, '将结果导出为CSV表格', filter='*.csv')
            if filename:
                n, m = table.rowCount(), table.columnCount()
                data = [[table.horizontalHeaderItem(i).text() for i in range(m)]]
                for i in range(n):
                    data.append([table.item(i, j).text() for j in range(m)])

                with open(filename, 'w', newline='') as csv_file:
                    writer = csv.writer(csv_file)
                    for line in data:
                        writer.writerow(line)

                QMessageBox.information(self, '将结果导出为CSV表格', f'已经导出至{repr(filename)}')

        def _show_menu(curpos: QPoint):
            menu = QMenu(table)

            action_export = QAction(qta.icon('msc.export'), '导出结果(&E)...', menu)
            action_export.triggered.connect(_export_to_csv)
            menu.addAction(action_export)

            dest_point = table.mapToGlobal(curpos)
            menu.exec_(dest_point)

        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(_show_menu)

    def _init_button_generate(self):
        result: QTableWidget = self.table_result
        button = self.button_generate

        class _GenerateThread(QThread):
            init_table = pyqtSignal(list)
            new_result = pyqtSignal(int, tuple)
            completed = pyqtSignal(int)

            def __init__(self, parent, generator):
                QThread.__init__(self, parent)
                self.__generator: BaseGenerator = generator

            def run(self) -> None:
                self.init_table.emit(self.__generator.names)
                cnt = 0
                for p in self.__generator.tuple_cases():
                    cnt += 1
                    self.new_result.emit(cnt, p)

                self.completed.emit(cnt)

        def _generate(method):
            method: GenerateMethod = GenerateMethod.loads(method)
            _properties = self._collection.value
            table_title = [*_properties.keys(), 'control_num']

            names = []
            free_names = []
            time_names = []
            control_names = []
            values = {}
            _fixed_dict = {}
            for name, value in _properties.items():
                if isinstance(value, list):
                    names.append(name)
                    values[name] = value
                    free_names.append(name)
                else:
                    _fixed_dict[name] = value

            mappings = {}
            for index, control_item in enumerate(self.control_items):
                ctimes, ccontrols = control_item['time'], control_item['control']

                name_time = f'name_{index}'
                names.append(name_time)
                time_names.append(name_time)
                mappings[name_time] = {i: t for i, t in enumerate(ctimes)}
                values[name_time] = tuple(mappings[name_time].keys())
                table_title.append('time')

                name_control = f'control_{index}'
                control_names.append(name_control)
                names.append(name_control)
                mappings[name_control] = {i: t for i, t in enumerate(ccontrols)}
                values[name_control] = tuple(mappings[name_control].keys())
                table_title.append('gap')
                table_title.append('type')
                table_title.append('R1')
                table_title.append('R2')
                table_title.append('R3')

            if method == GenerateMethod.AETG:
                generator = AETGGenerator(
                    values=values, names=names,
                    pairs=[
                        tuple(free_names),
                        tuple(time_names),
                        tuple(control_names),
                    ]
                )
            elif method == GenerateMethod.MATRIX:
                generator = MatrixGenerator(
                    values=values, names=names,
                )
            else:
                raise ValueError(f'非法方法 - {repr(method)}.')

            def _init_table(ns):
                result.setRowCount(0)
                self._table_result_set_title(table_title)
                self.label_status.setText(f'初始化完毕...')

            def _new_result(inx, pi):
                _pair_offset = 0
                vs = []
                for name_, value_ in _properties.items():
                    if isinstance(value_, list):
                        vs.append(pi[_pair_offset])
                        _pair_offset += 1
                    else:
                        vs.append(value_)

                vs.append(self.control_num)
                for i in range(_pair_offset, len(pi), 2):
                    tvalue = mappings[names[i]][pi[i]]
                    cvalue = mappings[names[i + 1]][pi[i + 1]]
                    vs.append(tvalue)
                    vs += cvalue

                self._table_result_add_line(vs)
                self.label_status.setText(f'已经产生{inx}条结果...')

            def _completed(cnt):
                QMessageBox.information(self, '测试数据生成', f'总计{cnt}条测试数据，已生成完毕！')
                self.label_status.setText(f'已完成')

            g = _GenerateThread(self, generator)
            g.init_table.connect(_init_table, Qt.QueuedConnection)
            g.new_result.connect(_new_result, Qt.QueuedConnection)
            g.completed.connect(_completed, Qt.QueuedConnection)
            g.start()

        menu = QMenu(button)
        action_use_matrix = QAction("使用笛卡尔积策略生成(&M)", menu)
        action_use_matrix.triggered.connect(lambda: _generate(GenerateMethod.MATRIX))
        menu.addAction(action_use_matrix)
        action_use_matrix = QAction("使用AETG算法生成(&A)", menu)
        action_use_matrix.triggered.connect(lambda: _generate(GenerateMethod.AETG))
        menu.addAction(action_use_matrix)

        self.button_generate.setMenu(menu)
        self.button_generate.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

    def _update_enablement(self):
        self.button_generate.setEnabled(self._collection.valid)

    @property
    def control_num(self) -> str:
        return self.edit_control_num.text()

    @property
    def control_items(self) -> List:
        return self.table_control_type.property('data')

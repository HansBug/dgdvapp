import csv
import os
from enum import IntEnum, unique
from types import MethodType
from typing import List

import qtawesome as qta
from PyQt5.Qt import QWidget, QInputDialog, QToolButton, QMenu, QAction, QPoint, Qt, QMessageBox, QTableWidgetItem, \
    QTableWidget, QThread, pyqtSignal, QFileDialog, QHeaderView, QIntValidator
from hbutils.color import Color
from hbutils.model import int_enum_loads
from hbutils.string import plural_word
from hbutils.testing import AETGGenerator, MatrixGenerator, BaseGenerator
from natsort import natsorted

from ..ui import UIFormGenerate


@int_enum_loads(enable_int=False, name_preprocess=str.upper)
@unique
class GenerateMethod(IntEnum):
    AETG = 1
    MATRIX = 2


class FormGenerate(QWidget, UIFormGenerate):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)
        self._init()

    def _init(self):
        self._init_window_size()
        self._init_initial_num()
        self._init_loc_offset()
        self._init_perception()
        self._init_lost_possibility()
        self._init_table_control_type()
        self._init_table_result()
        self._init_button_generate()

    def _init_window_size(self):
        self.setFixedSize(self.width(), self.height())
        self.setMaximumSize(self.width(), self.height())
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)

    def _init_initial_num(self):
        _validator = QIntValidator(1, 1000, self.edit_initial_num)
        self.edit_initial_num.setValidator(_validator)

        def _validate(t):
            try:
                v = int(t)
            except ValueError:
                return False, None

            if 1 <= v <= 1000:
                return True, v
            else:
                return False, None

        def _text_change():
            text = self.edit_initial_num.text()
            ok, val = _validate(text)
            self.edit_initial_num.setProperty('ok', ok)

            color = Color('black' if ok else 'red')
            self.edit_initial_num.setStyleSheet(f"""
            QLineEdit {{
                color: {color};
            }}
            """)
            self.label_initial_num.setStyleSheet(f"""
            QLabel {{
                color: {color};
            }}
            """)
            self._update_enablement()

        _text_change()
        self.edit_initial_num.textChanged.connect(_text_change)

    def _init_loc_offset(self):
        _validator = QIntValidator(-500, 500, self.edit_loc_offset)
        self.edit_loc_offset.setValidator(_validator)

        def _validate(t):
            try:
                v = int(t)
            except ValueError:
                return False, None

            if -500 <= v <= 500:
                return True, v
            else:
                return False, None

        def _text_change():
            text = self.edit_loc_offset.text()
            ok, val = _validate(text)
            self.edit_loc_offset.setProperty('ok', ok)

            color = Color('black' if ok else 'red')
            self.edit_loc_offset.setStyleSheet(f"""
            QLineEdit {{
                color: {color};
            }}
            """)
            self.label_loc_offset.setStyleSheet(f"""
            QLabel {{
                color: {color};
            }}
            """)
            self._update_enablement()

        _text_change()
        self.edit_loc_offset.textChanged.connect(_text_change)

    def _init_perception(self):
        def _edit_perception():
            current_items = self.perceptions
            result_str, result_ok = QInputDialog.getMultiLineText(self, 'Edit Perceptions', 'Update new perceptions:',
                                                                  os.linesep.join(current_items))
            if result_ok:
                items = natsorted(filter(bool, map(str.strip, result_str.splitlines())))
                self.edit_perception.setText(','.join(items))

        _button_edit = QToolButton(self)
        _button_edit.setFixedHeight(self.edit_perception.height())
        _button_edit.setFixedWidth(self.edit_initial_num.width() - self.edit_perception.width())
        _button_edit.setText('...')
        _button_edit.move(self.edit_perception.x() + self.edit_perception.width(), self.edit_perception.y())
        _button_edit.clicked.connect(_edit_perception)
        self.edit_perception.mouseDoubleClickEvent = MethodType(lambda s, e: _edit_perception(), self)

    def _init_lost_possibility(self):
        def _edit_lost_possibility():
            current_items = self.lost_possibilities
            result_str, result_ok = QInputDialog.getMultiLineText(
                self, 'Edit Lost Possibilities', 'Update new lost_possibilities:', os.linesep.join(current_items))
            if result_ok:
                items = natsorted(filter(bool, map(str.strip, result_str.splitlines())))
                self.edit_lost_possibility.setText(','.join(items))

        _button_edit = QToolButton(self)
        _button_edit.setFixedHeight(self.edit_lost_possibility.height())
        _button_edit.setFixedWidth(self.edit_initial_num.width() - self.edit_lost_possibility.width())
        _button_edit.setText('...')
        _button_edit.move(self.edit_lost_possibility.x() + self.edit_lost_possibility.width(),
                          self.edit_lost_possibility.y())
        _button_edit.clicked.connect(_edit_lost_possibility)
        self.edit_lost_possibility.mouseDoubleClickEvent = MethodType(lambda s, e: _edit_lost_possibility(), self)

    def _init_table_control_type(self):
        table = self.table_control_type
        table.setColumnCount(2)
        table.setProperty('data', [])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        def _edit_item_time(row):
            data: list = table.property('data')
            item_str_lines = data[row]['time']
            time_str, time_ok = QInputDialog.getMultiLineText(
                self, 'Edit Item Time',
                'Edit the times of control:', os.linesep.join(item_str_lines)
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
                self, 'Edit Item Control',
                'Input the control items (gap,type,R1,R2,R3):',
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
                            self, 'Add Control Item',
                            f'Invalid control as line {repr(lineno)} - {repr(line)}.'
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
                raise ValueError(f'Invalid column - {repr(column)}.')

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

        def _add_new_item():
            time_str, time_ok = QInputDialog.getMultiLineText(self, 'Add Control Item', 'Input the times of control:')
            if time_ok:
                time_items = natsorted(set(filter(bool, map(str.strip, time_str.splitlines()))))
                control_str, control_ok = QInputDialog.getMultiLineText(
                    self, 'Add Control Item',
                    'Input the control items (gap,type,R1,R2,R3):'
                )
                if control_ok:
                    control_lines = filter(bool, map(str.strip, control_str.splitlines()))
                    control_items = []
                    for lineno, line in enumerate(control_lines, 1):
                        try:
                            gap, type_, r1, r2, r3 = map(str.strip, line.split(',', maxsplit=4))
                        except ValueError:
                            QMessageBox.critical(
                                self, 'Add Control Item',
                                f'Invalid control as line {repr(lineno)} - {repr(line)}.'
                            )
                            return
                        else:
                            control_items.append((gap, type_, r1, r2, r3))

                    _add_item(time_items, control_items)

        def _del_one_item(item: QTableWidgetItem):
            row = item.row()
            data: list = table.property('data')
            if QMessageBox.warning(
                    self, 'Delete Control Item',
                    f'Control item {repr(row)} will be removed, continue?',
                    QMessageBox.Ok | QMessageBox.Cancel,
            ) == QMessageBox.Ok:
                data.pop(row)
                table.removeRow(row)

                table.setProperty('data', data)
                self.edit_control_num.setText(str(len(data)))

        def _clear_all_items():
            data: list = table.property('data')
            if QMessageBox.warning(
                    self, 'Clear all items',
                    f'All control items will be cleared, continue?',
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
                action_del_item = QAction(qta.icon('msc.remove'), f'&Delete control item {repr(row)}', menu)
                action_del_item.triggered.connect(lambda: _del_one_item(item))
                menu.addAction(action_del_item)

                menu.addSeparator()

            action_add_item = QAction(qta.icon('msc.add'), '&Add new control item', menu)
            action_add_item.triggered.connect(_add_new_item)
            menu.addAction(action_add_item)

            action_clear = QAction(qta.icon('msc.clear-all'), '&Clear all items', menu)
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
            ['initial_num', 'loc_offset', 'loc_err', 'angle_err', 'perception', 'lost_possibility', 'control_num']
        )

        def _export_to_csv():
            filename, _ = QFileDialog.getSaveFileName(self, 'Export Result to CSV', filter='*.csv')
            if filename:
                n, m = table.rowCount(), table.columnCount()
                data = [[table.horizontalHeaderItem(i).text() for i in range(m)]]
                for i in range(n):
                    data.append([table.item(i, j).text() for j in range(m)])

                with open(filename, 'w', newline='') as csv_file:
                    writer = csv.writer(csv_file)
                    for line in data:
                        writer.writerow(line)

                QMessageBox.information(self, 'Export Result to CSV', f'Exported to {repr(filename)}.')

        def _show_menu(curpos: QPoint):
            menu = QMenu(table)

            action_export = QAction(qta.icon('msc.export'), '&Export to csv', menu)
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
            table_title = ['initial_num', 'loc_offset', 'loc_err', 'angle_err',
                           'perception', 'lost_possibility', 'control_num']
            names = ['perception', 'lost_possibility', ]
            time_names = []
            control_names = []
            values = {
                'perception': self.perceptions,
                'lost_possibility': self.lost_possibilities,
            }
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
                        ('perception', 'lost_possibility'),
                        tuple(time_names),
                        tuple(control_names),
                    ]
                )
            elif method == GenerateMethod.MATRIX:
                generator = MatrixGenerator(
                    values=values, names=names,
                )
            else:
                raise ValueError(f'Invalid method - {repr(method)}.')

            def _init_table(ns):
                result.setRowCount(0)
                self._table_result_set_title(table_title)
                self.label_status.setText(f'Initialized...')

            def _new_result(inx, pi):
                vs = [
                    self.initial_num, self.loc_offset, self.loc_err, self.angle_err,
                    pi[0], pi[1], self.control_num,
                ]
                for i in range(2, len(pi), 2):
                    tvalue = mappings[names[i]][pi[i]]
                    cvalue = mappings[names[i + 1]][pi[i + 1]]
                    vs.append(tvalue)
                    vs += cvalue

                self._table_result_add_line(vs)
                self.label_status.setText(f'{plural_word(inx, "result")} generated...')

            def _completed(cnt):
                QMessageBox.information(self, 'Result Generation', f'{plural_word(cnt, "result")} generated!')
                self.label_status.setText(f'Completed.')

            g = _GenerateThread(self, generator)
            g.init_table.connect(_init_table, Qt.QueuedConnection)
            g.new_result.connect(_new_result, Qt.QueuedConnection)
            g.completed.connect(_completed, Qt.QueuedConnection)
            g.start()

        menu = QMenu(button)
        action_use_matrix = QAction("Use &Matrix Mode", menu)
        action_use_matrix.triggered.connect(lambda: _generate(GenerateMethod.MATRIX))
        menu.addAction(action_use_matrix)
        action_use_matrix = QAction("Use &AETG Mode", menu)
        action_use_matrix.triggered.connect(lambda: _generate(GenerateMethod.AETG))
        menu.addAction(action_use_matrix)

        self.button_generate.setMenu(menu)
        self.button_generate.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

    def _update_enablement(self):
        ok = bool(self.edit_initial_num.property('ok') and self.edit_loc_offset.property('ok'))
        self.button_generate.setEnabled(ok)

    @property
    def initial_num(self) -> str:
        return self.edit_initial_num.text()

    @property
    def loc_offset(self) -> str:
        return self.edit_loc_offset.text()

    @property
    def loc_err(self) -> str:
        return self.edit_loc_err.text()

    @property
    def angle_err(self) -> str:
        return self.edit_angle_err.text()

    @property
    def perceptions(self) -> List[str]:
        return natsorted(filter(bool, map(str.strip, self.edit_perception.text().split(','))))

    @property
    def lost_possibilities(self) -> List[str]:
        return natsorted(filter(bool, map(str.strip, self.edit_lost_possibility.text().split(','))))

    @property
    def control_num(self) -> str:
        return self.edit_control_num.text()

    @property
    def control_items(self) -> List:
        return self.table_control_type.property('data')

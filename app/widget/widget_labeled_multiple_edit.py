import os
from typing import List

import inflection
from PyQt5.Qt import QWidget
from PyQt5.QtWidgets import QInputDialog, QMessageBox
from natsort import natsorted

from ..ui import UILabeledMultipleEdit


def _to_list(vs) -> List:
    if isinstance(vs, (set, list, tuple)):
        return list(vs)
    else:
        return [vs]


class WidgetLabeledMultipleEdit(QWidget, UILabeledMultipleEdit):
    def __init__(self, parent, label, init_value=None, placeholder=None,
                 dialog_title=None, dialog_text=None):
        QWidget.__init__(self, parent)
        self.label = label
        self.init_value = init_value
        self.placeholder = placeholder
        self.dialog_title = dialog_title or f'Edit {label}'
        self.dialog_text = dialog_text or f'Edit the values of {label}:'

        self._values = self._validate_list(self.init_value or [])

        self.setupUi(self)
        self._init()

    def _init(self):
        self._init_label()
        self._init_content()
        self._init_edit()
        self._init_layout()

    def _init_label(self):
        self.edit_name.setText(self.label)

    def _init_content(self):
        if self.placeholder:
            self.edit_content.setPlaceholderText(self.placeholder)
        self._text_change_call()

    def _init_edit(self):
        def _edit_perception():
            result_str, result_ok = QInputDialog.getMultiLineText(
                self, self.dialog_title, self.dialog_text,
                os.linesep.join(map(self._devalidate_one, self._values))
            )
            if result_ok:
                items = natsorted(filter(bool, map(str.strip, result_str.splitlines())))
                try:
                    self._values = self._validate_list(items)
                except ValueError as err:
                    msg, *_ = err.args
                    QMessageBox.information(self, self.dialog_title, msg)
                else:
                    self._text_change_call()

        self.edit_edit.clicked.connect(_edit_perception)
        self.edit_content.mouseDoubleClickEvent = lambda e: _edit_perception()

    def _init_layout(self):
        content_geo = self.edit_content.geometry()
        name_geo = self.edit_name.geometry()
        edit_geo = self.edit_edit.geometry()
        width = edit_geo.x() + edit_geo.width() + name_geo.x()
        height = content_geo.height() + content_geo.y() * 2
        self.setFixedSize(width, height)

    def _text_change_call(self):
        self.edit_content.setText(self._repr())
        self._after_changed(self._values)

    @property
    def values(self) -> List:
        return list(self._values)

    @values.setter
    def values(self, newvs):
        self._values = self._validate_list(newvs)
        self._text_change_call()

    def _validate_list(self, vs):
        vs = _to_list(vs)
        result = []
        for i, item in enumerate(vs, start=1):
            try:
                v = self._validate_one(item)
            except ValueError as err:
                msg, *args = err.args
                raise ValueError(f'{msg} on {inflection.ordinalize(i)} item')
            else:
                result.append(v)

        return result

    # noinspection PyMethodMayBeStatic
    def _validate_one(self, v):
        return v

    # noinspection PyMethodMayBeStatic
    def _devalidate_one(self, v) -> str:
        return str(v)

    def _repr(self) -> str:
        return ','.join(map(str, self._values))

    def _after_changed(self, values: List):
        pass

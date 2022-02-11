import os
from typing import List

from PyQt5.Qt import QWidget, QInputDialog

from ..ui import UIFormGenerate
from ..utils import smart_sort


class FormGenerate(QWidget, UIFormGenerate):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)
        self.setFixedSize(self.width(), self.height())
        self._init()

    def _init(self):
        self._init_perception()
        self._init_lost_possibility()

    def _init_perception(self):
        def _edit_perception():
            current_items = self.perceptions
            result_str, result_ok = QInputDialog.getMultiLineText(self, 'Edit Perceptions', 'Update new perceptions:',
                                                                  os.linesep.join(current_items))
            if result_ok:
                items = smart_sort(filter(bool, map(str.strip, result_str.splitlines())))
                self.edit_perception.setText(','.join(items))

        self.button_edit_perception.clicked.connect(_edit_perception)

    def _init_lost_possibility(self):
        def _edit_lost_possibility():
            current_items = self.lost_possibilities
            result_str, result_ok = QInputDialog.getMultiLineText(
                self, 'Edit Lost Possibilities', 'Update new lost_possibilities:', os.linesep.join(current_items))
            if result_ok:
                items = smart_sort(filter(bool, map(str.strip, result_str.splitlines())))
                self.edit_lost_possibility.setText(','.join(items))

        self.button_edit_lost_possibility.clicked.connect(_edit_lost_possibility)

    @property
    def perceptions(self) -> List[str]:
        return smart_sort(filter(bool, map(str.strip, self.edit_perception.text().split(','))))

    @property
    def lost_possibilities(self) -> List[str]:
        return smart_sort(filter(bool, map(str.strip, self.edit_lost_possibility.text().split(','))))

from functools import partial
from typing import Dict, Any, Collection, Optional

from PyQt5.Qt import QWidget, QVBoxLayout, QScrollArea, pyqtSignal


class WidgetEditCollection(QWidget):
    changed = pyqtSignal(QWidget, object)  # only saved changes
    textChanged = pyqtSignal(QWidget, bool, object)  # all the changes

    def __init__(self, parent=None, height=None, width=None, edits: Optional[Collection[QWidget]] = None):
        QWidget.__init__(self, parent=parent)
        main = QVBoxLayout(self)
        self.edits = list(edits or [])
        self._edit_dict = {edit.name: edit for edit in self.edits}

        scroll = QScrollArea()
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        scroll.setWidgetResizable(True)

        layout = QVBoxLayout(content_widget)
        _max_width, _total_height = 0, 0
        for edit in self.edits:
            edit.changed.connect(partial(self._changed_method, edit))
            edit.textChanged.connect(partial(self._text_changed_method, edit))
            layout.addWidget(edit)

            _total_height += edit.geometry().height()
            _max_width = max(_max_width, edit.geometry().width())

        scroll.setFixedHeight(height or _total_height)
        scroll.setFixedWidth(width or _max_width)
        main.addWidget(scroll)

    def __getitem__(self, item):
        return self._edit_dict[item]

    @property
    def value(self) -> Dict[str, Any]:
        return {
            name: edit.value
            for name, edit in self._edit_dict.items()
        }

    def _changed_method(self, widget: QWidget, value):
        self.changed.emit(widget, value)

    def _text_changed_method(self, widget: QWidget, valid: bool, value):
        self.textChanged.emit(widget, valid, value)

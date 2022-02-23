from types import MethodType
from typing import List, Tuple, Optional

from PyQt5.Qt import QDialog, QStandardItem, QStandardItemModel, Qt, QDialogButtonBox

from ..ui import UIDialogMultipleChoice


class DialogMultipleChoice(QDialog, UIDialogMultipleChoice):
    def __init__(self, parent, title, content, selections, check=None):
        QDialog.__init__(self, parent)
        self.title = title
        self.content = content
        self.selections = selections
        self.check = MethodType(check, self) if check else self._always_ok

        self.setupUi(self)
        self.setFixedSize(self.width(), self.height())
        self._init()

    def _init(self):
        self._init_dialog()
        self._init_content()
        self._init_selections()

    def _always_ok(self):
        return True

    def _init_dialog(self):
        self.setWindowTitle(self.title)

    def _init_content(self):
        self.label_content.setWordWrap(True)
        self.label_content.setText(self.content)

        new_height = self.label_content.sizeHint().height()
        hdelta = new_height - self.label_content.height()

        self.label_content.setFixedHeight(new_height)
        self.list_choices.setGeometry(
            self.list_choices.x(), self.list_choices.y() + hdelta,
            self.list_choices.width(), self.list_choices.height(),
        )
        self.button_next.setGeometry(
            self.button_next.x(), self.button_next.y() + hdelta,
            self.button_next.width(), self.button_next.height(),
        )
        self.setFixedHeight(self.height() + hdelta)

    def _init_selections(self):
        model = QStandardItemModel(0, 1)
        for name in self.selections:
            item = QStandardItem(name)
            item.setCheckState(Qt.Unchecked)
            item.setCheckable(True)
            item.setEditable(False)
            model.appendRow(item)

        self.list_choices.setModel(model)

        def _model_changed():
            if self.check():
                self.button_next.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            else:
                self.button_next.setStandardButtons(QDialogButtonBox.Cancel)

        model.dataChanged.connect(_model_changed)
        _model_changed()

    def chosen(self) -> List[str]:
        model: QStandardItemModel = self.list_choices.model()
        result = []
        for i in range(model.rowCount()):
            item: QStandardItem = model.item(i, 0)
            if item.checkState() == Qt.Checked:
                result.append(item.text())

        return result

    @classmethod
    def get_chosen(cls, parent, title, content, selections, check=None) -> Tuple[Optional[List[str]], bool]:
        dialog = cls(parent, title, content, selections, check)
        if dialog.exec() == QDialog.Accepted:
            return dialog.chosen(), True
        else:
            return None, False

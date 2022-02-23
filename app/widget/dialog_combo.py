from PyQt5.Qt import QDialog

from ..ui import UiDialogCombo


class DialogCombo(QDialog, UiDialogCombo):
    def __init__(self, parent, title, content, selections):
        QDialog.__init__(self, parent)
        self.title = title
        self.content = content
        self.selections = selections

        self.setupUi(self)
        self.setFixedSize(self.width(), self.height())
        self._init()

    def _init(self):
        self._init_dialog()
        self._init_content()
        self._init_selections()

    def _init_dialog(self):
        self.setWindowTitle(self.title)

    def _init_content(self):
        self.label_content.setWordWrap(True)
        self.label_content.setText(self.content)

        new_height = self.label_content.sizeHint().height()
        hdelta = new_height - self.label_content.height()

        self.label_content.setFixedHeight(new_height)
        self.combo_selection.setGeometry(
            self.combo_selection.x(), self.combo_selection.y() + hdelta,
            self.combo_selection.width(), self.combo_selection.height(),
        )
        self.button_next.setGeometry(
            self.button_next.x(), self.button_next.y() + hdelta,
            self.button_next.width(), self.button_next.height(),
        )
        self.setFixedHeight(self.height() + hdelta)

    def _init_selections(self):
        self.combo_selection.clear()
        for item in self.selections:
            self.combo_selection.addItem(item)

        self.combo_selection.setCurrentIndex(0)

    @property
    def selected(self) -> str:
        index = self.combo_selection.currentIndex()
        return self.combo_selection.itemText(index)

    @classmethod
    def show_selection(cls, parent, title, content, selections):
        dialog = cls(parent, title, content, selections)
        if dialog.exec() == QDialog.Accepted:
            return dialog.selected, True
        else:
            return None, False

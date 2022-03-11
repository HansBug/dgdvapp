from PyQt5.Qt import QDialog

from ..config.meta import __TITLE__, __VERSION__, __AUTHOR__, __AUTHOR_EMAIL__
from ..ui import UIDialogConfig


class DialogConfig(QDialog, UIDialogConfig):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setFixedSize(self.width(), self.height())
        self._init()

    def _init(self):
        self._init_ok()
        self._init_information()

    def _init_ok(self):
        self.button_dialog.clicked.connect(self._event_close)

    def _init_information(self):
        original_width = max(self.label_title.width(), self.label_author.width())
        original_win_width = self.width()

        self.label_title.setText(
            '{title}, version {version}.'.format(title=__TITLE__.capitalize(), version=__VERSION__))
        self.label_author.setText('Developed by {author}, {email}.'.format(author=__AUTHOR__, email=__AUTHOR_EMAIL__))

        new_width = max(self.label_title.sizeHint().width(), self.label_author.sizeHint().width())
        self.label_title.setFixedWidth(new_width)
        self.label_title.setFixedHeight(self.label_title.sizeHint().height())
        self.label_author.setFixedWidth(new_width)
        self.label_author.setFixedHeight(self.label_author.sizeHint().height())
        self.button_dialog.setGeometry(
            self.button_dialog.x() + (new_width - original_width), self.button_dialog.y(),
            self.button_dialog.width(), self.button_dialog.height(),
        )
        self.setFixedWidth(original_win_width + (new_width - original_width))

    def _event_close(self, btn):
        self.close()

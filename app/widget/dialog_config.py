from PyQt5.Qt import QDialog

from ..config.meta import __TITLE__, __VERSION__, __AUTHOR__, __AUTHOR_EMAIL__
from ..ui import UIDialogConfig


class DialogConfig(QDialog, UIDialogConfig):
    def __init__(self):
        QDialog.__init__(self)
        self.setupUi(self)
        self.setFixedSize(self.width(), self.height())
        self._init()

    def _init(self):
        self._init_ok()
        self._init_information()

    def _init_ok(self):
        self.button_dialog.clicked.connect(self._event_close)

    def _init_information(self):
        self.label_title.setText(
            '{title}, version {version}.'.format(title=__TITLE__.capitalize(), version=__VERSION__))
        self.label_author.setText('Developed by {author}, {email}.'.format(author=__AUTHOR__, email=__AUTHOR_EMAIL__))

    def _event_close(self, btn):
        self.close()

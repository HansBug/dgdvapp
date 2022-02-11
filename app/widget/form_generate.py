from PyQt5.Qt import QWidget

from ..ui import UIFormGenerate


class FormGenerate(QWidget, UIFormGenerate):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)
        self.setFixedSize(self.width(), self.height())

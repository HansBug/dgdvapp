import math

from PyQt5.Qt import QWidget, pyqtSignal
from hbutils.color import Color

from ..ui import UILabeledEdit


class WidgetLabeledEdit(QWidget, UILabeledEdit):
    changed = pyqtSignal(object)  # only saved changes
    textChanged = pyqtSignal(bool, object)  # all the changes

    def __init__(self, parent, label, init_value=None, placeholder=None):
        QWidget.__init__(self, parent)
        self.label = label
        self.init_value = init_value
        self.placeholder = placeholder

        self.setupUi(self)
        self._init()

    def _init(self):
        self._init_label()
        self._init_content()
        self._init_layout()

    def _init_label(self):
        self.edit_name.setText(self.label)

    def _init_content(self):
        if self.init_value is not None:
            self.edit_content.setText(str(self.init_value))
        if self.placeholder:
            self.edit_content.setPlaceholderText(self.placeholder)

        self._text_change_call()
        self.edit_content.textChanged.connect(self._text_change_call)

    def _init_layout(self):
        content_geo = self.edit_content.geometry()
        name_geo = self.edit_name.geometry()
        width = content_geo.x() + content_geo.width() + name_geo.x()
        height = content_geo.height() + content_geo.y() * 2
        self.setFixedSize(width, height)

    def _text_change_call(self):
        try:
            value = self._validate(self.edit_content.text())
        except ValueError as err:
            valid, value, (msg, *_) = False, None, err.args
        else:
            valid, msg = True, None

        color = Color('black' if valid else 'red')
        self.edit_name.setStyleSheet(f"QLabel {{ color: {color}; }} ")
        self.edit_content.setStyleSheet(f"QLineEdit {{ color: {color}; }}")
        if not valid:
            self.edit_content.setToolTip(f'Validation Failed: {msg}' if not valid else '')
        else:
            self.edit_content.setToolTip(f'{self.label}: {value!r}')

        self.textChanged.emit(valid, value if valid else self.edit_content.text())
        if valid:
            self.changed.emit(value)

    @property
    def name(self) -> str:
        return self.label

    @property
    def value(self):
        return self._validate(self.edit_content.text())

    @value.setter
    def value(self, newv):
        self.edit_content.setText(str(self._validate(newv)))
        self._text_change_call()

    @property
    def valid(self) -> bool:
        try:
            self._validate(self.edit_content.text())
        except ValueError:
            return False
        else:
            return True

    # noinspection PyMethodMayBeStatic
    def _validate(self, v):
        return v

    @classmethod
    def parse_json(cls, d: dict, parent=None) -> 'WidgetLabeledEdit':
        name = d['name']
        assert not d.get('multiple', None), f'Multiple not supported in {cls!r}.'
        placeholder = d.get('placeholder', None)

        min_ = d.get('min', -math.inf)
        max_ = d.get('max', +math.inf)
        type_ = d.get('type')
        if isinstance(type_, str):
            type_ = eval(type_)

        init_value = d.get('init')

        class _MyEdit(WidgetLabeledEdit):
            def _validate(self, v):
                if type_ is not None:
                    try:
                        v = type_(v)
                    except (TypeError, ValueError) as err:
                        raise ValueError(*err.args).with_traceback(err.__traceback__)

                if min_ <= v <= max_:
                    return v
                else:
                    raise ValueError(f'Value in [{min_!r}, {max_!r}] expected, but {v!r} found.')

        return _MyEdit(parent, name, init_value, placeholder)

import pytest
from PyQt5.Qt import Qt

from app.widget import AppMainWindow


@pytest.mark.unittest
class TestMainWindow:
    def test_common(self, qtbot):
        window = AppMainWindow()
        qtbot.addWidget(window)

        window.text_first.setPlainText('2')
        window.text_second.setPlainText('233')

        qtbot.mouseClick(window.button_plus, Qt.MouseButton.LeftButton)
        assert window.text_result.toPlainText() == '235'

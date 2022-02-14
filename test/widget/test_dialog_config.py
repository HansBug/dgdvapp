import pytest

from app.config.meta import __TITLE__, __VERSION__, __AUTHOR__, __AUTHOR_EMAIL__
from app.widget import DialogConfig


@pytest.mark.unittest
class TestDialogConfig:
    def test_common(self, qtbot):
        dc = DialogConfig(None)

        qtbot.addWidget(dc)

        title_info_str = dc.label_title.text().lower()
        assert __TITLE__.lower() in title_info_str
        assert __VERSION__.lower() in title_info_str

        author_info_str = dc.label_author.text().lower()
        assert __AUTHOR__.lower() in author_info_str
        assert __AUTHOR_EMAIL__.lower() in author_info_str

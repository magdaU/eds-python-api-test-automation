import pytest

from scripts.inject_report_notes import TAG, inject
from tests.support.allure_labels import labels

pytestmark = labels("Test support", "Report notes")

INDEX = "<html><body><div id='content'></div></body></html>"


def test_givenGeneratedReport_whenInjectingTwice_thenScriptIsCopiedAndLoadedOnce(tmp_path):
    # arrange
    (tmp_path / "index.html").write_text(INDEX, encoding="utf-8")

    # act
    inject(tmp_path)
    inject(tmp_path)

    # assert
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert html.count(TAG) == 1
    assert html.index(TAG) < html.index("</body>")
    assert "Categories" in (tmp_path / "report-notes.js").read_text(encoding="utf-8")


def test_givenReportWithoutBodyTag_whenInjecting_thenErrorIsRaisedAndNothingIsWritten(tmp_path):
    # arrange
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")

    # act / assert
    with pytest.raises(ValueError, match="no </body>"):
        inject(tmp_path)
    assert not (tmp_path / "report-notes.js").exists()

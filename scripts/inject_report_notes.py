"""Add allure/report-notes.js to a generated Allure report (see that file for what it does).

Usage (from the repository root): python scripts/inject_report_notes.py allure-report
"""

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "allure" / "report-notes.js"
TAG = '<script src="report-notes.js"></script>'


def inject(report_dir: Path) -> None:
    """Copy the script into the report and load it from index.html; running it twice changes nothing more."""
    index = report_dir / "index.html"
    html = index.read_text(encoding="utf-8")
    if "</body>" not in html:
        raise ValueError(f"{index} has no </body>; the report layout has changed and the note cannot be added")
    shutil.copyfile(SCRIPT, report_dir / "report-notes.js")
    if TAG not in html:
        index.write_text(html.replace("</body>", f"    {TAG}\n</body>", 1), encoding="utf-8")


if __name__ == "__main__":
    inject(Path(sys.argv[1]))
    print(f"Added report-notes.js to {sys.argv[1]}")

"""Print a one-line summary of a JUnit XML report, for the GitHub job summary.

Usage: python scripts/summarise_junit.py FILE

A missing or unreadable report is printed as such instead of failing, because the
summary also runs after a failed test run.
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def _has(case: ET.Element, *tags: str) -> bool:
    return any(case.find(tag) is not None for tag in tags)


def summarise(path: Path) -> str:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as error:
        return f"**Live tests:** no readable JUnit report ({error})"

    cases = list(root.iter("testcase"))
    errors = [case for case in cases if _has(case, "error")]
    failures = [case for case in cases if _has(case, "failure") and not _has(case, "error")]
    skipped = [case for case in cases if _has(case, "skipped")]

    line = (
        f"**Live tests:** {len(cases)} tests, {len(failures)} failed, "
        f"{len(errors)} errors, {len(skipped)} skipped"
    )
    broken = failures + errors
    if broken:
        names = ", ".join(
            f"`{case.get('classname', '')}::{case.get('name', '')}`" for case in broken
        )
        line += f"\n\nFailed: {names}"
    return line


if __name__ == "__main__":
    print(summarise(Path(sys.argv[1])))

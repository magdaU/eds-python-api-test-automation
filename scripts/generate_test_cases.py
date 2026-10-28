"""Generate docs/test-cases.md from the pytest suite.

Test names follow `givenX_whenY_thenZ`, so each one reads as a test case: precondition, action, expected result.
Counts and execution mode come from pytest's own collection; labels come from the test modules' Allure markers.

Usage (from the repository root): python scripts/generate_test_cases.py
"""

import ast
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "test-cases.md"

# module -> (test level, environment / test double, main test design technique); a new module must be classified here
MODULES = {
    "test_allure_environment": ("Component", "none", "Equivalence partitioning"),
    "test_boundary_values": ("Component", "mocked HTTP", "Boundary value analysis"),
    "test_dataset_contract": ("Component", "mocked HTTP, local HTTP server", "Contract and request verification"),
    "test_eds_client": ("Component", "none", "Configuration checks"),
    "test_filter_encoding": ("Component", "mocked HTTP", "Equivalence partitioning"),
    "test_live_edge_cases": ("System", "public EDS API", "Error guessing, negative testing"),
    "test_live_smoke": ("System", "public EDS API", "Smoke testing"),
    "test_logging": ("Integration", "local HTTP server", "Negative testing, log assertions"),
    "test_models": ("Component", "none", "Equivalence partitioning, negative testing"),
    "test_negative_scenarios": ("Component", "mocked HTTP, unused local port", "Negative testing"),
    "test_news_api": ("Component", "mocked HTTP", "Request verification, schema validation"),
    "test_pagination": ("Component", "mocked HTTP", "Request verification"),
    "test_parameter_combinations": ("Component", "mocked HTTP", "Decision table"),
    "test_properties": ("Component", "mocked HTTP", "Property-based testing"),
    "test_retry_behavior": ("Integration", "local HTTP server", "State-based, negative testing"),
    "test_retry_config": ("Component", "none", "Configuration checks"),
    "test_schema_validation": (
        "Component",
        "JSON Schema; two tests use the public EDS API",
        "Equivalence partitioning, negative testing",
    ),
    "test_support_paths": ("Component", "none", "Regression test"),
    "test_url_building": ("Component", "none", "Equivalence partitioning"),
}
LEVELS = ["Component", "Integration", "System"]

WORDS = {
    "co2 emis": "CO2Emis",
    "elspotprices": "Elspotprices",
    "json": "JSON",
    "url": "URL",
    "http": "HTTP",
    "api": "API",
    "eds": "EDS",
    "ci": "CI",
    "ok": "OK",
}


def collect(*pytest_args: str) -> Counter[tuple[str, str]]:
    """Variants per (module, test function), from `pytest --collect-only`."""
    command = [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", *pytest_args]
    output = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True).stdout
    counts: Counter[tuple[str, str]] = Counter()
    for line in output.splitlines():
        match = re.match(r"tests/(test_\w+)\.py::(test_\w+)", line)
        if match:
            counts[match.groups()] += 1
    return counts


def label_calls(node: ast.AST) -> list[tuple[str, list[str]]]:
    """(function name, string arguments) of every `labels(...)`, `allure.epic(...)` and `allure.feature(...)` call below node."""
    found = []
    for call in ast.walk(node):
        if isinstance(call, ast.Call):
            name = call.func.attr if isinstance(call.func, ast.Attribute) else getattr(call.func, "id", "")
            if name in {"labels", "epic", "feature"}:
                found.append((name, [arg.value for arg in call.args if isinstance(arg, ast.Constant)]))
    return found


def read_labels(module: str) -> dict[str, tuple[str, str]]:
    """Allure (epic, feature) per test function: from the module's `pytestmark`, a function's own `allure.feature`."""
    tree = ast.parse((ROOT / "tests" / f"{module}.py").read_text(encoding="utf-8"))
    epic = feature = ""
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(target, "id", "") == "pytestmark" for target in node.targets):
            for name, args in label_calls(node.value):
                if name == "labels":
                    epic, feature = args
                elif name == "epic":
                    epic = args[0]
    per_test = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            own = [args[0] for decorator in node.decorator_list for name, args in label_calls(decorator) if name == "feature"]
            per_test[node.name] = (epic, own[0] if own else feature)
    return per_test


def humanize(part: str) -> str:
    words = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", part).lower()
    for source, target in WORDS.items():
        words = re.sub(rf"\b{source}\b", target, words)
    return words[:1].upper() + words[1:]


def split_name(name: str) -> tuple[str, str, str]:
    """`test_givenX_whenY_thenZ` -> (precondition, action, expected result)."""
    match = re.fullmatch(r"test_(?:given(\w+?)_)?when(\w+?)_then(\w+)", name)
    if not match:
        raise ValueError(f"{name} does not follow givenX_whenY_thenZ / whenY_thenZ")
    given, when, then = match.groups()
    return humanize(given) if given else "-", humanize(when), humanize(then)


def render() -> str:
    everything = collect()
    live = collect("-m", "live")
    unclassified = {module for module, _ in everything} - MODULES.keys()
    if unclassified:
        raise SystemExit(f"Classify new test modules in MODULES: {sorted(unclassified)}")

    sections = []
    executed: Counter[tuple[str, str]] = Counter()  # (effective level, mode) -> executed test cases
    functions = 0
    for module in sorted(MODULES):
        per_test = read_labels(module)
        names = [name for (mod, name) in everything if mod == module]
        level, environment, technique = MODULES[module]
        epic = per_test[names[0]][0]
        features = {per_test[name][1] for name in names}
        feature_column = len(features) > 1
        lines = [
            f"### {epic} ({module})" if feature_column else f"### {epic}: {next(iter(features))}",
            "",
            f"Source: [`tests/{module}.py`](../tests/{module}.py) | Level: {level} | Environment: {environment} "
            f"| Technique: {technique}",
            "",
            "| ID |"
            + (" Feature |" if feature_column else "")
            + " Precondition (given) | Action (when) | Expected result (then) "
            "| Variants | Mode |",
            "| --- |" + (" --- |" if feature_column else "") + " --- | --- | --- | ---: | --- |",
        ]
        for name in names:
            functions += 1
            given, when, then = split_name(name)
            mode = "Live" if (module, name) in live else "Offline"
            executed["System" if mode == "Live" else level, mode] += everything[(module, name)]
            feature_cell = f" {per_test[name][1]} |" if feature_column else ""
            lines.append(
                f"| TC-{functions:03d} |{feature_cell} {given} | {when} | {then} | {everything[(module, name)]} | {mode} |"
            )
        sections.append("\n".join(lines))

    summary = ["| Test level | Offline | Live | Total |", "| --- | ---: | ---: | ---: |"]
    for level in LEVELS:
        offline, live_count = executed[level, "Offline"], executed[level, "Live"]
        summary.append(f"| {level} | {offline} | {live_count} | {offline + live_count} |")
    all_offline = sum(count for (_, mode), count in executed.items() if mode == "Offline")
    all_live = sum(count for (_, mode), count in executed.items() if mode == "Live")
    summary.append(f"| **Total** | **{all_offline}** | **{all_live}** | **{all_offline + all_live}** |")

    header = (
        "# Test cases\n\n"
        "> Generated by `scripts/generate_test_cases.py` from the pytest suite - do not edit by hand.\n"
        "> Regenerate after adding, renaming or removing tests. IDs are sequential and are **not stable** between\n"
        "> regenerations, so refer to a test by its module and name.\n\n"
        f"{functions} test functions expand to {all_offline + all_live} executed test cases "
        "(*Variants* counts parametrized runs). Each test name reads `given<precondition>_when<action>_then<expected result>`; "
        "the columns below are that name, split. Tests that call the public EDS API count as *System* level whichever "
        "module they live in. See the [test strategy](test-strategy.md) for how the levels are used.\n\n"
        "## Summary by test level\n\n" + "\n".join(summary) + "\n\n## Test cases\n"
    )
    return header + "\n" + "\n\n".join(sections) + "\n"


if __name__ == "__main__":
    OUTPUT.write_text(render(), encoding="utf-8", newline="\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")

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
    "test_allure_categories": ("Component", "none", "Equivalence partitioning, configuration checks"),
    "test_allure_environment": ("Component", "none", "Equivalence partitioning"),
    "test_boundary_values": ("Component", "mocked HTTP", "Boundary value analysis"),
    "test_dataset_queries": ("Component", "mocked HTTP", "Executable specification (Gherkin)"),
    "test_dataset_contract": ("Component", "mocked HTTP, local HTTP server", "Contract and request verification"),
    "test_eds_client": ("Component", "none", "Configuration checks"),
    "test_filter_encoding": ("Component", "mocked HTTP", "Equivalence partitioning"),
    "test_live_data_quality": ("System", "public EDS API", "Data quality checks"),
    "test_live_edge_cases": ("System", "public EDS API", "Error guessing, negative testing"),
    "test_openapi_drift": ("System", "public EDS API", "Contract testing, regression test"),
    "test_live_smoke": ("System", "public EDS API", "Smoke testing"),
    "test_logging": ("Integration", "local HTTP server", "Negative testing, log assertions"),
    "test_models": ("Component", "none", "Equivalence partitioning, negative testing"),
    "test_news": ("Component", "mocked HTTP", "Executable specification (Gherkin)"),
    "test_news_api": ("Component", "mocked HTTP", "Request verification, schema validation"),
    "test_parameter_combinations": ("Component", "mocked HTTP", "Decision table"),
    "test_properties": ("Component", "mocked HTTP", "Property-based testing"),
    "test_resilience": ("Integration", "local HTTP server", "Executable specification (Gherkin)"),
    "test_retry_after_cap": ("Integration", "local HTTP server", "Boundary value analysis, state-based testing"),
    "test_retry_behavior": ("Integration", "local HTTP server", "State-based, negative testing"),
    "test_retry_config": ("Component", "none", "Configuration checks"),
    "test_schema_validation": (
        "Component",
        "JSON Schema; two tests use the public EDS API",
        "Equivalence partitioning, negative testing",
    ),
    "test_typed_records": ("Component", "mocked HTTP", "Contract and request verification"),
    "test_url_building": ("Component", "none", "Equivalence partitioning"),
}
LEVELS = ["Component", "Integration", "System"]

# BDD modules: test module -> Gherkin feature file in tests/bdd/features (their rows come from the scenarios)
BDD_FEATURES = {"test_dataset_queries": "dataset_queries", "test_resilience": "resilience", "test_news": "news"}
FEATURES_DIR = ROOT / "tests" / "bdd" / "features"

WORDS = {
    "co2 emis": "CO2Emis",
    "dayaheadprices": "DayAheadPrices",
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
        match = re.match(r"tests/(?:bdd/)?(test_\w+)\.py::(test_\w+)", line)
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


def module_path(module: str) -> Path:
    return ROOT / "tests" / ("bdd" if module in BDD_FEATURES else "") / f"{module}.py"


def read_labels(module: str) -> tuple[dict[str, tuple[str, str]], tuple[str, str]]:
    """Allure (epic, feature) per test function and the module default, from `pytestmark` and `allure.feature`."""
    tree = ast.parse(module_path(module).read_text(encoding="utf-8"))
    epic = feature = ""
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(target, "id", "") == "pytestmark" for target in node.targets):
            for name, args in label_calls(node.value):
                if name == "labels":
                    epic, feature = args[:2]  # the optional third argument is the severity
                elif name == "epic":
                    epic = args[0]
    per_test = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            own = [args[0] for decorator in node.decorator_list for name, args in label_calls(decorator) if name == "feature"]
            per_test[node.name] = (epic, own[0] if own else feature)
    return per_test, (epic, feature)


def read_scenarios(feature: str) -> list[dict]:
    """Scenarios of a `.feature` file: title, steps by Given/When/Then and the number of runs (example rows, or 1)."""
    scenarios: list[dict] = []
    current: dict | None = None
    phase = ""
    in_examples = header_seen = False
    for raw in (FEATURES_DIR / f"{feature}.feature").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith(("Scenario Outline:", "Scenario:")):
            current = {"title": line.split(":", 1)[1].strip(), "Given": [], "When": [], "Then": [], "runs": 1}
            scenarios.append(current)
            in_examples = header_seen = False
            phase = ""
        elif line.startswith("Examples:"):
            in_examples, header_seen = True, False
            current["runs"] = 0
        elif in_examples and line.startswith("|"):
            if header_seen:
                current["runs"] += 1
            header_seen = True
        elif current is not None and line.split(" ", 1)[0] in {"Given", "When", "Then", "And", "But"}:
            keyword, text = line.split(" ", 1)
            phase = keyword if keyword in {"Given", "When", "Then"} else phase
            current[phase].append(text)
    return scenarios


def cell(steps: list[str]) -> str:
    return "; ".join(steps).replace("<", "&lt;").replace(">", "&gt;") or "-"


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
        per_test, default_labels = read_labels(module)
        names = [name for (mod, name) in everything if mod == module]
        level, environment, technique = MODULES[module]
        epic = default_labels[0] if module in BDD_FEATURES else per_test[names[0]][0]
        features = {default_labels[1]} if module in BDD_FEATURES else {per_test[name][1] for name in names}
        feature_column = len(features) > 1
        source = (
            f"[`tests/bdd/features/{BDD_FEATURES[module]}.feature`](../tests/bdd/features/{BDD_FEATURES[module]}.feature)"
            if module in BDD_FEATURES
            else f"[`tests/{module}.py`](../tests/{module}.py)"
        )
        lines = [
            f"### {epic} ({module})" if feature_column else f"### {epic}: {next(iter(features))}",
            "",
            f"Source: {source} | Level: {level} | Environment: {environment} | Technique: {technique}",
            "",
            *(
                ["| ID | Scenario | Given | When | Then | Variants | Mode |", "| --- | --- | --- | --- | --- | ---: | --- |"]
                if module in BDD_FEATURES
                else [
                    "| ID |"
                    + (" Feature |" if feature_column else "")
                    + " Precondition (given) | Action (when) | Expected result (then) | Variants | Mode |",
                    "| --- |" + (" --- |" if feature_column else "") + " --- | --- | --- | ---: | --- |",
                ]
            ),
        ]
        if module in BDD_FEATURES:
            scenarios = read_scenarios(BDD_FEATURES[module])
            collected = sum(everything[(module, name)] for name in names)
            if sum(scenario["runs"] for scenario in scenarios) != collected or any((module, n) in live for n in names):
                raise SystemExit(f"{module}: the feature file and the collected tests disagree (or a scenario is live)")
            for scenario in scenarios:
                functions += 1
                executed[level, "Offline"] += scenario["runs"]
                lines.append(
                    f"| TC-{functions:03d} | {scenario['title']} | {cell(scenario['Given'])} | {cell(scenario['When'])} "
                    f"| {cell(scenario['Then'])} | {scenario['runs']} | Offline |"
                )
            sections.append("\n".join(lines))
            continue
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

"""Check that the offline tests notice deliberate one-line breakages of the client ("mutants").

Each mutation is applied to the client source, the offline suite runs until its first failure, and the file is restored.
A mutant that no test notices ("survived") means a behaviour of the client is not protected by an assertion.
The unmutated suite must pass first, otherwise every mutant would look detected.

Usage (from the repository root, on a clean working tree): python scripts/mutation_check.py [--report FILE] [name ...]
--report writes the result of every mutation as a Markdown table (the workflow shows it in the job summary).
Exit code 1 when a mutant survives or a mutation no longer matches the source.
"""

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTEST = [
    sys.executable,
    "-m",
    "pytest",
    "-x",
    "-q",
    "-p",
    "no:cacheprovider",
    "-p",
    "no:randomly",  # a fixed order, so a mutant is judged the same way on every run
    "-o",
    "log_cli=false",
    "-m",
    "not live",
]
EDS_CLIENT = "client/eds_client.py"
DATASET_API = "client/dataset_api.py"
RETRY = "client/retry.py"
NEWS_API = "client/news_api.py"


@dataclass(frozen=True)
class Mutation:
    name: str
    path: str
    old: str  # one line of the source that occurs exactly once in `path`
    new: str


MUTATIONS = [
    Mutation("429-not-retried", EDS_CLIENT, "frozenset({429, 500, 502, 503, 504})", "frozenset({500, 502, 503, 504})"),
    Mutation(
        "client-errors-retried",
        EDS_CLIENT,
        "frozenset({429, 500, 502, 503, 504})",
        "frozenset({400, 401, 404, 429, 500, 502, 503, 504})",
    ),
    Mutation(
        "timeout-not-passed",
        EDS_CLIENT,
        "self.session.get(url, params=params, timeout=self.timeout)",
        "self.session.get(url, params=params)",
    ),
    Mutation("negative-limit-allowed", EDS_CLIENT, "if limit is not None and limit < 0:", "if False:"),
    Mutation("limit-zero-ignored", EDS_CLIENT, "if limit is not None:", "if limit:"),
    Mutation("offset-zero-ignored", EDS_CLIENT, "if offset is not None:", "if offset:"),
    Mutation("limit-not-sent", EDS_CLIENT, 'params["limit"] = limit', "pass"),
    Mutation("offset-not-sent", EDS_CLIENT, 'params["offset"] = offset', "pass"),
    Mutation("sort-not-sent", EDS_CLIENT, 'params["sort"] = sort', "pass"),
    Mutation("filter-not-sent", EDS_CLIENT, 'params["filter"] = self._encode_filters(filters)', "pass"),
    Mutation("filter-json-with-spaces", EDS_CLIENT, 'separators=(",", ":")', 'separators=(", ", ": ")'),
    Mutation("dataset-name-not-encoded", EDS_CLIENT, 'return quote(value, safe="")', "return value"),
    Mutation("dataset-path-wrong", EDS_CLIENT, 'f"{self.base_url}/dataset/{', 'f"{self.base_url}/datasets/{'),
    Mutation("metadata-path-wrong", EDS_CLIENT, 'f"{self.base_url}/meta/dataset/{', 'f"{self.base_url}/meta/datasets/{'),
    Mutation("retry-after-limit-600", EDS_CLIENT, "DEFAULT_MAX_RETRY_AFTER = 60.0", "DEFAULT_MAX_RETRY_AFTER = 600.0"),
    Mutation("retry-after-limit-exclusive", RETRY, "retry_after > self.max_retry_after", "retry_after >= self.max_retry_after"),
    Mutation(
        "retry-after-limit-disabled",
        RETRY,
        "if retry_after and self.max_retry_after is not None and retry_after > self.max_retry_after:",
        "if False:",
    ),
    Mutation(
        "retry-after-limit-lost-between-attempts",
        RETRY,
        "retry.max_retry_after = self.max_retry_after",
        "retry.max_retry_after = None",
    ),
    Mutation("retry-after-limit-not-passed", EDS_CLIENT, "max_retry_after=config.max_retry_after,", "max_retry_after=None,"),
    Mutation(
        "long-wait-error-not-a-retry-error",
        RETRY,
        "class RetryAfterTooLongError(requests.exceptions.RetryError):",
        "class RetryAfterTooLongError(Exception):",
    ),
    Mutation("news-category-lowercased", NEWS_API, '{"category": category}', '{"category": category.lower()}'),
    Mutation("news-path-lowercase", EDS_CLIENT, 'f"{self.base_url}/News"', 'f"{self.base_url}/news"'),
    Mutation("news-path-slashes-kept", EDS_CLIENT, 'path.strip("/")', "path"),
    Mutation("archived-date-not-sent", NEWS_API, '{"date": date} if date is not None else None', "None"),
    Mutation("category-not-sent", NEWS_API, '{"category": category} if category is not None else None', "None"),
    Mutation("base-url-slash-kept", EDS_CLIENT, 'self.base_url = base_url.rstrip("/")', "self.base_url = base_url"),
    Mutation(
        "dataset-override-applies-to-all",
        EDS_CLIENT,
        "self._mount_retry(self.dataset_url(dataset), override)",
        'self._mount_retry("https://", override)',
    ),
    Mutation("backoff-jitter-ignored", EDS_CLIENT, "backoff_jitter=config.backoff_jitter,", "backoff_jitter=0.0,"),
    Mutation("max-retries-ignored", EDS_CLIENT, "total=config.max_retries,", "total=3,"),
    Mutation("model-co2-area-any-text", "models/co2emis.py", 'PriceArea: Literal["DK1", "DK2"]', "PriceArea: str"),
    Mutation("model-co2-time-as-text", "models/co2emis.py", "Minutes5UTC: datetime", "Minutes5UTC: str"),
    Mutation(
        "model-price-optional", "models/dayaheadprices.py", "DayAheadPriceDKK: float", "DayAheadPriceDKK: float | None = None"
    ),
    Mutation("model-time-required", "models/dayaheadprices.py", "TimeUTC: datetime | None = None", "TimeUTC: datetime"),
    Mutation(
        "schema-co2-envelope-optional",
        "schemas/co2emis_schema.json",
        '"required": ["records", "total", "limit", "dataset"]',
        '"required": ["records", "total"]',
    ),
    Mutation(
        "schema-price-optional",
        "schemas/dayaheadprices_schema.json",
        '"required": ["PriceArea", "DayAheadPriceDKK"]',
        '"required": ["PriceArea"]',
    ),
    Mutation("schema-emission-any-type", "schemas/co2emis_schema.json", '"CO2Emission": {"type": "number"}', '"CO2Emission": {}'),
    Mutation(
        "records-not-parsed",
        DATASET_API,
        "return parse_records(response.json(), self.model)",
        'return response.json()["records"]',
    ),
    Mutation("records-error-status-ignored", DATASET_API, "response.raise_for_status()", "pass"),
    Mutation(
        "records-query-dropped",
        DATASET_API,
        "response = self.get(limit=limit, offset=offset, sort=sort, filters=filters)",
        "response = self.get()",
    ),
    Mutation("records-model-check-removed", DATASET_API, "if self.model is None:", "if False:"),
]


def run_suite() -> int:
    return subprocess.run(PYTEST, cwd=ROOT, capture_output=True, check=False).returncode


def run_mutation(mutation: Mutation) -> str:
    path = ROOT / mutation.path
    original = path.read_bytes()
    source = original.decode("utf-8")
    if source.count(mutation.old) != 1:
        return "STALE"  # the source changed; the mutation has to be updated
    path.write_bytes(source.replace(mutation.old, mutation.new).encode("utf-8"))
    try:
        returncode = run_suite()
    finally:
        path.write_bytes(original)
    return {0: "survived", 1: "killed"}.get(returncode, "INVALID")  # anything else: the mutant did not even load


def is_problem(outcome: str) -> bool:
    return outcome != "killed"


def write_report(path: Path, results: list[tuple[Mutation, str, float]]) -> None:
    survivors = [mutation.name for mutation, outcome, _ in results if is_problem(outcome)]
    verdict = (
        f"**Not killed: {', '.join(survivors)}.** A behaviour of the client has no assertion."
        if survivors
        else "Every change was noticed."
    )
    lines = [
        "## Mutation checks",
        "",
        f"{len(results) - len(survivors)} of {len(results)} mutations killed. {verdict}",
        "",
        "| Result | Mutation | File | Change | Seconds |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for mutation, outcome, seconds in results:
        change = f"`{mutation.old.strip()}` → `{mutation.new.strip()}`".replace("|", "\\|")
        lines.append(f"| {outcome.upper()} | {mutation.name} | `{mutation.path}` | {change} | {seconds:.0f} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(selected: list[str], report: Path | None = None) -> int:
    mutations = [mutation for mutation in MUTATIONS if not selected or mutation.name in selected]
    if selected and len(mutations) != len(selected):
        print(f"Unknown mutation among: {', '.join(selected)}")
        return 2
    print("Baseline: unmutated offline suite ...", flush=True)
    if run_suite() != 0:
        print("The unmutated suite does not pass, so mutants cannot be judged. Fix it first.")
        return 2

    problems = []
    results = []
    for mutation in mutations:
        started = time.perf_counter()
        outcome = run_mutation(mutation)
        seconds = time.perf_counter() - started
        results.append((mutation, outcome, seconds))
        flag = "  <-- PROBLEM" if is_problem(outcome) else ""
        print(f"{outcome:9} {mutation.name} ({seconds:.0f} s){flag}", flush=True)
        if flag:
            problems.append(mutation.name)
    if report:
        write_report(report, results)

    print(f"\n{len(mutations) - len(problems)} of {len(mutations)} mutations killed; problems: {', '.join(problems) or 'none'}")
    return 1 if problems else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check that the offline tests notice deliberate breakages of the client.")
    parser.add_argument("names", nargs="*", help="run only these mutations")
    parser.add_argument("--report", type=Path, help="write the results as a Markdown table to this file")
    arguments = parser.parse_args()
    sys.exit(main(arguments.names, arguments.report))

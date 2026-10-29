"""Check that the offline tests notice deliberate one-line breakages of the client ("mutants").

Each mutation is applied to the client source, the offline suite runs until its first failure, and the file is restored.
A mutant that no test notices ("survived") means a behaviour of the client is not protected by an assertion.
The unmutated suite must pass first, otherwise every mutant would look detected.

Usage (from the repository root, on a clean working tree): python scripts/mutation_check.py [name ...]
Exit code 1 when a detectable mutant survives or a mutation no longer matches the source.
"""

import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The catalogue test reads the client source, so it fails for every mutant; it must not count as a detection.
PYTEST = [
    sys.executable,
    "-m",
    "pytest",
    "-x",
    "-q",
    "-p",
    "no:cacheprovider",
    "-o",
    "log_cli=false",
    "-m",
    "not live",
    "--ignore=tests/test_mutation_catalogue.py",
]
EDS_CLIENT = "client/eds_client.py"
RETRY = "client/retry.py"
NEWS_API = "client/news_api.py"


@dataclass(frozen=True)
class Mutation:
    name: str
    path: str
    old: str  # one line of the source that occurs exactly once in `path`
    new: str
    equivalent: bool = False  # behaves the same through the public interface, so surviving is expected


MUTATIONS = [
    Mutation("429-not-retried", EDS_CLIENT, "frozenset({429, 500, 502, 503, 504})", "frozenset({500, 502, 503, 504})"),
    Mutation(
        "client-errors-retried",
        EDS_CLIENT,
        "frozenset({429, 500, 502, 503, 504})",
        "frozenset({400, 404, 429, 500, 502, 503, 504})",
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
    # the client only ever sends GET, so retrying every method cannot be seen from outside
    Mutation("all-methods-retried", EDS_CLIENT, 'allowed_methods=["GET"],', "allowed_methods=None,", equivalent=True),
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


def is_problem(mutation: Mutation, outcome: str) -> bool:
    return outcome in ("STALE", "INVALID") or (outcome == "survived" and not mutation.equivalent)


def main(selected: list[str]) -> int:
    mutations = [mutation for mutation in MUTATIONS if not selected or mutation.name in selected]
    if selected and len(mutations) != len(selected):
        print(f"Unknown mutation among: {', '.join(selected)}")
        return 2
    print("Baseline: unmutated offline suite ...", flush=True)
    if run_suite() != 0:
        print("The unmutated suite does not pass, so mutants cannot be judged. Fix it first.")
        return 2

    problems = []
    for mutation in mutations:
        started = time.perf_counter()
        outcome = run_mutation(mutation)
        flag = "  <-- PROBLEM" if is_problem(mutation, outcome) else ""
        print(f"{outcome:9} {mutation.name} ({time.perf_counter() - started:.0f} s){flag}", flush=True)
        if flag:
            problems.append(mutation.name)

    killed = sum(1 for _ in mutations) - len(problems)
    print(f"\n{len(mutations)} mutations, {len(problems)} problems: {', '.join(problems) or 'none'}")
    return 1 if problems else 0 if killed >= 0 else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

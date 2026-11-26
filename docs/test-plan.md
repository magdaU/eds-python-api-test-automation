# Test plan

Plan for testing the current state of `main`. The general approach is in the [test strategy](test-strategy.md); this
document says what is tested, when, by what, and when testing is done.

## 1. Test items

| Item | Version |
| --- | --- |
| API client: `client/` (`EDSApiClient`, `DatasetApi`, `NewsApi`, parsers) and `models/` | `main` |
| EDS API as consumed by the client: datasets `CO2Emis`, `DayAheadPrices`, endpoints `/News*` | recorded samples and JSON Schemas (offline) |
| The public OpenAPI specification (`/swagger/public/swagger.json`), as far as the client relies on it | inline specifications (offline) |
| Test framework: fixtures, helpers, CI workflows, Allure reporting | `main` |

## 2. Features to be tested

| Area | Features |
| --- | --- |
| Dataset queries | `limit`, `offset`, `sort`, `filter` (single, combined, edge and invalid values) |
| News | `/News`, `/News/actual`, `/News/calendar`, `/News/archived`: paths, parameters, 400/204/404 behaviour, calendar vs archive consistency |
| Response contract | JSON Schema and Pydantic validation of dataset and news responses; typed records (`DatasetApi.records()`); `InvalidResponseError` for an unexpected body |
| API specification | The operations and parameters the client uses are still documented in the OpenAPI specification (drift detector) |
| Client robustness | Retry with backoff on 429/5xx, no retry on 4xx, exhaustion, `Retry-After` cap and wait budget, per-dataset overrides, timeout (a read timeout surfaces as `ConnectionError`), refused connection, warning on exhaustion, keyword-only query arguments, session closed by `close()` or `with` |
| Test infrastructure | Severity labels, CI publish guard |
| Quality attributes | Low-load latency and error rate (JMeter), static analysis, statement and branch coverage, known vulnerabilities and committed secrets (`Security` workflow) |

**Not tested:** see "Out of scope" in the [test strategy](test-strategy.md#2-scope) and "Known gaps" in the
[test coverage](test-coverage.md#6-known-gaps).

## 3. Approach

Per the [test strategy](test-strategy.md): mocked component tests for breadth, a scripted local HTTP server for retry
behaviour, JMeter for a latency baseline. The suite sends no requests to the public EDS API. The live tests that did so
are not in the repository now; the option to run them by hand is described in the strategy, section 8.1. Test cases are
catalogued in [test-cases.md](test-cases.md).

## 4. Schedule and triggers

| When | What runs |
| --- | --- |
| Every pull request to `main` | `Tests` (offline suite, random order, Allure results as artifact), `Quality` (`ruff`, `ruff format --check`, `mypy --strict`, coverage gate), `Security` |
| Every push to `main` | `Tests` (offline suite, Allure report published to GitHub Pages), `Quality`, `Security` |
| Monday 04:00 UTC and manual | `Mutation checks`: 62 deliberate breakages of the client, models and schemas; fails when the offline suite misses one. Results in the job summary |
| Monday 05:00 UTC and manual | `Security`: `pip-audit` and `detect-secrets` |
| Manual only | `Performance`: JMeter plan against the public API (2 users, 30 s, think time 1 s); fails on any failed sample |
| After a defect fix | A regression test is added in the fix, then the normal triggers apply |

### 4.1 No live or nightly workflow

- **Cause:** the live tests were removed from the repository on 2026-11-10 (commit `800b1e4e`). The `Live nightly` workflow
  still ran `pytest -m live` every day at 02:00 UTC, so pytest collected nothing and exited with code 5 ("no tests
  collected"). Every scheduled run from 2026-11-17 to 2026-11-25 failed, and GitHub mailed the repository administrators for
  each failure.
- **Decision:** the `Live nightly` workflow was removed on 2026-11-26. Its schedule had already been removed in PR #147, and
  PR #149 made the manual run succeed with a notice; no such run has been observed yet. Removing the workflow means the
  pipeline no longer contains a job that tests nothing.
- **Reasons:** protect the public EDS API from daily load, keep the pipeline free of failing or empty jobs, and gate changes
  on the offline suite. The reasoning and the steps to bring live tests back are in the
  [test strategy, section 8.1](test-strategy.md#81-why-there-is-no-live-or-nightly-workflow).

## 5. Pass and fail criteria

A test passes when all its assertions hold. The suite passes when no test fails or breaks and the coverage gate (90%) is
met. Exit criteria for merging and for a healthy `main` are in the [test strategy](test-strategy.md#9-entry-and-exit-criteria).

## 6. Suspension and resumption

| Situation | Action |
| --- | --- |
| The public EDS API returns 429 or 5xx persistently | Not detected automatically: no workflow sends requests to the API. It is detected only when the live tests are run by hand (strategy, section 8.1). |
| The EDS API changes a contract | Not detected automatically. The offline suite checks the recorded samples and the JSON Schemas; the OpenAPI drift detector checks the documented operations and parameters only when run against a fetched specification. |
| A run produces no results (collection error) | The CI guard blocks publishing of the Allure report; fix the cause (for example a missing dependency) and re-run. |

## 7. Deliverables

| Deliverable | Location | Kept current by |
| --- | --- | --- |
| Test strategy, plan, architecture, coverage, report | `docs/` | Edited by hand when the approach or the measured state changes |
| Test cases | [test-cases.md](test-cases.md) | `scripts/generate_test_cases.py` |
| Test results (one CI run) | [test-results.md](test-results.md) | `scripts/generate_test_results.py` |
| Live report with history | [Allure report](https://magdau.github.io/eds-python-api-test-automation/) | CI on every push to `main` |
| Performance and mutation results | Job summaries of `Performance` and `Mutation checks` | CI |

## 8. Environment and responsibilities

Local development (Windows, Python 3.12), Docker (`python:3.12-slim`), GitHub Actions (`ubuntu-latest`, Python 3.12). The
only external dependency is the public EDS API at `https://api.energidataservice.dk`, which the default suite does not call.
One person designs, implements and reviews the tests. CI runs on every pull request; requiring it through branch protection
is an open task for the repository owner (test strategy, section 9).

## 9. Risks and contingencies

See the risk table in the [test strategy](test-strategy.md#10-risk-based-prioritisation).

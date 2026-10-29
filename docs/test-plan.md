# Test plan

Plan for testing the current state of `main`. The general approach is in the [test strategy](test-strategy.md); this
document says what is tested, when, by what, and when testing is done.

## 1. Test items

| Item | Version |
| --- | --- |
| API client: `client/` (`EDSApiClient`, `DatasetApi`, `NewsApi`, parsers) and `models/` | `main` |
| EDS API as consumed by the client: datasets `CO2Emis`, `DayAheadPrices`, endpoints `/News*` | live, observed behaviour |
| Test framework: fixtures, helpers, CI workflows, Allure reporting | `main` |

## 2. Features to be tested

| Area | Features |
| --- | --- |
| Dataset queries | `limit`, `offset`, `sort`, `filter` (single, combined, edge and invalid values) |
| News | `/News`, `/News/actual`, `/News/calendar`, `/News/archived`: paths, parameters, 400/204/404 behaviour, calendar vs archive consistency |
| Response contract | JSON Schema and Pydantic model validation of dataset and news responses |
| Client robustness | Retry with backoff on 429/5xx, no retry on 4xx, retry exhaustion, per-dataset overrides, timeout, refused connection, warning log on exhaustion |
| Test infrastructure | Allure environment widget, fixture paths, CI publish guard |
| Quality attributes | Low-load latency and error rate (JMeter), static analysis, statement and branch coverage |

**Not tested:** see "Out of scope" in the [test strategy](test-strategy.md#2-scope) and "Known gaps" in the
[test coverage](test-coverage.md#6-known-gaps).

## 3. Approach

Per [test strategy](test-strategy.md): mocked component tests for breadth, a scripted local HTTP server for retry
behaviour, a small number of bounded live tests for the real API, JMeter for a latency baseline. Test cases are
catalogued in [test-cases.md](test-cases.md).

## 4. Schedule and triggers

| When | What runs |
| --- | --- |
| Every pull request | Offline tests, `ruff`, `mypy`, coverage gate |
| Every push to `main` | Full suite incl. live tests, `ruff`, `mypy`, coverage gate, Allure report published |
| Daily 02:00 UTC | Live tests only |
| Monday 03:00 UTC | JMeter performance plan |
| Monday 04:00 UTC | Mutation checks (37 deliberate breakages of the client, models and schemas, offline) |
| After a defect fix | Regression test added in the fix, then the normal triggers |

## 5. Pass and fail criteria

A test passes when all its assertions hold. The suite passes when no test fails or breaks and the coverage gate (90%) is met.
Exit criteria for merging and for a healthy `main` are listed in the [test strategy](test-strategy.md#9-entry-and-exit-criteria).

## 6. Suspension and resumption

| Situation | Action |
| --- | --- |
| The public EDS API returns 429 or 5xx persistently | Live runs fail for infrastructure reasons (on `main` runs the Allure category *Infrastructure problems*; the nightly run has no Allure report, so read its log). Do not raise retries or add requests; wait for the nightly run to recover. Offline tests are unaffected and keep gating pull requests. |
| The EDS API changes a contract | Treat the nightly failure as a finding: update the schema or test if the change is intended, report it otherwise. |
| A run produces no results (collection error) | The CI guard blocks publishing; fix the cause (for example a missing dependency) and re-run. |

## 7. Deliverables

| Deliverable | Location | Kept current by |
| --- | --- | --- |
| Test strategy, plan, coverage, report | `docs/` | Edited by hand when the approach changes |
| Test cases | [test-cases.md](test-cases.md) | `scripts/generate_test_cases.py` |
| Test results | [test-results.md](test-results.md) | `scripts/generate_test_results.py` |
| Live report with history | [Allure report](https://magdau.github.io/eds-python-api-test-automation/) | Published by CI on every push to `main` |
| Performance report | `jmeter-report` artifact of the `Performance` workflow | CI |

## 8. Environment

Local development (Windows, Python 3.12), Docker (`python:3.12-slim`), GitHub Actions (`ubuntu-latest`, Python 3.12).
The only external dependency is the public EDS API at `https://api.energidataservice.dk`.

## 9. Responsibilities

The repository is maintained by one person, who designs, implements and reviews the tests. Every change goes through
a pull request that must pass CI before merge.

## 10. Risks and contingencies

See the risk table in the [test strategy](test-strategy.md#10-risk-based-prioritisation).

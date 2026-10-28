# Test report

Test summary report for the state of `main` at commit `3597f80` (CI build #161), 2026-10-28.
Related: [test strategy](test-strategy.md) · [test plan](test-plan.md) · [test cases](test-cases.md) ·
[test coverage](test-coverage.md) · [test results](test-results.md).

## 1. Summary and recommendation

All 183 automated test cases passed: 167 offline and 16 against the live EDS API. Static analysis is clean and code
coverage of the client is 100% (statements and branches). The nightly live run has passed on each of its last five
executions. **Every exit criterion in the [test strategy](test-strategy.md#9-entry-and-exit-criteria) is met, and the
suite is fit for its purpose: gating changes to the client and detecting drift in the EDS API.**

Two full runs on `main` (builds #154 and #158) ended red today because the public API throttled the live fixtures. That is
fixed (defects 11 and 12), and the runs since take about 40 seconds instead of 5.5 minutes. One residual risk remains: two
runs less than five minutes apart can collide on the API's limit (section 7).

## 2. What was tested

As in the [test plan](test-plan.md): dataset queries (`CO2Emis`, `Elspotprices`), the News endpoints, the response
contract, client robustness (retry, timeout, logging), the test infrastructure (including the Allure failure
categories), executable (Gherkin) specifications of the main client behaviours and a low-load performance baseline.

## 3. Results

| Check | Result | Evidence |
| --- | --- | --- |
| Offline tests (167) | 167 passed | [test results](test-results.md) |
| Live tests (16) | 16 passed | [test results](test-results.md) |
| Failed, broken or skipped tests | 0 | [test results](test-results.md) |
| `ruff` | no findings | `Quality` workflow |
| `mypy` (strict) | no findings | `Quality` workflow |
| Statement coverage of `client/` and `models/` | 100% (gate: 90%) | [test coverage](test-coverage.md#1-code-coverage) |
| Branch coverage | 100% (20 of 20 branches) | [test coverage](test-coverage.md#1-code-coverage) |
| Nightly live run, 2026-10-24 to 2026-10-28 | 5 of 5 passed | `Live nightly` workflow history |
| Performance plan (JMeter), latest run 2026-10-26 | passed (no failed sample) | `Performance` workflow, artifact `jmeter-report` |

Live Allure report with history: <https://magdau.github.io/eds-python-api-test-automation/>.

## 4. Test cases by level

| Level | Offline | Live | Total |
| --- | ---: | ---: | ---: |
| Component | 140 | 0 | 140 |
| Integration | 27 | 0 | 27 |
| System | 0 | 16 | 16 |
| **Total** | **167** | **16** | **183** |

116 test functions and BDD scenarios; the difference is parametrized runs. Details in [test cases](test-cases.md).

## 5. Deviations from the plan

All planned triggers ran, and no test was skipped, disabled or excluded. The one deviation from a green `main`: builds #154
and #158 were red (1 broken test each, an infrastructure problem classified by Allure as such), see defects 11 and 12.

## 6. Defects and weaknesses found and resolved

Found by reviewing CI results and by audits of the tests and documentation against the strategy.

| # | Finding | Impact | Resolved in |
| --- | --- | --- | --- |
| 1 | In build #76 a dependency was missing from `requirements.txt`; pytest failed during collection, yet an empty report (0 tests) was published | The Allure Trend history dropped to 0 | PR #56: `pytest --collect-only` step and a publish guard that blocks empty or broken runs |
| 2 | `requirements.txt` allowed `urllib3>=1.26.9`, but `backoff_jitter` exists only from 2.0 | Client creation raised `TypeError` on old versions | PR #60: minimum is `2.0.2`, verified in a clean environment |
| 3 | The "retryable status" warning could never be reached in real use (`urllib3` raises `RetryError` after the last retry); its test passed only because the mock bypasses retries | The log promised in the docs never appeared | PR #60: the client logs retry exhaustion; tests run against the local HTTP server |
| 4 | Test fixtures used paths relative to the working directory | Tests failed when run from another directory | PR #60: paths are resolved from the code's location, with regression tests |
| 5 | Several tests only repeated what the mock returned, and some compared lower-cased query values; tests for `Elspotprices` were missing; some live checks were too weak (`status != 200`) | Regressions in the client could pass unnoticed | PR #61: tests assert the request that was sent, exact case, both datasets, exact live statuses; mutation checks added |
| 6 | A misspelled per-dataset retry setting was silently ignored | A wrong configuration looked valid | PR #64: `RetryConfig` raises `TypeError` for unknown settings |
| 7 | Live schema, sort and news tests passed on an empty result (an empty list satisfies the schema and the sort check) | A live API returning no data would have shown green | PR #66: the schema helper rejects an empty list and live tests assert status and record count |
| 8 | Allure failure categories were wrong: any message containing "429" (a port number, `KeyError: 4290`) counted as an infrastructure problem, while a real `RetryError` counted as a test defect | Misleading failure triage in the report | PR #66: pattern fixed, verified with Allure 2.46.1, `test_allure_categories.py` guards the mapping |
| 9 | Empty Categories views (Overview widget, Categories page, Categories trend) looked like missing data; the first version of the explanation did not show on the trend once the history had several builds (Allure then draws an empty chart instead of "There is nothing to show"), which was found by checking the published report | A reader could not tell an empty view from a broken report | PRs #69-#72: a `Categories` line in the Environment widget and `allure/report-notes.js` (notes in all three views, shown only while nothing failed, broke or was skipped); verified with real Allure reports in headless Chrome in five situations and on the published report |
| 10 | A dataset name was put into the URL unencoded: `dataset_url("../News")` returned `/dataset/../News`, and spaces, `?` and `#` were not encoded either | A name could leave its path segment and change what is requested | PR #75, developed test-first: the history keeps the `Red:` (4 failing tests), `Green:` (`quote(dataset, safe="")`) and `Refactor:` commits |
| 11 | The client waited out any `Retry-After` without a limit, so when the API throttled, a full run took about 5.5 minutes (10 of the last 20 builds) and the wait was invisible | Slow CI, the job timeout was the only limit | PR #68 logs every wait and its reason; PR #77 refuses a `Retry-After` above 60 s (`RetryConfig.max_retry_after`, `RetryAfterTooLongError`), verified live (the API asked for 299 s, the client gave up in about 3 s) |
| 12 | Each run sent two different queries to `Elspotprices`; the API answers one query per window of about 300 s (measured: 200, cached repeat after 14 s, 429 after 89 s with `Retry-After` 211), so the second was throttled and, once the limit existed, failed fast: builds #154 and #158 were broken | Red `main` for an infrastructure reason | PR #81: one session-scoped live query shared by the sort and schema tests; verified in a clean window and by the first run on `main` (build #161) |

## 7. Residual risks and open items

- **The public API throttles `Elspotprices`; collisions are still possible.** In the Allure history, 10 of the last 20 builds
  took 324-326 s (the API's `Retry-After` was waited out in a fixture) and 10 took 33-43 s; all six latest builds took 37-43 s
  because the wait is now refused after 60 s. The API answers one `Elspotprices` query per window of about 300 s, and every
  run sends exactly one. Two runs less than five minutes apart (for example two merges in a row) can still collide: the
  second then fails fast with `RetryAfterTooLongError`, which Allure files under *Infrastructure problems*. Options if that
  becomes a nuisance: skip these tests with an explicit reason when the API throttles, or run them only in the nightly job.
  The rule is measured, not documented by EDS, and not fully understood (a repeated `limit=1` query kept passing for about a
  minute in one probe).
- **External dependency.** Live tests depend on the public EDS API (availability, rate limits, contract changes). The
  nightly run detects this within a day; offline tests keep gating changes regardless.
- **Untested areas** (details in [test coverage](test-coverage.md#6-known-gaps)): other datasets and query parameters,
  correctness of data values, security, stress and soak load, other Python versions.
- **Diagnostics.** Since the diagnostics change, every request is logged (status, duration, start of an error body) together
  with the wait before each retry and its reason, and Allure attaches the log to the test. The nightly run produces no
  Allure report, but its workflow log contains the same lines.
- **CI stability.** The `Tests` workflow has 161 runs; 10 did not succeed (6%): six during the first days of the project
  (22 and 25 September, causes not examined), two on 23 October (the collection error behind defect 1) and two today
  (defect 12). None was a failed assertion about the product.
- **Process.** At least eleven pull requests (#61, #65, #66, #68-#72, #76, #77 and #79) were merged 17-44 seconds before their
  `Tests` run finished. CI was green each time, but the merge did not wait for it. PRs #73 and #75 were merged after CI had
  finished, so the habit is improving, but nothing enforces it. Requiring the `Tests` and `Quality` checks before merge
  (branch protection) would make the gate automatic.
- **Manual evidence.** Mutation checks and the CI publish-guard simulation are not repeated automatically.

## 8. How this report is kept current

`test-cases.md` and `test-results.md` are generated (`scripts/generate_test_cases.py`, `scripts/generate_test_results.py`).
This report, the strategy, the plan and the coverage document are edited by hand: update the results, the date and the
commit above when a new report is needed.

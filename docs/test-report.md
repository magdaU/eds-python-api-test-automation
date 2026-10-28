# Test report

Test summary report for the state of `main` at commit `3a3309f` (CI build #144), 2026-10-28.
Related: [test strategy](test-strategy.md) · [test plan](test-plan.md) · [test cases](test-cases.md) ·
[test coverage](test-coverage.md) · [test results](test-results.md).

## 1. Summary and recommendation

All 156 automated test cases passed: 140 offline and 16 against the live EDS API. Static analysis is clean and code
coverage of the client is 100% (statements and branches). The nightly live run has passed on each of its last five
executions. **Every exit criterion in the [test strategy](test-strategy.md#9-entry-and-exit-criteria) is met, and the
suite is fit for its purpose: gating changes to the client and detecting drift in the EDS API.**

One open observation needs attention: the duration of a full run on `main` is either about 5.5 minutes or about 35
seconds, depending on whether the public API throttles the live fixtures (section 7).

## 2. What was tested

As in the [test plan](test-plan.md): dataset queries (`CO2Emis`, `Elspotprices`), the News endpoints, the response
contract, client robustness (retry, timeout, logging), the test infrastructure (including the Allure failure
categories) and a low-load performance baseline.

## 3. Results

| Check | Result | Evidence |
| --- | --- | --- |
| Offline tests (140) | 140 passed | [test results](test-results.md) |
| Live tests (16) | 16 passed | [test results](test-results.md) |
| Failed, broken or skipped tests | 0 | [test results](test-results.md) |
| `ruff` | no findings | `Quality` workflow |
| `mypy` (strict) | no findings | `Quality` workflow |
| Statement coverage of `client/` and `models/` | 100% (gate: 90%) | [test coverage](test-coverage.md#1-code-coverage) |
| Branch coverage | 100% (18 of 18 branches) | [test coverage](test-coverage.md#1-code-coverage) |
| Nightly live run, 2026-10-24 to 2026-10-28 | 5 of 5 passed | `Live nightly` workflow history |
| Performance plan (JMeter), latest run 2026-10-26 | passed (no failed sample) | `Performance` workflow, artifact `jmeter-report` |

Live Allure report with history: <https://magdau.github.io/eds-python-api-test-automation/>.

## 4. Test cases by level

| Level | Offline | Live | Total |
| --- | ---: | ---: | ---: |
| Component | 126 | 0 | 126 |
| Integration | 14 | 0 | 14 |
| System | 0 | 16 | 16 |
| **Total** | **140** | **16** | **156** |

97 test functions; the difference is parametrized runs. Details in [test cases](test-cases.md).

## 5. Deviations from the plan

None. All planned triggers ran, and no test was skipped, disabled or excluded.

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

## 7. Residual risks and open items

- **Run duration is bimodal; the public API throttles.** In the Allure history, 14 of the last 20 builds took 323-326 s
  and 6 took 16-36 s (build #144 took 36 s). The summed duration of the test bodies is about 17-19 s in both cases. Request
  diagnostics added afterwards showed the cause on a local run: the API answered `429` with `Retry-After` and the client
  waited it out (`Retrying in 217.0 s because the server sent Retry-After (status 429)`; an earlier attempt waited 300 s).
  The waits happen in fixtures that call the live API during setup (`co2_response`, `elspotprices_response`), which is why
  they are not part of the test bodies. The same cause was confirmed in CI: the log attached to a test in build #136 shows
  `Retrying in 289.0 s because the server sent Retry-After (status 429)` for the same request (`Elspotprices`, `limit=1`);
  other live tests waited 4 s and 7 s. The client has no cap on the wait, so a throttled API can stretch a run to
  minutes; the job timeout (30 min) is the only limit.
- **External dependency.** Live tests depend on the public EDS API (availability, rate limits, contract changes). The
  nightly run detects this within a day; offline tests keep gating changes regardless.
- **Untested areas** (details in [test coverage](test-coverage.md#6-known-gaps)): other datasets and query parameters,
  correctness of data values, security, stress and soak load, other Python versions.
- **Diagnostics.** Since the diagnostics change, every request is logged (status, duration, start of an error body) together
  with the wait before each retry and its reason, and Allure attaches the log to the test. The nightly run produces no
  Allure report, but its workflow log contains the same lines.
- **Process.** At least eight pull requests (#61, #65, #66 and #68-#72) were merged 17-39 seconds before their `Tests` run
  finished. CI was green each time, but the merge did not wait for it. Requiring the `Tests` and `Quality` checks before merge
  (branch protection) would make the gate automatic.
- **Manual evidence.** Mutation checks and the CI publish-guard simulation are not repeated automatically.

## 8. How this report is kept current

`test-cases.md` and `test-results.md` are generated (`scripts/generate_test_cases.py`, `scripts/generate_test_results.py`).
This report, the strategy, the plan and the coverage document are edited by hand: update the results, the date and the
commit above when a new report is needed.

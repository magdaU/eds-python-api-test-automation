# Test report

Test summary report for the state of `main` at commit `b304c99` (CI build #128), 2026-10-28.
Related: [test strategy](test-strategy.md) · [test plan](test-plan.md) · [test cases](test-cases.md) ·
[test coverage](test-coverage.md) · [test results](test-results.md).

## 1. Summary and recommendation

All 136 automated test cases passed: 120 offline and 16 against the live EDS API. Static analysis is clean and code
coverage of the client is 100% (statements and branches). The nightly live run has passed on each of its last five
executions. **Every exit criterion in the [test strategy](test-strategy.md#9-entry-and-exit-criteria) is met, and the
suite is fit for its purpose: gating changes to the client and detecting drift in the EDS API.**

Known limits are listed in section 7 and, in full, in [test coverage](test-coverage.md#6-known-gaps).

## 2. What was tested

As in the [test plan](test-plan.md): dataset queries (`CO2Emis`, `Elspotprices`), the News endpoints, the response
contract, client robustness (retry, timeout, logging), the test infrastructure and a low-load performance baseline.

## 3. Results

| Check | Result | Evidence |
| --- | --- | --- |
| Offline tests (120) | 120 passed | [test results](test-results.md) |
| Live tests (16) | 16 passed | [test results](test-results.md) |
| Failed, broken or skipped tests | 0 | [test results](test-results.md) |
| `ruff` | no findings | `Quality` workflow |
| `mypy` (strict) | no findings | `Quality` workflow |
| Statement coverage of `client/` and `models/` | 100% (gate: 90%) | [test coverage](test-coverage.md#1-code-coverage) |
| Branch coverage | 100% (14 of 14 branches) | [test coverage](test-coverage.md#1-code-coverage) |
| Nightly live run, 2026-10-24 to 2026-10-28 | 5 of 5 passed | `Live nightly` workflow history |
| Performance plan (JMeter), latest run 2026-10-26 | passed (no failed sample) | `Performance` workflow, artifact `jmeter-report` |

Live Allure report with history: <https://magdau.github.io/eds-python-api-test-automation/>.

## 4. Test cases by level

| Level | Offline | Live | Total |
| --- | ---: | ---: | ---: |
| Component | 110 | 0 | 110 |
| Integration | 10 | 0 | 10 |
| System | 0 | 16 | 16 |
| **Total** | **120** | **16** | **136** |

85 test functions; the difference is parametrized runs. Details in [test cases](test-cases.md).

## 5. Deviations from the plan

None. All planned triggers ran, and no test was skipped, disabled or excluded.

## 6. Defects and weaknesses found and resolved

Found by reviewing CI results and by an audit of the tests and documentation against the strategy.

| # | Finding | Impact | Resolved in |
| --- | --- | --- | --- |
| 1 | In build #76 a dependency was missing from `requirements.txt`; pytest failed during collection, yet an empty report (0 tests) was published | The Allure Trend history dropped to 0 | PR #56: `pytest --collect-only` step and a publish guard that blocks empty or broken runs |
| 2 | `requirements.txt` allowed `urllib3>=1.26.9`, but `backoff_jitter` exists only from 2.0 | Client creation raised `TypeError` on old versions | PR #60: minimum is `2.0.2`, verified in a clean environment |
| 3 | The "retryable status" warning could never be reached in real use (`urllib3` raises `RetryError` after the last retry); its test passed only because the mock bypasses retries | The log promised in the docs never appeared | PR #60: the client logs retry exhaustion; tests run against the local HTTP server |
| 4 | Test fixtures used paths relative to the working directory | Tests failed when run from another directory | PR #60: paths are resolved from the code's location, with regression tests |
| 5 | Several tests only repeated what the mock returned, and some compared lower-cased query values; tests for `Elspotprices` were missing; some live checks were too weak (`status != 200`) | Regressions in the client could pass unnoticed | PR #61: tests assert the request that was sent, exact case, both datasets, exact live statuses; mutation checks added |
| 6 | A misspelled per-dataset retry setting was silently ignored | A wrong configuration looked valid | PR #64: `RetryConfig` raises `TypeError` for unknown settings |

## 7. Residual risks and open items

- **External dependency.** Live tests depend on the public EDS API (availability, rate limits, contract changes). The
  nightly run detects this within a day; offline tests keep gating changes regardless.
- **Untested areas** (details in [test coverage](test-coverage.md#6-known-gaps)): other datasets and query parameters,
  correctness of data values, security, stress and soak load, other Python versions.
- **Process.** Pull request #61 was merged about 20 seconds before its `Tests` run finished (CI was green, but the merge
  did not wait for it). Requiring the `Tests` and `Quality` checks before merge (branch protection) would make the gate
  automatic.
- **Manual evidence.** Mutation checks and the CI publish-guard simulation are not repeated automatically.

## 8. How this report is kept current

`test-cases.md` and `test-results.md` are generated (`scripts/generate_test_cases.py`, `scripts/generate_test_results.py`).
This report, the strategy, the plan and the coverage document are edited by hand: update the results, the date and the
commit above when a new report is needed.

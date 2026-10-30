# Test report

Test summary report for the state of `main` at commit `3931c57` (CI build #201), 2026-10-30.
Related: [test strategy](test-strategy.md) · [test plan](test-plan.md) · [test cases](test-cases.md) ·
[test coverage](test-coverage.md) · [test results](test-results.md) · [test architecture](test-architecture.md).

## 1. Summary and recommendation

The suite has 156 automated test cases: 122 offline and 34 against the live EDS API. The 144 that run on every push to `main`
(122 offline, 22 live) all passed in build #201 (none failed, broken or skipped). The other 12 are data-quality checks that
run in the nightly job only, so they are not in the Allure report; they passed in the nightly run of 2026-10-30 (08:14 UTC),
the first one to include them. Static analysis is clean, coverage of the client is 100% (statements and branches), the
dependency audit and secret scan are clean, and all 45 mutations of the client are killed (run locally). The nightly live run
passed on each of its seven executions (2026-10-24 to 2026-10-30). **Every exit criterion in the
[test strategy](test-strategy.md#9-entry-and-exit-criteria) is met, and the suite is fit for its purpose: gating changes to the
client and detecting drift in the EDS API.**

Since build #177 (2026-10-29): duplicate tests were removed after checking per mutation which test kills what (defect 21); the
client was hardened (defects 17, 18); `pip-audit` flagged `requests` and `pytest`, which were bumped (defect 19); a live test now
notices when EDS stops documenting an operation the client uses (defect 22); and a review found that a retry override for one
dataset also applied to datasets with a longer name (defect 23, PR #100). Residual risks are in section 7: the `Mutation checks`
workflow has not run in Actions yet, and the nightly run has not yet run with the new dependency pins.

## 2. What was tested

As in the [test plan](test-plan.md): dataset queries (`CO2Emis`, `DayAheadPrices`), typed records, data quality, the News
endpoints, the response contract and OpenAPI drift, client robustness (retry, timeout, logging, closable session, unexpected
bodies), the test infrastructure (including Allure failure categories), Gherkin specifications of the main client behaviours,
a low-load performance baseline, and known vulnerabilities and secrets.

## 3. Results

| Check | Result | Evidence |
| --- | --- | --- |
| Offline tests (122) | 122 passed, in random order | [test results](test-results.md) |
| Live tests on `main` (22) | 22 passed | [test results](test-results.md) |
| Data-quality checks (12, nightly only) | 12 passed in the nightly run of 2026-10-30 (commit `ebe4111`); not yet run with the current dependency pins | `Live nightly` workflow |
| Failed, broken or skipped tests | 0 | [test results](test-results.md) |
| `ruff` (with the `PT` rules), `mypy` (strict) | no findings | `Quality` workflow |
| Statement / branch coverage of `client/` and `models/` | 100% (197 statements, 26 of 26 branches); gate 90% | [test coverage](test-coverage.md#1-code-coverage) |
| Mutation checks | 45 of 45 killed (local run on 2026-10-30; not yet run in Actions) | `scripts/mutation_check.py` |
| Known vulnerabilities, committed secrets | none (`pip-audit`, `detect-secrets`) | `Security` workflow |
| Nightly live run, 2026-10-24 to 2026-10-30 | 7 of 7 passed | `Live nightly` workflow history |
| Performance plan (JMeter), latest run 2026-10-26 | passed; the plan has changed since (`DayAheadPrices` endpoint, percentiles in the job summary) and has not run again | `Performance` workflow, artifact `jmeter-report` |

The Allure report of `main` holds the 144 tests of build #201. Live report with history: <https://magdau.github.io/eds-python-api-test-automation/>.

## 4. Test cases by level

| Level | Offline | Live | Total |
| --- | ---: | ---: | ---: |
| Component | 98 | 0 | 98 |
| Integration | 23 | 0 | 23 |
| System | 1 | 34 | 35 |
| **Total** | **122** | **34** | **156** |

The 34 live cases are 22 that run on every push to `main` and the 12 nightly data-quality checks. The one offline System case
proves the OpenAPI drift detector can fail. The suite has 115 test functions and BDD scenarios; the difference is parametrized runs.
Details in [test cases](test-cases.md).

## 5. Deviations from the plan

All planned triggers ran except `Mutation checks`, which has not run in Actions yet (first scheduled run: Monday 2026-11-02
04:00 UTC; the catalogue was run locally). No test was skipped or disabled. The 12 data-quality checks are left out of the run
on `main` on purpose (`-m "not data_quality"`). `main` was red twice: builds #154 and #158 (1 broken test each, an
infrastructure problem classified as such by Allure), see defects 11 and 12.

## 6. Defects and weaknesses found and resolved

Found by reviewing CI results and by auditing the tests and documentation against the strategy.

| # | Finding | Impact | Resolved in |
| --- | --- | --- | --- |
| 1 | In build #76 a dependency was missing from `requirements.txt`; pytest failed during collection, yet an empty report (0 tests) was published | Allure Trend history dropped to 0 | PR #56: `pytest --collect-only` step and a publish guard |
| 2 | `requirements.txt` allowed `urllib3>=1.26.9`, but `backoff_jitter` exists only from 2.0 | `TypeError` on client creation with old versions | PR #60: minimum `2.0.2`, verified in a clean environment |
| 3 | The "retryable status" warning could never be reached (`urllib3` raises `RetryError` after the last retry); its test passed only because the mock bypasses retries | The promised log never appeared | PR #60: the client logs retry exhaustion; tests use the local HTTP server |
| 4 | Fixtures used paths relative to the working directory | Tests failed from another directory | PR #60: paths resolved from the code's location |
| 5 | Tests repeated what the mock returned, some compared lower-cased query values, `Elspotprices` tests were missing, some live checks were weak (`status != 200`) | Client regressions could pass unnoticed | PR #61: tests assert the request sent, exact case, both datasets, exact live statuses; mutation checks added |
| 6 | A misspelled per-dataset retry setting was silently ignored | A wrong configuration looked valid | PR #64: `RetryConfig` raises `TypeError` for unknown settings |
| 7 | Live schema, sort and news tests passed on an empty result | An API returning no data would have shown green | PR #66: the schema helper rejects an empty list; live tests assert status and record count |
| 8 | Allure categories were wrong: any message containing "429" (a port number, `KeyError: 4290`) counted as infrastructure, a real `RetryError` as a test defect | Misleading failure triage | PR #66: pattern fixed (Allure 2.46.1), `test_allure_categories.py` guards it |
| 9 | Empty Categories views looked like missing data; the first explanation did not show on the trend once the history had several builds | A reader could not tell an empty view from a broken report | PRs #69-#72: `Categories` line in the Environment widget and `allure/report-notes.js`, verified with real reports in headless Chrome and on the published report |
| 10 | A dataset name was put into the URL unencoded (`dataset_url("../News")` gave `/dataset/../News`) | A name could leave its path segment | PR #75, test-first: `Red:` (4 failing tests), `Green:` (`quote(dataset, safe="")`), `Refactor:` |
| 11 | The client waited out any `Retry-After` without a limit, so a throttled full run took about 5.5 minutes (10 of the last 20 builds) and the wait was invisible | Slow CI, the job timeout was the only limit | PR #68 logs every wait; PR #77 refuses a `Retry-After` above 60 s (`RetryAfterTooLongError`), verified live (asked for 299 s, gave up in about 3 s) |
| 12 | Each run sent two different queries to `Elspotprices`; the API allows one per ~300 s window, so the second was throttled and failed fast (builds #154, #158) | Red `main` for an infrastructure reason | PR #81: one session-scoped live query shared by the sort and schema tests |
| 13 | EDS discontinued `Elspotprices` after 2025-09-30 while its `active` flag stayed true; 5 live tests ran on frozen data (found in the audit of 2026-10-29 from the dataset metadata) | Green tests said nothing about current prices | PRs #87 (metadata check), #88 (tests, schema, model, sample, JMeter moved to `DayAheadPrices`), #89 (nightly data-quality checks) |
| 14 | Eight tests could not fail (they checked their own mock), the live paging assertion passed with four shared records, only some live tests had a network-error rerun | False confidence, avoidable red builds | PR #86: tests removed, paging compares two pages with one larger page, reruns on every live test |
| 15 | Documents said live smoke tests rerun but only edge-case ones did; the README structure was incomplete; the rate limit was not mentioned | Documents could not be trusted | PR #83 |
| 16 | Dataset schemas did not require `limit` and `dataset`, and no live test checked that a filter returns only the requested values | An altered envelope or an ignored filter could pass | PR #84 |
| 17 | `DatasetApi.records()` did not pass `limit`, `offset`, `sort` and `filters` on (found because the mutation baseline failed) | Typed records ignored every query parameter | PR #94 |
| 18 | `get_dataset` and `DatasetApi.get` took the same query arguments in a different order, so a positional call passed `filters` as `offset`; the session could not be closed; a non-JSON or non-object body ended in a bare `JSONDecodeError`/`KeyError` | A wrong call looked valid, connections stayed open | PR #97: keyword-only arguments in one order, `close()` and `with`, `InvalidResponseError`; three new mutations |
| 19 | `pip-audit` found known vulnerabilities in `requests` 2.32.3 and `pytest` 8.3.3 | Vulnerable environment | PR #94: bumped to 2.33.0 and 9.0.3 after the offline suite, `mypy` and coverage passed; `Security` workflow added |
| 20 | The README said 203 tests while the suite had 154 | Numbers could not be trusted | PR #95 |
| 21 | Duplicate and trivial tests (same mechanism for two datasets, two "no warning on success" checks, a property test that was a subset of another) | Upkeep cost, false sense of breadth | PR #96: ten tests removed after a per-mutation kill matrix; all mutations still killed |
| 22 | The strategy and coverage documents said EDS publishes no OpenAPI specification. It does (`/swagger/public/swagger.json`), but it is thin | A wrong premise behind a tooling decision | PR #98 (drift test) and a document refresh |
| 23 | A per-dataset retry override was mounted by URL prefix, so an override for `CO2Emis` also served `CO2EmisProg` | A dataset retried with another's settings | PR #100: adapter chosen by exact dataset URL and closed with the client; reproduced by a test that failed before the fix; two new mutations |
| 24 | The documents listed boundary values that no test used; the README tree missed two test files; `test-cases.md` numbered tests in random order (pytest-randomly) | Documents promised more than the tests did; a diff on every regeneration | PR #100 and a document refresh; the generator collects tests in source order |

## 7. Residual risks and open items

- **The public API throttles by dataset; the limit of `DayAheadPrices` is not measured.** The discontinued `Elspotprices` allowed
  one query per ~300 s: 10 of the last 20 builds then took 324-326 s (the `Retry-After` was waited out) and 10 took 33-43 s.
  The wait is now refused after 60 s. A run on `main` sends one sorted query to `DayAheadPrices`, the nightly run one more; two
  local runs a few seconds apart both passed. If a limit exists, a second run within its window fails fast with
  `RetryAfterTooLongError` (Allure: *Infrastructure problems*). Options if it becomes a nuisance: skip these tests with an
  explicit reason when throttled, or run them only nightly.
- **The data-quality thresholds are first estimates.** Freshness of 2 hours for `CO2Emis`, wide value ranges and the 15 and 5
  minute steps come from one look at the live data on 2026-10-29; the 12 checks have passed once in the nightly run.
- **External dependency.** Live tests depend on the public EDS API (availability, rate limits, contract changes, discontinued
  datasets). The nightly run detects this within a day; offline tests keep gating changes.
- **Untested areas** (see [test coverage](test-coverage.md#6-known-gaps)): other datasets, parameters such as `start`, `end`,
  `columns`, `timezone`, operations the client does not call, correctness of data values, TLS, stress and soak load, other Python versions.
- **The published specification is thin** (only status 200, no response schema for `/dataset/{datasetName}`), so the drift test
  checks only that what the client uses is still documented; the response contract stays in the JSON Schemas.
- **Diagnostics.** Every request and every retry wait is logged and Allure attaches the log. The nightly run has no Allure report,
  but its workflow log has the same lines.
- **CI stability.** The `Tests` workflow has 201 runs; 10 did not succeed (5%): six in the first days (22 and 25 September, causes
  not examined), two on 23 October (defect 1) and two on 28 October (defect 12). The latest 43 runs (#159-#201) all succeeded.
  None was a failed assertion about the product.
- **Process.** At least 26 pull requests (#61 to #98, measured from the GitHub API on 2026-10-29 and 2026-10-30) were merged 19-49
  seconds before their `Tests` run finished. CI was green each time, but nothing enforces the wait. Requiring `Tests` and `Quality`
  before merge (branch protection) would make the gate automatic.
- **Performance.** The JMeter plan queries `DayAheadPrices` and prints p50, p95 and p99 in the job summary, but has not run since
  the change and has no percentile limits yet (see [test architecture](test-architecture.md#4-performance-acceptance)).
- **Manual evidence.** The CI publish-guard simulation is not repeated automatically. `Mutation checks` runs weekly (45 changes;
  local run on 2026-10-30: all caught) but has no run in Actions yet; its report is still to be checked.
- **Dependency pins.** `requests` 2.33.0 and `pytest` 9.0.3 passed the offline suite and the live tests of builds #187 and #201.
  The nightly run with the data-quality checks has not run with them yet (first: 2026-10-31).
- **Scheduled runs start late.** The cron of `Live nightly` is 02:00 UTC, but GitHub started the last seven runs between 06:57
  and 08:14 UTC. Plan around the date, not the hour.

## 8. How this report is kept current

`test-cases.md` and `test-results.md` are generated (`scripts/generate_test_cases.py`, `scripts/generate_test_results.py`).
This report, the strategy, the plan and the coverage document are edited by hand: update the results, the date and the commit
above when a new report is needed.

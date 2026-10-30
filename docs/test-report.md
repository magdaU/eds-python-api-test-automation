# Test report

Test summary report for the state of `main` at commit `2acf689` (CI build #195), 2026-10-30.
Related: [test strategy](test-strategy.md) · [test plan](test-plan.md) · [test cases](test-cases.md) ·
[test coverage](test-coverage.md) · [test results](test-results.md) · [test architecture](test-architecture.md).

## 1. Summary and recommendation

The suite has 153 automated test cases: 119 offline and 34 against the live EDS API. The 141 that run on every push to `main`
(119 offline, 22 live) all passed in build #195 (141 of 141, none failed, broken or skipped). The other 12 are data-quality
checks that run in the nightly job only, so they are not in the Allure report; they passed in the nightly run of 2026-10-30
(08:14 UTC), the first one to include them. Static analysis is clean, code coverage of the client is 100% (statements and
branches), the dependency audit and the secret scan are clean, and all 43 mutations of the client are killed (run locally). The
nightly live run passed on each of its seven executions (2026-10-24 to 2026-10-30). **Every exit criterion in the
[test strategy](test-strategy.md#9-entry-and-exit-criteria) is met, and the suite is fit for its purpose: gating changes to the
client and detecting drift in the EDS API.**

Since build #177 (2026-10-29): duplicate tests were removed after checking, per mutation, which test kills what (defect 21); the
client was hardened (keyword-only query arguments in one order, a closable session, one error for an unexpected body, and
`records()` passing its query on; defects 17 and 18); `pip-audit` flagged `requests` and `pytest`, which were bumped (defect 19);
and a live test now notices when EDS stops documenting an operation the client uses in its OpenAPI specification (defect 22).
Residual risks are in section 7: the `Mutation checks` workflow has not run in Actions yet, and the nightly run has not yet run with
the new dependency pins.

## 2. What was tested

As in the [test plan](test-plan.md): dataset queries (`CO2Emis`, `DayAheadPrices`), typed records, data quality, the News endpoints,
the response contract and the drift of the published OpenAPI specification, client robustness (retry, timeout, logging, a closable
session, unexpected bodies), the test infrastructure (including the Allure failure categories), executable (Gherkin) specifications
of the main client behaviours, a low-load performance baseline, and known vulnerabilities and secrets.

## 3. Results

| Check | Result | Evidence |
| --- | --- | --- |
| Offline tests (119) | 119 passed, in random order | [test results](test-results.md) |
| Live tests on `main` (22) | 22 passed | [test results](test-results.md) |
| Data-quality checks (12, nightly only) | 12 passed in the nightly run of 2026-10-30 (commit `ebe4111`); not yet run with the current dependency pins | `Live nightly` workflow |
| Failed, broken or skipped tests | 0 | [test results](test-results.md) |
| `ruff` (with the `PT` rules) | no findings | `Quality` workflow |
| `mypy` (strict) | no findings | `Quality` workflow |
| Statement coverage of `client/` and `models/` | 100%, 187 statements (gate: 90% of the combined figure) | [test coverage](test-coverage.md#1-code-coverage) |
| Branch coverage | 100% (24 of 24 branches) | [test coverage](test-coverage.md#1-code-coverage) |
| Mutation checks | 43 of 43 killed (local run on 2026-10-30; not yet run in Actions) | `scripts/mutation_check.py` |
| Known vulnerabilities, committed secrets | none (`pip-audit`, `detect-secrets`) | `Security` workflow |
| Nightly live run, 2026-10-24 to 2026-10-30 | 7 of 7 passed | `Live nightly` workflow history |
| Performance plan (JMeter), latest run 2026-10-26 | passed (no failed sample); the plan has changed since (`DayAheadPrices` endpoint, percentiles in the job summary) and has not run again | `Performance` workflow, artifact `jmeter-report` |

The Allure report of `main` holds the 141 tests of the push run (build #195). Live Allure report with history: <https://magdau.github.io/eds-python-api-test-automation/>.

## 4. Test cases by level

| Level | Offline | Live | Total |
| --- | ---: | ---: | ---: |
| Component | 95 | 0 | 95 |
| Integration | 23 | 0 | 23 |
| System | 1 | 34 | 35 |
| **Total** | **119** | **34** | **153** |

The 34 live cases are 22 that run on every push to `main` and the 12 nightly data-quality checks. The one offline System case
is the test that proves the OpenAPI drift detector can fail. 112 test functions and BDD scenarios; the difference is parametrized runs. Details in [test cases](test-cases.md).

## 5. Deviations from the plan

All planned triggers ran except `Mutation checks`, which has not run in Actions yet (first scheduled run: Monday 2026-11-02
04:00 UTC; the catalogue was run locally), and no test was skipped or disabled. The 12 data-quality checks are left out of the run on
`main` on purpose (`-m "not data_quality"`) and run in the nightly job. The one deviation from a green `main`: builds #154
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
| 13 | EDS had discontinued `Elspotprices` after 2025-09-30 while its `active` metadata flag stayed true; 5 live tests and the shared-query workaround ran on frozen data. Found in the audit of 2026-10-29 by reading the dataset metadata | Green tests said nothing about current prices; the nightly run would have gone red only when EDS removed the dataset | PR #87 (metadata check of title and update interval), PR #88 (tests, schema, model, sample and JMeter endpoint moved to `DayAheadPrices`), PR #89 (nightly data-quality checks) |
| 14 | Eight tests could not fail (they checked their own mock or the language), the live paging assertion passed with four shared records, and only some live tests had a rerun on network errors | False confidence and avoidable red builds | PR #86: tests removed, paging compares two pages with one larger page, reruns on every live test |
| 15 | The documents said live smoke tests rerun but only the edge-case ones did; the README structure list was incomplete, the CI guard text sat under "Run in Docker" and the API rate limit was not mentioned | A reader could not trust the documents | PR #83 |
| 16 | The dataset schemas did not require `limit` and `dataset` from the documented response, and no live test checked that a filter returns only the requested values | An altered response envelope or an ignored filter could pass | PR #84 |
| 17 | `DatasetApi.records()` accepted `limit`, `offset`, `sort` and `filters` but did not pass them on. The baseline of the mutation checks failed before any mutation, which led to it; the test for typed records caught it | Typed records ignored every query parameter | PR #94 |
| 18 | `EDSApiClient.get_dataset` and `DatasetApi.get` took the same query arguments in a different order (`limit, filters, offset, sort` against `limit, offset, sort, filters`), so a positional call passed `filters` as `offset`; the session could not be closed; a body that was not JSON or not an object ended in a bare `JSONDecodeError` or `KeyError` | A wrong call looked valid, connections stayed open, errors said little | PR #97: keyword-only arguments in one order, `close()` and `with`, `InvalidResponseError`; three new mutations |
| 19 | `pip-audit` found known vulnerabilities in `requests` 2.32.3 (PYSEC-2026-1872, PYSEC-2026-2275) and `pytest` 8.3.3 (PYSEC-2026-1845) | Vulnerable dependencies in the test and runtime environment | PR #94: bumped to 2.33.0 and 9.0.3 after the offline suite, `mypy` and coverage passed in a clean environment; `Security` workflow added; live tests passed on `main` in build #187 |
| 20 | The README said 203 tests while the suite had 154 | A reader could not trust the numbers | PR #95 |
| 21 | Duplicate and trivial tests: the same mechanism tested for two datasets, two "no warning on success" checks, a property test that was a subset of another | Upkeep cost and a false sense of breadth | PR #96: ten tests removed after a matrix of which test kills which mutation; the mutations are still all killed |
| 22 | The strategy and coverage documents said EDS publishes no OpenAPI specification, and Schemathesis had been put aside for that reason. EDS does publish one (`/swagger/public/swagger.json`); it is thin (only status 200, no response schema for `/dataset`, unbounded `limit`) | A wrong premise behind a tooling decision | PR #98 (drift test) and the refresh of these documents: premise corrected, Schemathesis left out for the right reasons |

## 7. Residual risks and open items

- **The public API throttles by dataset; the limit of `DayAheadPrices` is not measured.** The discontinued `Elspotprices` answered
  one query per window of about 300 s: in the Allure history of that time, 10 of the last 20 builds took 324-326 s (the API's
  `Retry-After` was waited out in a fixture) and 10 took 33-43 s. The wait is now refused after 60 s. A run on `main` sends one
  sorted query to `DayAheadPrices`, the nightly run one more for the data-quality checks; two local runs a few seconds apart both
  passed. If a limit exists, a second run within its window fails fast with `RetryAfterTooLongError`, which Allure files under
  *Infrastructure problems*. Options if that becomes a nuisance: skip these tests with an explicit reason when the API throttles,
  or run them only in the nightly job.
- **The data-quality thresholds are first estimates.** Freshness of 2 hours for `CO2Emis`, wide value ranges and the 15 minute
  and 5 minute steps come from one look at the live data on 2026-10-29. The 12 checks passed in the nightly run of 2026-10-30; that is one run, so the thresholds are still estimates.
- **External dependency.** Live tests depend on the public EDS API (availability, rate limits, contract changes, discontinued
  datasets). The nightly run detects this within a day; offline tests keep gating changes regardless.
- **Untested areas** (details in [test coverage](test-coverage.md#6-known-gaps)): other datasets, query parameters (including
  `start`, `end`, `columns` and `timezone`) and the operations of the specification the client does not call (`/dataset/{name}/download`,
  the `/meta/*` lists), correctness of data values, TLS, stress and soak load, other Python versions.
- **The published specification is thin.** It declares only status 200 and has no response schema for `/dataset/{datasetName}`;
  the drift test therefore checks only that what the client uses is still documented, and the response contract stays in this
  repository's JSON Schemas.
- **Diagnostics.** Every request is logged (status, duration, start of an error body) together with the wait before each retry and its
  reason, and Allure attaches the log to the test. The nightly run produces no Allure report, but its workflow log contains the same lines.
- **CI stability.** The `Tests` workflow has 195 runs; 10 did not succeed (5%): six during the first days of the project
  (22 and 25 September, causes not examined), two on 23 October (the collection error behind defect 1) and two on 28 October
  (defect 12). The latest 37 runs (#159-#195) all succeeded. None was a failed assertion about the product.
- **Process.** Every pull request merged from #77 to #89 (12 merges) was merged 33-49 seconds before its `Tests` run finished
  (measured on 2026-10-29 from the GitHub API). Of the nine merges #90 to #98, five (#90, #93, #94, #95 and #98) came 19-39 seconds
  before the `Tests` run of the pull request finished and four waited (measured on 2026-10-30). Together with the earlier eleven
  (#61, #65, #66, #68-#72, #76, #77 and #79) that makes at least 26 merges that did not wait for CI. CI was green each time, but nothing enforces the wait. Requiring the `Tests` and
  `Quality` checks before merge (branch protection) would make the gate automatic.
- **Performance.** The JMeter plan now queries `DayAheadPrices` and prints p50, p95 and p99 in the job summary, but has not run since
  the change and has no percentile limits yet (see [test architecture](test-architecture.md#4-performance-acceptance)).
- **Manual evidence.** The CI publish-guard simulation is not repeated automatically. Mutation checks are set to run weekly
  (`Mutation checks` workflow, catalogue of 43 changes; local run on 2026-10-30: all 43 caught), but the workflow has no run in
  Actions yet; its report (job summary and artifact) is still to be checked.
- **Dependency pins.** `requests` 2.33.0 and `pytest` 9.0.3 passed the offline suite and the live tests of the push runs
  (builds #187 and #195). The nightly run, which also holds the data-quality checks, has not run with them yet (the first one is the
  run of 2026-10-31).
- **Scheduled runs start late.** The cron of `Live nightly` is 02:00 UTC, but GitHub started the last seven runs between 06:57
  and 08:14 UTC. Plan around the date, not the hour.

## 8. How this report is kept current

`test-cases.md` and `test-results.md` are generated (`scripts/generate_test_cases.py`, `scripts/generate_test_results.py`).
This report, the strategy, the plan and the coverage document are edited by hand: update the results, the date and the
commit above when a new report is needed.

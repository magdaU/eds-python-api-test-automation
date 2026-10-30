# Test report

Test summary report for the state of `main` at commit `67915ed` (CI build #218), 2026-10-30.
Related: [test strategy](test-strategy.md) · [test plan](test-plan.md) · [test cases](test-cases.md) ·
[test coverage](test-coverage.md) · [test results](test-results.md) · [test architecture](test-architecture.md).

## 1. Summary and recommendation

The suite has 164 automated test cases: 130 offline and 34 against the live EDS API. Build #218 (commit `67915ed`) ran the 152 that run on every push to `main` (130 offline, 22 live), and all passed. The other 12 are data-quality checks that run in the nightly job only (not in
the Allure report) and passed in the nightly run of 2026-10-30, the first to include them. Static analysis, the dependency
audit and the secret scan are clean, coverage of the client is 100% (statements and branches), all 49 mutations are killed
(local run), and the nightly live run passed on each of its seven executions (2026-10-24 to 2026-10-30). **Every exit criterion
in the [test strategy](test-strategy.md#9-entry-and-exit-criteria) is met, and the suite is fit for its purpose: gating
changes to the client and detecting drift in the EDS API.**

Since build #177 (2026-10-29) duplicate tests were removed (defect 21), the client was hardened (17, 18, 23), vulnerable
dependencies were bumped (19), a drift test on the OpenAPI specification was added (22), and the review findings of 2026-10-30
were fixed (25-28). Residual risks are in section 7.

## 2. What was tested

As in the [test plan](test-plan.md): dataset queries, typed records, data quality, the News endpoints, the response contract and
OpenAPI drift, client robustness, the test infrastructure, Gherkin specifications, a low-load performance baseline, and known
vulnerabilities and secrets.

## 3. Results

| Check | Result | Evidence |
| --- | --- | --- |
| Offline tests (130) | 130 passed, in random order | [test results](test-results.md) |
| Live tests on `main` (22) | 22 passed | [test results](test-results.md) |
| Data-quality checks (12, nightly only) | 12 passed in the nightly run of 2026-10-30 (commit `ebe4111`); not yet run with the current dependency pins | `Live nightly` workflow |
| Failed, broken or skipped tests | 0 | [test results](test-results.md) |
| `ruff` (with the `PT` rules), `mypy` (strict) | no findings | `Quality` workflow |
| Statement / branch coverage of `client/` and `models/` | 100% (207 statements, 28 of 28 branches); gate 90% | [test coverage](test-coverage.md#1-code-coverage) |
| Mutation checks | 49 of 49 killed (local run on 2026-10-30; not yet run in Actions) | `scripts/mutation_check.py` |
| Known vulnerabilities, committed secrets | none (`pip-audit`, `detect-secrets`) | `Security` workflow |
| Nightly live run, 2026-10-24 to 2026-10-30 | 7 of 7 passed | `Live nightly` workflow history |
| Performance plan (JMeter), latest run 2026-10-26 | passed; the plan has changed since (`DayAheadPrices` endpoint, percentiles in the job summary) and has not run again | `Performance` workflow, artifact `jmeter-report` |

The Allure report of `main` holds the 152 tests of build #218. Live report with history: <https://magdau.github.io/eds-python-api-test-automation/>.

## 4. Test cases by level

| Level | Offline | Live | Total |
| --- | ---: | ---: | ---: |
| Component | 102 | 0 | 102 |
| Integration | 27 | 0 | 27 |
| System | 1 | 34 | 35 |
| **Total** | **130** | **34** | **164** |

The 34 live cases are 22 that run on every push to `main` and the 12 nightly data-quality checks. The one offline System case
proves the OpenAPI drift detector can fail. The suite has 121 test functions and BDD scenarios; the difference is parametrized runs.
Details in [test cases](test-cases.md).

## 5. Deviations from the plan

All planned triggers ran except `Mutation checks`, which has not run in Actions yet (first scheduled run: Monday 2026-11-02
04:00 UTC; the catalogue ran locally). No test was skipped or disabled. The 12 data-quality checks are left out of the run on
`main` on purpose. `main` was red twice (builds #154 and #158, one broken infrastructure test each; defects 11 and 12).

## 6. Defects and weaknesses found and resolved

Found by reviewing CI results and by auditing the tests and documentation against the strategy.

| # | Finding and impact | Resolved in |
| --- | --- | --- |
| 1 | A dependency missing from `requirements.txt` (build #76) made collection fail, yet an empty report was published and the Allure Trend dropped to 0 | PR #56: `--collect-only` step and publish guard |
| 2 | `urllib3>=1.26.9` allowed, but `backoff_jitter` exists only from 2.0: `TypeError` on client creation | PR #60: minimum `2.0.2` |
| 3 | The "retryable status" warning was unreachable (`urllib3` raises `RetryError`); its test passed only because the mock bypasses retries | PR #60: exhaustion is logged; tests use the local server |
| 4 | Fixtures used paths relative to the working directory | PR #60: resolved from the code's location |
| 5 | Tests repeated the mock, compared lower-cased queries, missed `Elspotprices`, and some live checks were weak (`status != 200`) | PR #61: assert the request sent, exact case, exact statuses; mutation checks added |
| 6 | A misspelled per-dataset retry setting was silently ignored | PR #64: `TypeError` for unknown settings |
| 7 | Live schema, sort and news tests passed on an empty result | PR #66: the schema helper rejects an empty list; live tests assert status and count |
| 8 | Allure categories wrong: any message with "429" (a port, `KeyError: 4290`) counted as infrastructure, a real `RetryError` as a test defect | PR #66: pattern fixed, guarded by `test_allure_categories.py` |
| 9 | Empty Categories views looked like missing data | PRs #69-#72: `Categories` line and `allure/report-notes.js`, verified in headless Chrome and on the published report |
| 10 | A dataset name went into the URL unencoded (`../News` gave `/dataset/../News`) | PR #75, test-first (`Red:`, `Green:`, `Refactor:`) |
| 11 | The client waited out any `Retry-After`, so a throttled run took about 5.5 minutes (10 of 20 builds) and the wait was invisible | PR #68 logs waits; PR #77 refuses above 60 s (`RetryAfterTooLongError`), verified live |
| 12 | Two queries per run to `Elspotprices`, which allows one per ~300 s: the second failed fast (builds #154, #158 red) | PR #81: one shared session-scoped query |
| 13 | EDS discontinued `Elspotprices` after 2025-09-30 while `active` stayed true; 5 live tests ran on frozen data | PRs #87 (metadata check), #88 (moved to `DayAheadPrices`), #89 (nightly data quality) |
| 14 | Eight tests could not fail, the live paging assertion passed with four shared records, only some live tests had a rerun | PR #86 |
| 15 | Documents contradicted the code (reruns, README structure, rate limit) | PR #83 |
| 16 | Schemas did not require `limit` and `dataset`; no live test checked that a filter returns only the requested values | PR #84 |
| 17 | `DatasetApi.records()` did not pass the query on (found because the mutation baseline failed) | PR #94 |
| 18 | Different query-argument order in `get_dataset` and `DatasetApi.get` (a positional call passed `filters` as `offset`), session not closable, a non-JSON body ended in a bare `JSONDecodeError` | PR #97: keyword-only arguments, `close()`/`with`, `InvalidResponseError`; three mutations |
| 19 | Known vulnerabilities in `requests` 2.32.3 and `pytest` 8.3.3 | PR #94: bumped to 2.33.0 and 9.0.3; `Security` workflow added |
| 20 | README said 203 tests, the suite had 154 | PR #95 |
| 21 | Duplicate and trivial tests | PR #96: ten removed after a kill matrix; all mutations still killed |
| 22 | Documents said EDS publishes no OpenAPI specification; it does, but it is thin | PR #98 (drift test) and a document refresh |
| 23 | A per-dataset retry override was mounted by URL prefix, so `CO2Emis` also served `CO2EmisProg` | PR #100: exact dataset URL, adapter closed with the client; two mutations |
| 24 | Documents listed boundary values no test used; `test-cases.md` numbered tests in random order | PR #100 and a document refresh; the generator uses source order |
| 25 | `news_url` did not encode its path, so a `/`, `?` or `#` could change what is requested (as defect 10 did for datasets); the README listed a "large" boundary value no test used | PR #104: encoded as one segment; one mutation (46 in all) |
| 26 | `Retry-After` as an HTTP date (not seconds) was untested | PR #104: two tests show the limit also works for a date |
| 27 | With jitter the logged wait differed from the wait that happened; a refused connection or timeout was not logged; live tests read the body before the status; a push to `main` and the nightly run could overlap; `urllib3` had no upper bound; an override was ignored when the base URL had capitals in the host | PR #106: backoff measured once, failures logged, status asserted first, one concurrency group (`eds-live-api`), `urllib3<3`, override key built from the URL as sent; three mutations (49 in all) |
| 28 | The CI checks ran only in CI, so a formatting or type error surfaced after the push; a commit with an AI co-author line or the private notes was possible | PR #105: pre-commit hooks run the same checks locally; PR #107: `ruff format --check` also in CI |

## 7. Residual risks and open items

- **The public API throttles by dataset; the limit of `DayAheadPrices` is not measured.** The discontinued `Elspotprices` allowed
  one query per ~300 s: 10 of the last 20 builds then took 324-326 s (the `Retry-After` was waited out) and 10 took 33-43 s.
  The wait is now refused after 60 s. A run on `main` sends one sorted query to `DayAheadPrices`, the nightly run one more; two
  local runs a few seconds apart both passed. If a limit exists, a second run within its window fails fast with
  `RetryAfterTooLongError` (Allure: *Infrastructure problems*). Options if it becomes a nuisance: skip these tests with an
  explicit reason when throttled, or run them only nightly.
- **The data-quality thresholds are first estimates** from one look at the live data on 2026-10-29; the 12 checks have passed once nightly.
- **External dependency.** Live tests depend on the public EDS API (availability, rate limits, contract changes, discontinued
  datasets). The nightly run detects this within a day; offline tests keep gating changes.
- **Untested areas and the thin specification:** see [test coverage](test-coverage.md#6-known-gaps).
- **CI stability.** Of 218 `Tests` runs, 10 did not succeed (5%): six in the first days (causes not examined), two on 23 October
  (defect 1) and two on 28 October (defect 12); the latest 60 (#159-#218) all succeeded. None was a failed assertion about the product.
- **Process.** At least 26 pull requests (#61 to #98) were merged 19-49 seconds before their `Tests` run finished (GitHub API,
  2026-10-29 and 2026-10-30). CI was green each time, but nothing enforces the wait; branch protection requiring `Tests` and
  `Quality` would.
- **Not yet run in Actions:** the JMeter plan since it moved to `DayAheadPrices` (no percentile limits yet, see
  [test architecture](test-architecture.md#4-performance-acceptance)), `Mutation checks` (local run on 2026-10-30: all 49 caught),
  and the nightly run with `requests` 2.33.0 and `pytest` 9.0.3 (passed in builds #187 and #218; first nightly: 2026-10-31).
  The CI publish-guard simulation is not repeated automatically.
- **Scheduled runs start late.** The cron of `Live nightly` is 02:00 UTC, but GitHub started the last seven runs between 06:57
  and 08:14 UTC. Plan around the date, not the hour.

## 8. How this report is kept current

`test-cases.md` and `test-results.md` are generated (`scripts/generate_test_cases.py`, `scripts/generate_test_results.py`).
This report, the strategy, the plan and the coverage document are edited by hand: update the results, the date and the commit
above when a new report is needed.

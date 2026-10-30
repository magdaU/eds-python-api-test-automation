# Test strategy

How this project tests the [Energi Data Service (EDS)](https://www.energidataservice.dk/) API and its own client library.
Related documents: [test plan](test-plan.md) · [test cases](test-cases.md) · [test coverage](test-coverage.md) ·
[test results](test-results.md) · [test report](test-report.md) · [test architecture](test-architecture.md).

Terminology follows ISTQB.

## 1. Objectives

1. Detect regressions in the API client (`client/`, `models/`) quickly and deterministically, on every pull request.
2. Detect drift in the real EDS API (changed fields, statuses or error messages) within a day.
3. Keep the load on a public, rate-limited API minimal and predictable.
4. Make results visible and trustworthy: one report with history, no misleading numbers.

## 2. Scope

| In scope | Out of scope |
| --- | --- |
| Dataset endpoints `CO2Emis` and `DayAheadPrices`: `limit`, `offset`, `sort`, `filter` | Other EDS datasets, parameters the client does not expose (`start`, `end`, `columns`, `timezone`), endpoints it does not call (`/dataset/{name}/download`, `/meta/*` lists) |
| News endpoints `/News`, `/News/actual`, `/News/calendar`, `/News/archived` | Correctness of the energy data values against an authoritative source |
| Client behaviour: URL building, retry with backoff, timeout, logging, error handling | Security testing of the API (public, unauthenticated), TLS testing |
| Response contract: JSON Schema, Pydantic models, typed records, unexpected bodies; drift of the published OpenAPI specification | Stress, soak and spike testing |
| Low-load performance baseline (JMeter); known vulnerabilities in dependencies and committed secrets | Browsers, UI, other Python versions or operating systems in CI |

**Test basis.** EDS publishes an OpenAPI 3.0.1 specification (`/swagger/public/swagger.json`, 15 GET operations, no
authentication), but it is thin: it declares only status 200 (no 204, 400, 404 or 429), the main `/dataset/{datasetName}`
operation has no response schema, and `limit` and `offset` are plain integers without a minimum (`limit=-1` returns the
whole dataset). The response contract was therefore observed on the live API and recorded in JSON Schemas
([`schemas/`](../schemas)) and in the [ROADMAP](../ROADMAP.md) (item 12). The **test oracle** is that observed contract,
the operations and parameters the specification does document, and the documented behaviour of the client.
A live drift test (`test_openapi_drift`) fails when the specification stops documenting an operation or parameter the client
uses. Schemathesis is not used: with only status 200 declared every real error response would count as a violation, and
unbounded `limit` and `offset` values would load the public API heavily.

One assumption could change without notice: the [EDS API guide](https://www.energidataservice.dk/guides/api-guides)
documents HTTP 429 with a message in the body but no `Retry-After` header, which the real API has been observed to send.
The client and the retry tests rely on it. If EDS stops sending it, the client falls back to its own backoff and the live
runs show it as slower or throttled, not as a failed assertion.

## 3. Test levels

| Level | What it checks | Environment / test double | Runs |
| --- | --- | --- | --- |
| Component | Client methods, parameter handling, parsing, configuration | `requests-mock` or none | every PR, every push to `main` |
| Integration | The client's real HTTP stack (`requests`, `urllib3`, retry adapter) | Scripted HTTP server on `127.0.0.1` | every PR, every push to `main` |
| System | The client against the real public EDS API | Public API, one small request per test | push to `main`, nightly |
| Non-functional | Latency and error rate under light concurrency | JMeter against the public API | manually and weekly |

`requests-mock` replaces the transport, so the retry adapter never runs against a mocked response. Everything that depends
on retries, status handling after retries or real connection errors therefore runs against the scripted local server
(`tests/support/scripted_server.py`). Test counts per level are in [test-cases.md](test-cases.md).

## 4. Test types and design techniques

| Test type | Technique | Where |
| --- | --- | --- |
| Functional, black-box | Equivalence partitioning (filter values, URL variants, record validity) | `test_filter_encoding`, `test_models`, `test_url_building`, `test_schema_validation` |
| Functional, black-box | Boundary value analysis (`limit`: negative, 0, 1; `offset`: negative, 0; the `int32` upper bound is not tested) | `test_boundary_values` |
| Functional, black-box | Decision table (combinations of the four optional parameters) | `test_parameter_combinations` |
| Functional, black-box | Property-based testing (`hypothesis`) | `test_properties` |
| Negative testing, error guessing | Invalid input, unknown paths and columns, timeouts, refused connections, persistent 5xx | `test_retry_behavior`, `test_live_edge_cases` |
| Contract testing | JSON Schema validation of samples and live responses | `test_schema_validation`, `test_dataset_contract`, `test_news_api` |
| Contract testing | OpenAPI drift: the operations and parameters the client uses are still documented (an offline test proves the detector reports a missing path, parameter and wrong type) | `test_openapi_drift` |
| Smoke testing | One bounded call per area against the live API | `test_live_smoke` |
| Data-quality monitoring | The 100 newest records of `CO2Emis` and `DayAheadPrices`: freshness, gaps, DK1/DK2, Danish time against UTC (daylight saving), value range; one query per series | `test_live_data_quality` (marker `data_quality`, nightly only) |
| Structural (white-box) | Statement and branch coverage of `client/` and `models/`; gate at 90% | `pytest --cov` |
| Static analysis | `ruff` and `mypy` in strict mode | `quality.yml` |
| Security | Known vulnerabilities in pinned dependencies (`pip-audit`) and secrets in tracked files (`detect-secrets`); also weekly | `security.yml` |
| Independence | `pytest-randomly` shuffles the test order on every run | pytest plugin |
| Performance | Low-load baseline: 2 users, every sample 200 and within 2000 ms; p50/p95/p99 reported, not yet enforced (see [test architecture](test-architecture.md#4-performance-acceptance)) | `performance/`, `performance.yml` |

### Executable specifications (BDD)

A few behaviours worth reading as a specification are written as Gherkin scenarios in
[`tests/bdd/features/`](../tests/bdd/features) and run with `pytest-bdd`: which query parameters reach the API, what the
client does when the API throttles or fails, and how News parameters are sent. The step definitions
([`tests/bdd/conftest.py`](../tests/bdd/conftest.py)) reuse the API objects, `requests-mock` and the scripted server, so a
scenario exercises the same code as every other test.

- A scenario states one behaviour in the vocabulary of the API (dataset, limit, retry), not of the code.
- Scenarios are offline and deterministic. Bulk edge cases, property-based tests and live checks stay in plain pytest.
- [test-cases.md](test-cases.md) is generated from the feature files, so the specification and the catalogue cannot drift apart.

BDD is not applied everywhere on purpose: there are no business stakeholders to write scenarios with, and a scenario layer
on every test would only add indirection.

## 5. Test design principles

- **Name and structure.** Tests are named `givenX_whenY_thenZ` (or `whenY_thenZ`) and have the sections `# arrange`,
  `# act`, `# assert`. An empty section is left out (live tests have no arrange), and act and assert are combined as
  `# act / assert` around `pytest.raises`. Names read as test cases, which is why [test-cases.md](test-cases.md) is generated from them.
- **Test the system, not the double.** A mocked test asserts what the client *sent* (path, parameters with exact case),
  not what the mock returns. Tests that only echoed the mock were removed.
- **Independent and deterministic.** No test depends on another, on order or on time. Only live tests depend on an external system.
- **Every test earns its place.** A test that repeats another and kills no mutation is removed. A kill matrix (one run per
  mutation, no `-x`) showed ten such cases on 2026-10-30; the suite went from 154 to 144 tests and still killed every
  mutation. A test that kills nothing is not removed blindly: either a mutation for the behaviour it protects is missing
  (then add it) or the test is redundant.
- **One reason to fail.** Mapping tests assert every attribute and use distinct values per attribute so swapped fields are detected.
- **Test first where it pays (TDD).** For offline client logic that is cheap to specify, the test is written first and must
  fail for the right reason: *red* (committed on its own), *green*, *refactor*. The URL-encoding of dataset names is the
  worked example (commits `Red:`, `Green:`, `Refactor:`; the `Red:` commit fails on purpose, so only the head of a pull
  request is expected to be green). TDD is not forced on live tests, the Allure script or documentation.
- **Diagnosable failures.** The client logs one line per request (URL, parameters, status, duration including retry waits,
  the start of an error body) and the wait before each retry with its reason. Allure attaches these logs, so a failed or
  slow live test explains itself.
- **Reports explain themselves.** An empty widget must not read as missing data: the Allure report says why the Categories
  widgets are empty (`allure/report-notes.js`), but only when its own data confirms it.
- **No vacuous passes.** A test that validates items first proves there are items: the schema helper rejects an empty list,
  and live tests assert that records arrived. A check that can only pass against live data gets an offline test that proves
  it can fail (the OpenAPI drift detector).
- **Severity.** Each module carries an Allure severity through `labels(epic, feature, severity)`: `critical` for retry,
  contract, schemas and models; `minor` for test tooling and logs; `normal` otherwise.
- **Mock-first, live-bounded.** Edge cases and error paths are proven offline. Live tests are smoke checks and a few edge
  cases, each one `limit=1` request with a pause between requests. `limit=-1` is never sent live: the API treats it as
  "no limit" and returns millions of records.
- **Tolerate only transient failures.** Live tests (all marked flaky) rerun only on network errors (`ConnectionError`,
  `Timeout`, `RetryError`), never on assertion failures, so a real defect is not hidden.
- **Path-independent fixtures.** Mocks and schemas are located relative to the code, so tests run from any directory.

## 6. Test data

| Data | Source | Notes |
| --- | --- | --- |
| Sample responses | `tests/mocks/*.json`, hand-built | Validated against the JSON Schemas so samples cannot drift from the contract |
| Generated inputs | `hypothesis` strategies | 100 examples per property |
| OpenAPI specification | Public EDS API (`/swagger/public/swagger.json`) | Read-only, fetched once per live run, not stored |
| Live data | Public EDS API | Read-only; asserted only on shape, order and error messages, never on specific values |

## 7. Environments and tools

| | |
| --- | --- |
| Python | 3.12 (local, Docker `python:3.12-slim`, CI on `ubuntu-latest`) |
| Test framework | `pytest`, `pytest-bdd`, `requests-mock`, `hypothesis`, `pytest-rerunfailures`, `pytest-randomly`, `pytest-cov` |
| Contract | `jsonschema`, `pydantic` |
| Reporting | Allure (published to GitHub Pages) |
| Static analysis / security | `ruff`, `mypy` (strict), `pip-audit`, `detect-secrets` |
| Performance | Apache JMeter 5.6.3 |
| Packaging | `Dockerfile` (offline tests by default, non-root) |

## 8. Execution schedule and CI

| Workflow | Trigger | Content |
| --- | --- | --- |
| `Tests` | pull request to `main` | Offline tests only (`-m "not live"`), Allure results as artifact |
| `Tests` | push to `main` | All tests including live (and the OpenAPI drift test) except data quality (`-m "not data_quality"`); Allure report published to GitHub Pages |
| `Quality` | pull request, push to `main` | `ruff`, `ruff format --check`, `mypy`, offline tests with the coverage gate |
| `Security` | pull request, push to `main`, Monday 05:00 UTC, manual | `pip-audit` and `detect-secrets`; fails on any finding |
| `Live nightly` | daily cron 02:00 UTC (GitHub started the last seven runs between 06:57 and 08:14 UTC), manual | Live tests only, including data quality, to catch API drift and stale or broken data. No Allure report: the result is the run itself |
| `Performance` | Monday 03:00 UTC, manual | JMeter plan, fails on any failed sample |
| `Mutation checks` | Monday 04:00 UTC, manual | 49 deliberate breakages of the client, models and schemas; fails when the offline tests miss one (about 7 minutes, report in the job summary) |

The `Tests` workflow publishes the Allure report only when pytest exits with 0 or 1 and results exist, so a broken run
cannot reset the Trend history.

## 9. Entry and exit criteria

**Entry:** the change is on a feature branch and a pull request is open.

**Exit (may be merged), enforced by CI:** `Tests` and `Quality` pass; `ruff` and `mypy --strict` report nothing; `Security`
reports no known vulnerability and no committed secret; coverage of `client/` and `models/` is at least 90% (currently 100%
line and branch). By convention: no test is skipped or marked as an expected failure to make a run pass (none is today).

**Exit (`main` is healthy):** the full run on `main` and the nightly live run pass, and the Allure report shows no failed or broken test.

## 10. Risk-based prioritisation

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| EDS API changes a field, status or message | Medium | Live tests fail, schemas outdated | Nightly live run (its result is the Actions run), JSON Schemas, the OpenAPI drift test; on `main` the Allure *Contract drift* category |
| Public API rate limiting (429) | Medium | Flaky live tests, blocked client | Few and small live requests, retry with backoff, rerun on network errors only; 429 is never triggered on purpose |
| 429 with a long `Retry-After` (up to 300 s observed). Before the limit existed the client waited it out, so a full run took about 5 minutes instead of 30 seconds (see the [test report](test-report.md#7-residual-risks-and-open-items)) | High | Slow feedback, job near its timeout; now a throttled live fixture fails fast | The client refuses a `Retry-After` above 60 s (`RetryConfig.max_retry_after`) with `RetryAfterTooLongError` (Allure: *Infrastructure problems*); the wait and its reason are logged; job timeout 30 minutes. Measured for the discontinued `Elspotprices`: one query per ~300 s. The limit of `DayAheadPrices` is not measured, so a run sends exactly one query to it; a second run within five minutes could be throttled and fails fast. A push to `main` and `Live nightly` share the concurrency group `eds-live-api`, so two live runs never overlap; a pull request runs offline tests only and does not wait |
| Retry logic is wrong but untested | Medium | Hammering the API, or silent failures | Retry behaviour tested against a real local server, not only mocks |
| Tests pass although the client is broken | Medium | False confidence | Mutation checks (49), the kill matrix, request-based assertions; coverage is not trusted alone (see [test coverage](test-coverage.md)) |
| Report shows misleading history | Low | Wrong decisions | Publish guard in CI, Allure categories |
| Dependency changes break the suite | Medium | Red build | Pinned versions; a changed minimum version is verified in a clean environment |
| A pinned dependency has a known vulnerability | Medium | Vulnerable environment | `pip-audit` on every pull request and weekly. On 2026-10-30 it flagged `requests` 2.32.3 and `pytest` 8.3.3; both were bumped after the offline suite, `mypy` and coverage passed on the new versions |

## 11. Defect management

Failures are triaged through Allure categories (*Infrastructure problems*, *Contract drift*, *Product defects*,
*Test defects*, *Skipped tests*). A defect is fixed on a branch with a regression test, merged through a pull request and
recorded in the [test report](test-report.md). With no separate issue tracker, the pull request is the defect record.

## 12. Metrics and reporting

Pass rate, trend, duration and retries are in the [Allure report](https://magdau.github.io/eds-python-api-test-automation/);
test counts in [test-cases.md](test-cases.md); coverage in [test-coverage.md](test-coverage.md); one run in
[test-results.md](test-results.md); summary, defects and risks in [test-report.md](test-report.md).

## 13. Test maintenance

- Regenerate [test-cases.md](test-cases.md) (`python scripts/generate_test_cases.py`) after changing tests, and
  [test-results.md](test-results.md) (`python scripts/generate_test_results.py`) when a new report is needed.
- Guard against the *pesticide paradox*: when client behaviour changes, check by a quick mutation that at least one test
  fails. `scripts/mutation_check.py` does this for 49 known changes every week; add a mutation when a new client behaviour
  is protected by a test, and update a mutation's line when the client line it names changes (otherwise the run reports `STALE`).
- Before removing a test, build the kill matrix (which test fails for which mutation, no `-x`, fixed order) and check what
  the test protects; do not edit tests while it runs, because the mutations change the client files.
- Coverage is an indicator, never a goal: 100% does not show that assertions are strong enough.

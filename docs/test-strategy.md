# Test strategy

How this project tests the [Energi Data Service (EDS)](https://www.energidataservice.dk/) API and its own client library.
Related documents: [test plan](test-plan.md) · [test cases](test-cases.md) · [test coverage](test-coverage.md) ·
[test results](test-results.md) · [test report](test-report.md).

Terminology follows ISTQB.

## 1. Objectives

1. Detect regressions in the API client (`client/`, `models/`) quickly and deterministically, on every pull request.
2. Detect drift in the real EDS API (changed fields, statuses or error messages) within a day.
3. Keep the load on a public, rate-limited API minimal and predictable.
4. Make results visible and trustworthy: one report with history, no misleading numbers.

## 2. Scope

| In scope | Out of scope |
| --- | --- |
| Dataset endpoints `CO2Emis` and `Elspotprices`: `limit`, `offset`, `sort`, `filter` | Other EDS datasets and query parameters the client does not expose (for example `start`, `end`, `columns`, `timezone`) |
| News endpoints `/News`, `/News/actual`, `/News/calendar`, `/News/archived` | Correctness of the energy data values against an authoritative source |
| Client behaviour: URL building, retry with backoff, timeout, logging, error handling | Security testing (the API is public and unauthenticated), TLS testing |
| Response contract: JSON Schema and Pydantic models | Stress, soak and spike testing |
| Low-load performance baseline (JMeter) | Browsers, UI, other Python versions or operating systems in CI |

**Test basis.** EDS publishes no OpenAPI/Swagger specification for these endpoints. The contract was therefore observed on
the live API and recorded in JSON Schemas ([`schemas/`](../schemas)) and in the [ROADMAP](../ROADMAP.md) (item 12).
The **test oracle** is that observed contract plus the documented behaviour of the client.

Where observation goes beyond the [EDS API guide](https://www.energidataservice.dk/guides/api-guides), the tests rest on an
assumption that EDS could change without notice. The main one: the guide documents only HTTP 429 with the message
"Rate limit is exceeded. Try again in X seconds" in the body, and does not mention a `Retry-After` header. The client and the
retry tests rely on that header, because the real API has been observed to send it. If EDS stops sending it, the client falls
back to its own backoff and the live runs show it as slower or throttled, not as a failed assertion.

## 3. Test levels

| Level | What it checks | Environment / test double | Runs |
| --- | --- | --- | --- |
| Component | Client methods, parameter handling, parsing, configuration | `requests-mock` or none | every PR, every push to `main` |
| Integration | The client's real HTTP stack (`requests`, `urllib3`, retry adapter) | Scripted HTTP server on `127.0.0.1` | every PR, every push to `main` |
| System | The client against the real public EDS API | Public API, one small request per test | push to `main`, nightly |
| Non-functional | Latency and error rate under light concurrency | JMeter against the public API | manually and weekly |

Why two kinds of test double: `requests-mock` replaces the transport, so the retry adapter never runs against a mocked
response. Everything that depends on retries, status handling after retries, or real connection errors therefore runs
against the scripted local server instead. See `tests/support/scripted_server.py`.

The number of test cases per level is in [test-cases.md](test-cases.md).

## 4. Test types and design techniques

| Test type | Technique | Where |
| --- | --- | --- |
| Functional, black-box | Equivalence partitioning (filter values, URL variants, record validity) | `test_filter_encoding`, `test_models`, `test_url_building`, `test_schema_validation` |
| Functional, black-box | Boundary value analysis (`limit`: 0, 1, 2, 100000, negative; `offset`: 0, 1, 100000, negative) | `test_boundary_values` |
| Functional, black-box | Decision table (combinations of the four optional parameters) | `test_parameter_combinations` |
| Functional, black-box | Property-based testing (invariants for arbitrary inputs, via `hypothesis`) | `test_properties` |
| Negative testing, error guessing | Invalid input, unknown paths and columns, timeouts, refused connections, persistent 5xx | `test_negative_scenarios`, `test_retry_behavior`, `test_live_edge_cases` |
| Contract testing | JSON Schema validation of samples and live responses | `test_schema_validation`, `test_dataset_contract`, `test_news_api` |
| Smoke testing | One bounded call per area against the live API | `test_live_smoke` |
| Structural (white-box) | Statement coverage of `client/` and `models/` (gate at 90%), branch coverage measured on demand | `pytest --cov` |
| Static analysis | `ruff` (style, bugs, complexity) and `mypy` in strict mode | `quality.yml` |
| Performance | Low-load baseline with a response-time assertion | `performance/`, `performance.yml` |

### Executable specifications (BDD)

A small set of behaviours is written as Gherkin scenarios in [`tests/bdd/features/`](../tests/bdd/features) and run with
`pytest-bdd`. They exist for behaviour that is worth reading as a specification: which query parameters reach the API,
what the client does when the API throttles or fails, and how News parameters are sent. Step definitions
([`tests/bdd/conftest.py`](../tests/bdd/conftest.py)) reuse the API objects, `requests-mock` and the scripted local server,
so a scenario exercises the same code as every other test.

- A scenario states one behaviour and its steps use the vocabulary of the API (dataset, limit, retry), not of the code.
- Scenario Outlines are used for data variants; tags would select subsets (`@live` would map to the `live` marker).
- Scenarios are offline and deterministic. Bulk edge cases, property-based tests and live checks stay in plain pytest, where
  they are shorter and clearer.
- [test-cases.md](test-cases.md) is generated from the feature files for these scenarios, so the specification and the
  catalogue cannot drift apart.

BDD is not applied everywhere on purpose: the project has no business stakeholders to write scenarios with, and
a scenario layer on every test would only add indirection.

## 5. Test design principles

- **Name and structure.** Tests are named `givenX_whenY_thenZ` (or `whenY_thenZ`) and have the sections `# arrange`,
  `# act`, `# assert`. A section is left out when it would be empty (live tests have no arrange), and act and assert are
  combined as `# act / assert` around `pytest.raises`. A test name reads as a test case, which is why [test-cases.md](test-cases.md) is generated from them.
- **Test the system, not the double.** A mocked test must assert what the client *sent* (path, parameters with exact
  case), not what the mock returns. Tests that only echo the mock were removed because they cannot fail when the client
  breaks.
- **Independent and deterministic.** No test depends on another, on execution order or on time. Live tests are the only
  ones that depend on an external system.
- **One reason to fail.** A test asserts one behaviour; mapping tests assert every attribute and use distinct values per
  attribute so that swapped fields are detected.
- **Test first where it pays (TDD).** For client logic that runs offline and is cheap to specify, the test is written
  first and must fail for the right reason before any production code changes: *red* (a failing test, committed on its own),
  *green* (the smallest change that passes), *refactor* (tidy up with the tests untouched and green). The change that made
  dataset names URL-encoded is the worked example: its history is the three commits `Red:`, `Green:` and `Refactor:`
  (the `Red:` commit fails on purpose, so only the head of a pull request is expected to be green). TDD is not forced on live
  tests, the Allure report script or documentation, where there is no way to write the failing test first.
- **Diagnosable failures.** The client logs one line per request (URL, parameters, status, duration including retry waits,
  the start of an error body) and the wait before each retry with its reason. pytest captures these logs, including those of
  fixtures, and Allure attaches them to the test, so a failed or slow live test explains itself.
- **Reports explain themselves.** An empty widget must not read as missing data: the Allure report states why the Categories
  widgets are empty (`allure/report-notes.js`), but only when the report's own data confirms it.
- **No vacuous passes.** A test that validates items must first prove that there are items: the schema helper rejects
  an empty list, and live tests assert that records arrived (for example five records for `limit=5`).
- **Mock-first, live-bounded.** Edge cases and error paths are proven offline. Live tests are limited to smoke checks
  and a few edge cases. Edge-case tests send one `limit=1` request each, with a pause between requests. `limit=-1` is never sent live:
  the API treats it as "no limit" and returns millions of records.
- **Tolerate only transient failures.** The live tests (all of them are marked flaky)
  rerun (`pytest-rerunfailures`) only on network errors (`ConnectionError`, `Timeout`, `RetryError`), never on assertion
  failures, so a real defect is not hidden by a rerun.
- **Fixtures are path-independent.** Mocks and schemas are located relative to the code, so tests run from any directory.

## 6. Test data

| Data | Source | Notes |
| --- | --- | --- |
| Sample responses | `tests/mocks/*.json`, hand-built | Validated against the JSON Schemas so that the samples cannot drift away from the contract |
| Generated inputs | `hypothesis` strategies | 100 examples per property |
| Live data | Public EDS API | Read-only; never asserted on specific values, only on shape, order and error messages |

## 7. Environments and tools

| | |
| --- | --- |
| Python | 3.12 (local, Docker `python:3.12-slim`, CI) |
| CI | GitHub Actions, `ubuntu-latest` |
| Test framework | `pytest`, `requests-mock`, `hypothesis`, `pytest-rerunfailures`, `pytest-cov` |
| Contract | `jsonschema`, `pydantic` |
| Reporting | Allure (published to GitHub Pages) |
| Static analysis | `ruff`, `mypy` (strict) |
| Performance | Apache JMeter 5.6.3 |
| Packaging | `Dockerfile` (runs the whole suite) |

## 8. Execution schedule and CI

| Workflow | Trigger | Content |
| --- | --- | --- |
| `Tests` | pull request to `main` | Offline tests only (`-m "not live"`), Allure results as artifact |
| `Tests` | push to `main` | All tests including live, Allure report published to GitHub Pages |
| `Quality` | pull request, push to `main` | `ruff`, `mypy`, offline tests with the coverage gate |
| `Live nightly` | daily 02:00 UTC, manual | Live tests only, to catch API drift. No Allure report: the result is the workflow run itself |
| `Performance` | Monday 03:00 UTC, manual | JMeter plan, fails on any failed sample |

A guard in the `Tests` workflow publishes the Allure report only when pytest exits with code 0 or 1 and results exist,
so an empty or broken run cannot reset the Trend history.

## 9. Entry and exit criteria

**Entry (a change is tested):** the change is on a feature branch and a pull request is open.

**Exit (a change may be merged), enforced by CI:**

- `Tests` and `Quality` pass on the pull request.
- `ruff` and `mypy --strict` report no findings.
- Line coverage of `client/` and `models/` is at least 90% (currently 100% line and branch).

By convention, not enforced: no test is skipped or marked as an expected failure to make a run pass. The one exception is deliberate: the metadata test for the discontinued `Elspotprices` dataset is a strict `xfail` (it must fail while EDS publishes no new data, and flags itself as soon as that changes).

**Exit (a state of `main` is healthy):** the full run on `main` including live tests passes, the nightly live run passes, and
the Allure report shows no failed or broken test.

## 10. Risk-based prioritisation

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| EDS API changes a field, status or message | Medium | Live tests fail, schemas outdated | Nightly live run (its result is the Actions run, not an Allure report), JSON Schemas; on `main` runs the Allure *Contract drift* category |
| Public API rate limiting (429) | Medium | Flaky live tests, blocked client | Few and small live requests, retry with backoff, rerun on network errors only, 429 is never triggered on purpose |
| The public API answers 429 with a long `Retry-After` (up to 300 s observed). Before the limit existed the client waited it out, so a full run took about 5 minutes instead of 30 seconds (see the [test report](test-report.md#7-residual-risks-and-open-items)) | High | Slow feedback, job near its timeout; since the limit, a throttled live fixture fails fast instead | The client refuses a `Retry-After` above 60 s (`RetryConfig.max_retry_after`) with `RetryAfterTooLongError`, which Allure files under *Infrastructure problems*; the wait and its reason are logged; job timeout of 30 minutes. Measured: `Elspotprices` answers one query per ~300 s window, so a test run sends exactly one query to it, shared by the live tests; a second run within five minutes can still be throttled and fails fast |
| Retry logic is wrong but untested | Medium | Hammering the API, or silent failures | Retry behaviour tested against a real local server, not only mocks |
| Tests pass although the client is broken | Medium | False confidence | Mutation checks, request-based assertions, coverage is not trusted alone (see [test coverage](test-coverage.md)) |
| Report shows misleading history | Low | Wrong decisions | Publish guard in CI, Allure categories |
| Dependency changes break the suite | Medium | Red build | Pinned versions; a changed minimum version is verified in a clean environment |

## 11. Defect management

Failures are triaged through Allure categories (*Infrastructure problems*, *Contract drift*, *Product defects*,
*Test defects*, *Skipped tests*). A defect is fixed on a branch with a regression test, merged through a pull request
and recorded in the [test report](test-report.md). Because the project has no separate issue tracker, the pull request
is the defect record.

## 12. Metrics and reporting

| Metric | Source |
| --- | --- |
| Pass rate, trend, duration, retries | [Allure report](https://magdau.github.io/eds-python-api-test-automation/) |
| Test counts per level | [test-cases.md](test-cases.md) |
| Statement and branch coverage | [test-coverage.md](test-coverage.md) |
| Results of one run | [test-results.md](test-results.md) |
| Summary, defects, risks | [test-report.md](test-report.md) |

## 13. Test maintenance

- Regenerate [test-cases.md](test-cases.md) (`python scripts/generate_test_cases.py`) after changing tests, and
  [test-results.md](test-results.md) (`python scripts/generate_test_results.py`) when a new report is needed.
- Guard against the *pesticide paradox*: when client behaviour changes, check by a quick mutation (remove or change one
  line of the client) that at least one test fails.
- Coverage numbers are an indicator, never a goal: 100% coverage does not show that assertions are strong enough.

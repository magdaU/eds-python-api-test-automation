# Test strategy

How this project tests the [Energi Data Service (EDS)](https://www.energidataservice.dk/) API and its own client library.
Related documents: [test plan](test-plan.md) · [test cases](test-cases.md) · [test coverage](test-coverage.md) ·
[test results](test-results.md) · [test report](test-report.md) · [test architecture](test-architecture.md).

Terminology follows ISTQB.

## 1. Objectives

1. Detect regressions in the API client (`client/`, `models/`) quickly and deterministically, on every pull request.
2. Keep the load on the public EDS API at zero for automated runs: no workflow sends requests to it. The live tests are
   kept and can be run by hand to check the real API (section 8.1).
3. Keep the framework itself demonstrable: test design, the client, reporting and CI are all runnable from the repository.
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
authentication), but it is thin: only status 200 is declared, `/dataset/{datasetName}` has no response schema, and `limit`
and `offset` are plain integers without a minimum (`limit=-1` returns the whole dataset). The response contract was therefore
observed on the live API and recorded in the JSON Schemas ([`schemas/`](../schemas)) and in the [ROADMAP](../ROADMAP.md)
(item 12). The **test oracle** is that contract, what the specification does document, and the documented behaviour of the
client. The drift detector (`test_openapi_drift`) checks that the operations and parameters the client uses are still documented
in the specification. It runs offline on inline specifications; the published specification is fetched only when the live
tests are run by hand. Schemathesis is not used: with only 200 declared every real error would count as a violation, and unbounded
`limit` and `offset` would load the public API.

One assumption could change without notice: the [EDS API guide](https://www.energidataservice.dk/guides/api-guides) documents
429 without a `Retry-After` header, which the real API has been observed to send. If it stops, the client falls back to its
own backoff and the live runs show it as slower or throttled, not as a failed assertion.

## 3. Test levels

| Level | What it checks | Environment / test double | Runs |
| --- | --- | --- | --- |
| Component | Client methods, parameter handling, parsing, configuration | `requests-mock` or none | every PR, every push to `main` |
| Integration | The client's real HTTP stack (`requests`, `urllib3`, retry adapter) | Scripted HTTP server on `127.0.0.1` | every PR, every push to `main` |
| System | The client against the real public EDS API | Public API, one small request per test | Not run by any workflow. Run by hand when the live tests are enabled (section 8.1) |
| Non-functional | Latency and error rate under light concurrency | JMeter against the public API | manually only (section 8.1) |

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
| Negative testing, error guessing | Invalid input, timeouts, refused connections, persistent 5xx | `test_retry_behavior`, `test_eds_client` |
| Contract testing | JSON Schema validation of samples | `test_schema_validation`, `test_dataset_contract`, `test_news_api` |
| Contract testing | OpenAPI drift: the operations and parameters the client uses are still documented (an offline test proves the detector reports a missing path, parameter and wrong type) | `test_openapi_drift` |
| Smoke testing | One bounded call per area against the live API. No such test exists in the repository now; the `live` marker stays registered in `pytest.ini` so the tests can be added back (section 8.1) | none |
| Data-quality monitoring | Checks on the newest records of `CO2Emis` and `DayAheadPrices`. No such test exists in the repository now; the `data_quality` marker stays registered in `pytest.ini` (section 8.1) | none |
| Structural (white-box) | Statement and branch coverage of `client/` and `models/`; gate at 90% | `pytest --cov` |
| Static analysis | `ruff` and `mypy` in strict mode | `quality.yml` |
| Security | Known vulnerabilities in pinned dependencies (`pip-audit`) and secrets in tracked files (`detect-secrets`); also weekly | `security.yml` |
| Independence | `pytest-randomly` shuffles the test order on every run | pytest plugin |
| Performance | Low-load baseline: 2 users, every sample 200 and within 2000 ms; p50/p95/p99 reported, not yet enforced (see [test architecture](test-architecture.md#4-performance-acceptance)) | `performance/`, `performance.yml` |

### Executable specifications (BDD)

A few behaviours worth reading as a specification are Gherkin scenarios in [`tests/bdd/features/`](../tests/bdd/features),
run with `pytest-bdd`: which query parameters reach the API, what the client does when the API throttles or fails, and how
News parameters are sent. Their steps ([`tests/bdd/conftest.py`](../tests/bdd/conftest.py)) reuse the API objects,
`requests-mock` and the scripted server, so a scenario exercises the same code as every other test. Scenarios are offline,
state one behaviour in the vocabulary of the API, and [test-cases.md](test-cases.md) is generated from the feature files.
BDD is not applied everywhere on purpose: there are no business stakeholders to write scenarios with, and a scenario layer
on every test would only add indirection.

## 5. Test design principles

- **Name and structure.** Tests are named `givenX_whenY_thenZ` (or `whenY_thenZ`) with the sections `# arrange`, `# act`,
  `# assert` (an empty one is left out; `# act / assert` around `pytest.raises`), so names read as test cases and
  [test-cases.md](test-cases.md) can be generated from them.
- **Test the system, not the double.** A mocked test asserts what the client *sent* (path, parameters with exact case), not
  what the mock returns. Independent and deterministic: no test depends on another, on order or on time; only live tests
  depend on an external system.
- **Every test earns its place.** A test that repeats another and kills no mutation is removed; a kill matrix on 2026-10-30
  found ten such cases (154 to 144 tests, every mutation still killed). A test that kills nothing is not removed blindly:
  either a mutation for the behaviour it protects is missing (add it) or the test is redundant.
- **One reason to fail.** Mapping tests assert every attribute and use distinct values per attribute so swapped fields are detected.
- **Test first where it pays (TDD).** For offline client logic that is cheap to specify, the failing test comes first (*red*,
  committed on its own, then *green*, then *refactor*); the URL-encoding of dataset names is the worked example (commits
  `Red:`, `Green:`, `Refactor:`; only the head of a pull request is expected to be green). Not forced on live tests, the Allure
  script or documentation.
- **Diagnosable failures.** The client logs one line per request (URL, parameters, status, duration, the start of an error
  body) and each retry wait with its reason; Allure attaches the log to the test. Reports explain themselves too: an empty
  widget must not read as missing data (`allure/report-notes.js`).
- **No vacuous passes.** A test that validates items first proves there are items: the schema helper rejects an empty list,
  and live tests assert that records arrived. A check that can only pass against live data gets an offline test that proves
  it can fail (the OpenAPI drift detector).
- **Severity.** Each module carries an Allure severity via `labels(epic, feature, severity)`: `critical` for retry, contract,
  schemas and models; `minor` for test tooling and logs; `normal` otherwise.
- **Offline by default.** The suite runs without network access: mocks and the local scripted server. No test currently
  sends a request to the public API. Live tests are a separate, manual option (section 8.1).
- **Rules for live tests, if they are enabled.** Rerun only on network errors (`ConnectionError`, `Timeout`), never on
  assertion failures or on throttling. A throttled test (`RetryAfterTooLongError`) is skipped with its reason, not failed.
  All waits of one run share a budget of 120 s (`wait_budget` of `EDSApiClient`, set in `tests/support/live.py`), and each
  test has a 120 s timeout (`pytest-timeout`). The offline tests keep the client defaults. Mocks and schemas are located
  relative to the code, so tests run from any directory.

## 6. Test data

Sample responses (`tests/mocks/*.json`) are hand-built and validated against the JSON Schemas so they cannot drift from the
contract; `hypothesis` generates 100 examples per property; the OpenAPI specification is fetched read-only once per live
run. Live data is read-only and asserted only on shape, order and error messages, never on specific values.

## 7. Environments and tools

Python 3.12 (local, Docker `python:3.12-slim`, CI on `ubuntu-latest`). `pytest` with `pytest-bdd`, `requests-mock`,
`hypothesis`, `pytest-rerunfailures`, `pytest-randomly`, `pytest-cov`; `jsonschema` and `pydantic` for the contract; Allure
(published to GitHub Pages); `ruff`, `mypy` (strict), `pip-audit`, `detect-secrets`; Apache JMeter 5.6.3; a `Dockerfile`
(offline tests by default, non-root).

## 8. Execution schedule and CI

| Workflow | Trigger | Content |
| --- | --- | --- |
| `Tests` | pull request to `main` | Offline tests only (`-m "not live"`), Allure results as artifact |
| `Tests` | push to `main` | The whole offline suite (`-m "not data_quality"`, which selects every test today); Allure report published to GitHub Pages |
| `Quality` | pull request, push to `main` | `ruff`, `ruff format --check`, `mypy`, offline tests with the coverage gate |
| `Security` | pull request, push to `main`, Monday 05:00 UTC, manual | `pip-audit` and `detect-secrets`; fails on any finding |
| `Performance` | manual only (no schedule) | JMeter plan against the public API, fails on any failed sample |
| `Mutation checks` | Monday 04:00 UTC and manual | 62 deliberate breakages of the client, models and schemas; fails when the offline tests miss one that is not in `ACCEPTED_SURVIVORS`. Last full run on the current suite (2026-11-26): 58 of 62 killed; the 4 survivors are listed under "Known mutation gaps" |

### 8.1 Why there is no live or nightly workflow

The live tests (marker `live`) and the data-quality checks (marker `data_quality`) sent requests to the public Energi Data
Service API. The live tests were removed from the repository on 2026-11-10 (commit `800b1e4e`). The `Live nightly` workflow
that ran them was removed on 2026-11-26. The reasons:

- **Protect the public API.** EDS is a shared production service with rate limits. A run on every push, or every night,
  adds load every day for no benefit to the users of this repository. The default is zero requests to the API.
- **Keep the pipeline meaningful.** With no live tests, the scheduled job ran `pytest -m live`, which collected nothing and
  exited with code 5 ("no tests collected"). It failed every night from 2026-11-17 to 2026-11-25, and each failure e-mailed
  the repository administrators. A manual run with no tests can only show a green result that tests nothing, so the
  workflow was removed rather than kept as a placeholder.
- **Gate on what the framework controls.** The offline suite, which runs on every pull request and push, is the quality gate.
  It checks the client against recorded samples, JSON Schemas and mocks. The real API is not part of the gate.

**To bring the live tests back** (manual steps, in this order):

1. Add the live tests with the `live` (or `data_quality`) marker, following the rules in section 5.
2. Check that the marker selects them: `pytest -m live --collect-only -q` must collect more than zero tests.
3. Run them by hand from a local checkout: `pytest -m live -v`.
4. Add a scheduled workflow only when a team has accepted the load on the API. Keep one run per day and the `eds-live-api`
   concurrency group, so two live runs never overlap.

## 9. Entry and exit criteria

**Entry:** the change is on a feature branch and a pull request is open.

**Exit (may be merged):** `Tests` and `Quality` pass; `ruff` and `mypy --strict` report nothing; `Security`
reports no known vulnerability and no committed secret; coverage of `client/` and `models/` is at least 90% (currently 100%
line and branch). By convention: no test is skipped or marked as an expected failure to make a run pass (none is today).
CI runs these checks on every pull request. It blocks a merge only where branch protection on `main` requires them.

> **TODO (owner):** set branch protection on `main` to require `Tests`, `Quality` and `Security`. Until then a failing check does not stop a merge.

**Exit (`main` is healthy):** the `Tests` run on `main` passes, and the Allure report shows no failed or broken test. The live
tests are not part of this criterion while they are disabled (section 8.1).

## 10. Risk-based prioritisation

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| EDS API changes a field, status or message | Medium | Live tests fail, schemas outdated | JSON Schemas and recorded samples, the OpenAPI drift detector, Allure *Contract drift* category. Live checks against the API run only by hand (section 8.1) |
| Public API rate limiting (429) | Medium | Flaky live tests, blocked client | Few and small live requests, retry with backoff, rerun on network errors only; 429 is never triggered on purpose |
| 429 with a long `Retry-After` (up to 300 s observed; waiting it out made a full run take about 5 minutes instead of 30 seconds, see the [test report](test-report.md#6-open-items)) | High | Slow feedback; now a throttled live fixture fails fast | The client refuses a `Retry-After` above 60 s (`RetryConfig.max_retry_after`) with `RetryAfterTooLongError` (Allure: *Infrastructure problems*); waits and reasons are logged. `Elspotprices` allowed one query per ~300 s; the limit of `DayAheadPrices` is not measured, so a run sends one query to it and a second run within five minutes could fail fast. Live runs share the concurrency group `eds-live-api`, so two live runs never overlap; no workflow runs them automatically |
| Retry logic is wrong but untested | Medium | Hammering the API, or silent failures | Retry behaviour tested against a real local server, not only mocks |
| Tests pass although the client is broken | Medium | False confidence | Mutation checks (62), the kill matrix, request-based assertions; coverage is not trusted alone (see [test coverage](test-coverage.md)) |
| Report shows misleading history | Low | Wrong decisions | Publish guard in CI, Allure categories |
| Dependency changes break the suite | Medium | Red build | Pinned versions; a changed minimum version is verified in a clean environment |
| A pinned dependency has a known vulnerability | Medium | Vulnerable environment | `pip-audit` on every pull request and weekly. On 2026-10-30 it flagged `requests` 2.32.3 and `pytest` 8.3.3; both were bumped after the offline suite, `mypy` and coverage passed on the new versions |

## 11. Defect management

Failures are triaged through Allure categories (*Infrastructure problems*, *Contract drift*, *Product defects*,
*Test defects*, *Skipped tests*). A defect is fixed on a branch with a regression test, merged through a pull request and
recorded in the [test report](test-report.md). With no separate issue tracker, the pull request is the defect record.

## 12. Metrics and reporting

Pass rate, trend, duration and retries: [Allure report](https://magdau.github.io/eds-python-api-test-automation/); test counts:
[test-cases.md](test-cases.md); coverage: [test-coverage.md](test-coverage.md); one run: [test-results.md](test-results.md);
summary, defects, risks: [test-report.md](test-report.md).

## 13. Test maintenance

- Regenerate [test-cases.md](test-cases.md) (`python scripts/generate_test_cases.py`) after changing tests, and
  [test-results.md](test-results.md) (`python scripts/generate_test_results.py`) when a new report is needed.
- Guard against the *pesticide paradox*: when client behaviour changes, check by a quick mutation that at least one test
  fails. `scripts/mutation_check.py` does this for 62 known changes every week (list as of 2026-11-26); add a mutation when a new client behaviour
  is protected by a test, and update a mutation's line when the client line it names changes (otherwise the run reports `STALE`).
- Before removing a test, build the kill matrix (which test fails for which mutation, no `-x`, fixed order) and check what
  the test protects; do not edit tests while it runs, because the mutations change the client files.
- Coverage is an indicator, never a goal: 100% does not show that assertions are strong enough.

### Known mutation gaps (decision, not a quality claim)

The mutation list is kept in full (62 mutants). It is not reduced to make the check pass. Mutants that survive are a
conscious gap, recorded here.

- Full run on the current suite (2026-11-26, 97 tests, 62 mutants): 58 killed, 4 survived. All 4 survivors are in models and schemas:
  - `model-time-required` (`models/dayaheadprices.py`): `TimeUTC` required in DayAheadPrices; no test accepts a record without `TimeUTC`.
  - `schema-co2-envelope-optional` (`schemas/co2emis_schema.json`): `limit` and `dataset` no longer required; no test fails.
  - `schema-price-optional` (`schemas/dayaheadprices_schema.json`): `DayAheadPriceDKK` no longer required; no test fails.
  - `schema-emission-any-type` (`schemas/co2emis_schema.json`): `CO2Emission` accepts any type; no test fails.
  All client mutants are killed.
- The four survivors are accepted as a conscious decision (recorded on 2026-11-10). The reason is not written down in this
  repository. They are listed in `ACCEPTED_SURVIVORS` in `scripts/mutation_check.py`: the run reports them as `ACCEPTED`
  and does not fail on them. Any other survivor still fails the run. Killing a survivor with a test means removing its
  entry from that list.
- Details of the run, with each survivor's effect, are in the [test report, section 4](test-report.md#4-mutation-checks).

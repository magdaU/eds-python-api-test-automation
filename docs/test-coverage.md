# Test coverage

What the tests cover and what they do not. State: 2026-11-10, measured by the commands given below. Python 3.12. Related:
[test strategy](test-strategy.md) · [test cases](test-cases.md) · [test results](test-results.md) · [test report](test-report.md).

## 1. Code coverage

Command: `pytest -m "not live" --cov --cov-branch` (branch measurement is switched on in `pyproject.toml`)

| Package | Statements | Missed | Branches | Missed branches | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| `client/` | 228 | 0 | 38 | 0 | 100% |
| `models/` | 15 | 0 | 0 | 0 | 100% |
| **Total** | **243** | **0** | **38** | **0** | **100%** |

- Scope is `client/` and `models/` (the code under test); test helpers and scripts are not measured.
- Offline tests are the only tests; there are no live tests.
- CI enforces at least 90% (`fail_under` in `pyproject.toml`) on the combined figure of statements and branches.

## 2. Why coverage alone is not trusted

**Current state (2026-11-10, measured):**
- Tests: 97 collected (`pytest --collect-only -q`): 95 pass, 2 expected failures (`xfail`, the documented single-quote rule). 0 live tests. 17 BDD cases from 6 scenarios. The limit for this project is 100 tests.
- Coverage: 100% of statements and branches (table above).
- Mutations (`python scripts/mutation_check.py`, 62 mutants, full run on 2026-11-10): 58 killed, 4 survived. All 4 survivors are in the Pydantic models and JSON Schemas (`model-time-required`, `schema-co2-envelope-optional`, `schema-price-optional`, `schema-emission-any-type`). They are a conscious decision; see `docs/test-strategy.md`, section 13.

Coverage shows which lines ran, not whether a test would fail if the line were wrong. That is why the suite is also checked by
mutations: one line of the client, the models or a schema is changed and the offline suite must fail. The mutation run is manual
(`performance.yml` has no schedule; `mutation.yml` still runs weekly; see `docs/test-plan.md`, section 4).

## 3. Functional coverage

Modules are `tests/test_*.py`; BDD scenarios are in `tests/bdd/features/`.

| Area | Behaviour | Covered by | Level |
| --- | --- | --- | --- |
| Dataset query | `limit` (negative rejected before sending, 0, 1), `offset` (negative passed through as the server's 400, 0), paging | `boundary_values`, `parameter_combinations`, `properties` | Component |
| | `sort` expressions with case preserved; `filter` encoding (non-ASCII, quotes, lists, empty, numbers); combinations of the four parameters | `parameter_combinations`, `filter_encoding`, `properties` | Component |
| | Request target and parameters per dataset; a name or News path with `/`, `?` or `#` stays one encoded segment; keyword-only query arguments in one order | `dataset_contract`, `url_building`, `eds_client` | Component |
| | Typed records: model objects, query passed on, `HTTPError`, `ValidationError`, `TypeError` when the API has no model | `typed_records` | Component |
| News | Paths, parameters with exact case; calendar agrees with archive (live checks of 400, 204, 404 and live schema were removed on 2026-11-10 with the other live tests) | `news_api` | Component |
| Dataset status | Removed on 2026-11-10 with the live tests (the metadata check, which would have caught the discontinued `Elspotprices`, was live) | none | - |
| Data quality | Removed on 2026-11-10 with the live tests (newest records, nightly job) | none | - |
| Contract | JSON Schema of samples (datasets require `records`, `total`, `limit`, `dataset`); Pydantic parsing (timestamps as `datetime`, price area as `Literal`; valid, missing field, bad time, unknown area, extra field, empty); a body that is not the expected JSON raises `InvalidResponseError` | `schema_validation`, `dataset_contract`, `news_api`, `models`, `typed_records` | Component |
| | OpenAPI drift: the detector reports a missing path, parameter and wrong type (offline, on inline specifications); the check against the published specification was live and was removed on 2026-11-10 | `openapi_drift`, `openapi_parameter_drift` | Component |
| Client robustness | Retry on 429 then success, exhaustion (503, News), zero retries, refused connection, `Retry-After` as seconds and as an HTTP date; no retry on 400, 401, 404 | `retry_behavior`, `retry_after_header`, BDD `resilience` | Integration |
| | A `Retry-After` above 60 s ends the request at once, at the limit it is waited, no limit waits any time, the limit survives retries; the total wait budget is shared and refused when exceeded | `retry_after_cap`, `wait_budget`, BDD `resilience` | Integration |
| | Retry, backoff, jitter and per-dataset overrides (an override serves its dataset only, also with a query string, and is closed with the client); warning above 10 retries | `retry_config`, `eds_client` | Component |
| | Log lines (request, error body preview, retry wait and reason, exhaustion); timeout passed on, read timeout surfaces as `ConnectionError`, session closed by `close()` and `with`; real JSON round-trip over HTTP | `logging`, `eds_client`, `dataset_contract` | Integration, Component |
| Test infrastructure | Not tested on purpose: the Allure environment properties and failure categories. Their test modules were removed on 2026-11-10 as low value, so a change to them is not caught by the suite | none | - |
| Non-functional, static, security | Latency and error rate (4 endpoints, 2 users, 30 s); `ruff` (with `PT`), `mypy --strict`; known vulnerabilities and secrets | `performance/` (JMeter), `Quality` and `Security` workflows | Non-functional, Static |

The Allure report groups tests by the same areas (epic and feature labels), the project's form of traceability: there is no
formal requirements document, so features rather than requirement IDs are traced.

## 4. Coverage of test techniques

Equivalence partitioning, boundary values, a decision table, property-based and state-based tests, error guessing, contract
testing, executable specifications and random order are applied as listed in the [test strategy](test-strategy.md#4-test-types-and-design-techniques).

## 5. Coverage of environments

| Dimension | Covered | Not covered |
| --- | --- | --- |
| Python | 3.12 | other versions (no matrix) |
| Operating system | Linux (CI), Windows (local) | macOS |
| `urllib3` | 2.0.2 (verified minimum), 2.8.0 (CI) | below 2.0 (no `backoff_jitter`) and 3.x (excluded by `<3`: `LoggingRetry` overrides `new` and `sleep`) |
| `requests`, `pytest` | 2.33.0 and 9.0.3 (pinned; the earlier 2.32.3 and 8.3.3 had known vulnerabilities) | other versions |

## 6. Known gaps

- The client does not expose other EDS query parameters (`start`, `end`, `columns`, `timezone`) and does not call
  `/dataset/{name}/download`, `/meta/Dataset` (list and search), `/meta/Group`, `/meta/Organization`, `/meta/Tag` and
  `/meta/TagGroup`, so these are untested.
- The published OpenAPI specification is thin (only status 200, no `/dataset` response schema), so the JSON Schemas are the
  oracle and Schemathesis is not used; the drift test only checks that what the client uses is still documented.
- Only `CO2Emis` and `DayAheadPrices` are tested.
- Boundary values are tested at the lower bound only (`limit` 0 and 1, `offset` 0, a negative value of each): no upper bound
  (`int32` in the specification) and no `offset=1`.
- Data values are not compared with an authoritative source; only shape, types, order and error messages.
- A live 429 is never provoked on purpose, so rate-limit handling is proven only against the local server (the wait and its
  logging, also with jitter, a refused connection and a timeout). The real API has answered 429 with `Retry-After` up to 300 s;
  the client refuses waits above 60 s by default (`RetryConfig.max_retry_after`) and fails with `RetryAfterTooLongError`.
- Live `DayAheadPrices` checks share a single query per run (a precaution kept from `Elspotprices`); its limit is not measured.
- Performance is a low-load baseline only; no stress, soak or spike test. No security or TLS tests.
- The CI publish guard is verified by simulating exit codes, not by an automated test.
- The JavaScript explaining empty Categories widgets has no automated test; it was verified by hand against real Allure reports
  in headless Chrome.
- Diagnostics log only the first 300 characters of an error body and never a successful body.
- The mutation catalogue is curated, not generated: it covers the behaviours in `scripts/mutation_check.py`, not every line of
  the client. In the first analysis of 2026-10-30 (40 mutations, 121 tests) 51 tests killed none of them (log lines, Allure tooling, mocks against schemas, model edge
  cases); mutations for the behaviours worth protecting are still to be added.
- `Mutation checks` ran in Actions for the first time on Monday 2026-11-02 (scheduled, succeeded); the catalogue was also run locally on 2026-10-30.

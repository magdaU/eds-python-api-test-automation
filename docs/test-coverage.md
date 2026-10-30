# Test coverage

What the tests cover and what they do not. Measured on `main` plus the review fixes (2026-10-30), Python 3.12. Related:
[test strategy](test-strategy.md) · [test cases](test-cases.md) · [test results](test-results.md) · [test report](test-report.md).

## 1. Code coverage

Command: `pytest -m "not live" --cov` (branch measurement is switched on in `pyproject.toml`)

| Package | Statements | Missed | Branches | Missed branches | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| `client/` | 192 | 0 | 28 | 0 | 100% |
| `models/` | 15 | 0 | 0 | 0 | 100% |
| **Total** | **207** | **0** | **28** | **0** | **100%** |

- Scope is `client/` and `models/` (the code under test); test helpers and scripts are not measured.
- Offline tests alone reach 100%; live tests add confidence in the real API, not coverage.
- CI enforces at least 90% (`fail_under` in `pyproject.toml`) on the combined figure of statements and branches.

## 2. Why coverage alone is not trusted

Coverage shows which lines ran, not whether a test would fail if the line were wrong. An earlier version of the suite had
100% coverage and still contained tests that only repeated what the mock returned. The suite is therefore also checked by
mutations: one line of the client is changed or removed and the offline suite is run. Since 2026-10-29 a catalogue of 49
mutations (client, models and schemas) runs weekly (`scripts/mutation_check.py`, `Mutation checks` workflow). On 2026-10-30
all of them were killed: 43 after three changes (typed records, closable session, invalid responses), 45 after the
per-dataset override fix, 46 after the News path was encoded, 49 after the review fixes.

The first checks were done by hand between 2026-10-28 and 2026-10-29 (`limit`, `sort`, `filter`, `offset` never sent, `sort` and
News `category` in lower case, a wrong dataset path, an unencoded dataset name, four `Retry-After` variants, an unretried 429,
a missing `timeout`, a disabled negative-`limit` check, filter JSON with spaces); each failed 1 to 12 tests. One change (all
methods retried instead of GET only) survived because the client sends only GET; it cannot be seen from outside, so it was
removed and every mutation that survives is now a failure. Seven mutations also fail the BDD scenarios, and the live paging
test fails when `offset` is ignored.

**Which test kills which mutation.** On 2026-10-30 each of the 40 mutations of that day was run against the whole offline
suite without stopping at the first failure. Ten mutations were killed by exactly one test (for example
`metadata-path-wrong`, `retry-after-limit-exclusive`, `backoff-jitter-ignored`, `model-price-optional`), so those tests are
the only guard of their behaviour. Five were killed by seven to nine tests (`filter-not-sent`, `limit-not-sent`,
`offset-not-sent`, `dataset-path-wrong`, `news-path-lowercase`), which is where duplicates were. 51 of 121 tests killed no
mutation; ten were removed as duplicates or trivial negatives, and the rest protect behaviour the catalogue does not mention
(log lines, Allure tooling, mocks against schemas, model edge cases) and stay until a mutation for them is added.

## 3. Functional coverage

Modules are `tests/test_*.py`; BDD scenarios are in `tests/bdd/features/`.

| Area | Behaviour | Covered by | Level |
| --- | --- | --- | --- |
| Dataset query | `limit` (negative rejected before sending, 0, 1), `offset` (negative passed through as the server's 400, 0), paging | `boundary_values`, `parameter_combinations`, `properties`, `live_smoke`, `live_edge_cases` | Component, System |
| | `sort` expressions with case preserved; `filter` encoding (non-ASCII, quotes, lists, empty, numbers); a filter returns only the requested values (also two combined with OR); combinations of the four parameters | `parameter_combinations`, `filter_encoding`, `properties`, `live_smoke`, `live_edge_cases` | Component, System |
| | Request target and parameters per dataset; a name or News path with `/`, `?` or `#` stays one encoded segment; keyword-only query arguments in one order | `dataset_contract`, `url_building`, `eds_client` | Component |
| | Typed records: model objects, query passed on, `HTTPError`, `ValidationError`, `TypeError` when the API has no model | `typed_records` | Component |
| News | Paths, parameters with exact case; live 400 (missing `category`, invalid `date`), 204 (unknown category), 404 (unknown path); calendar agrees with archive; live schema | `news_api`, `live_edge_cases`, `live_smoke` | Component, System |
| Dataset status | Still published and updated (metadata: `active`, title, update interval); would have caught the discontinued `Elspotprices` | `live_smoke`, `dataset_contract` | System, Component |
| Data quality | Newest `CO2Emis` and `DayAheadPrices` records: fresh, no gaps, DK1 and DK2, Danish time matching UTC, plausible values, fit the models | `live_data_quality` | System |
| Contract | JSON Schema of samples and live responses (datasets require `records`, `total`, `limit`, `dataset`); Pydantic parsing (timestamps as `datetime`, price area as `Literal`; valid, missing field, bad time, unknown area, extra field, empty); a body that is not the expected JSON raises `InvalidResponseError` | `schema_validation`, `dataset_contract`, `news_api`, `live_smoke`, `models`, `typed_records` | Component, System |
| | OpenAPI drift: operations and parameters the client uses are still documented; the detector reports a missing path, parameter and wrong type | `openapi_drift` | System, Component |
| Client robustness | Retry on 429 then success, exhaustion (503, News), zero retries, refused connection, `Retry-After` as seconds and as an HTTP date; no retry on 400, 401, 404 | `retry_behavior`, BDD `resilience` | Integration |
| | A `Retry-After` above 60 s ends the request at once, at the limit it is waited, no limit waits any time, the limit survives retries | `retry_after_cap`, BDD `resilience` | Integration |
| | Retry, backoff, jitter and per-dataset overrides (an override serves its dataset only, also with a query string, and is closed with the client); warning above 10 retries | `retry_config`, `eds_client` | Component |
| | Log lines (request, error body preview, retry wait and reason, exhaustion); timeout passed on, read timeout surfaces as `ConnectionError`, session closed by `close()` and `with`; real JSON round-trip over HTTP | `logging`, `eds_client`, `dataset_contract` | Integration, Component |
| Test infrastructure | Allure environment properties (incl. the empty-Categories note) and failure categories. Not tested on purpose: loading mocks from another directory and injecting the note into a report (removed 2026-10-30 as low value) | `allure_environment`, `allure_categories` | Component |
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
  the client. About 40 offline tests kill none of its mutations (log lines, Allure tooling, mocks against schemas, model edge
  cases); mutations for the behaviours worth protecting are still to be added.
- `Mutation checks` has not run in Actions yet (first scheduled run: Monday 2026-11-02 04:00 UTC); the catalogue was run locally.

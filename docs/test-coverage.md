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
per-dataset override fix, 46 after the News path was encoded, 49 after the review fixes. The table is the history of the first
checks, done by hand.

| Mutation of the client | Failing tests | Detected |
| --- | ---: | :---: |
| `limit` is never sent | 12 | yes |
| `sort` is never sent | 7 | yes |
| `filter` is never sent | 12 | yes |
| `sort` is sent in lower case | 7 | yes |
| News `category` is sent in lower case | 2 | yes |
| Dataset URL path is wrong (`/datasets/...`) | 4 | yes |
| `offset` is never sent | 9 | yes |
| Dataset name is not URL-encoded | 4 | yes |
| `Retry-After` limit check disabled | 5 | yes |
| `Retry-After` limit lost between attempts | 5 | yes |
| `Retry-After` limit exclusive (`>=`) | 1 | yes |
| `Retry-After` limit not passed to `urllib3` | 5 | yes |
| `429` is not retried | 2 | yes |
| `timeout` is not passed to the request | 2 | yes |
| Negative `limit` check disabled | 4 | yes |
| Filter JSON with spaces after `:` and `,` | 5 | yes |

The first six checks ran on 2026-10-28 (suite as of PR #61), `offset` against #66, URL-encoding while developing #75 (its
red step), the four `Retry-After` checks while developing #77, and the last four on 2026-10-29 (suite as of #86). One more
change (all methods retried instead of GET only) survived because the client sends only GET; it cannot be seen from outside,
so it was removed from the catalogue and every mutation that survives is now a failure. Seven mutations (`offset`, `sort`,
`filter`, negative `limit`, News `category` case, retried 4xx, ignored `Retry-After`) also fail the BDD scenarios, and the
live paging test fails when `offset` is ignored. Before the mutation checks, these were detected only by the
parameter-focused modules and by none of the dataset contract, pagination or negative-scenario tests; see the
[test report](test-report.md).

**Which test kills which mutation.** On 2026-10-30 each of the 40 mutations of that day was run against the whole offline
suite without stopping at the first failure. Ten mutations were killed by exactly one test (for example
`metadata-path-wrong`, `retry-after-limit-exclusive`, `backoff-jitter-ignored`, `model-price-optional`), so those tests are
the only guard of their behaviour. Five were killed by seven to nine tests (`filter-not-sent`, `limit-not-sent`,
`offset-not-sent`, `dataset-path-wrong`, `news-path-lowercase`), which is where duplicates were. 51 of 121 tests killed no
mutation; ten were removed as duplicates or trivial negatives, and the rest protect behaviour the catalogue does not mention
(log lines, Allure tooling, mocks against schemas, model edge cases) and stay until a mutation for them is added.

## 3. Functional coverage

| Area | Behaviour | Covered by (module `tests/test_*.py`) | Level |
| --- | --- | --- | --- |
| Dataset query | `limit`: negative (rejected before sending), 0 and 1 | `boundary_values`, `parameter_combinations`, `properties` | Component |
| | `offset`: negative (the server's 400 is passed through), 0; paging | `boundary_values`, `live_smoke`, `live_edge_cases` | Component, System |
| | `sort` expressions, case preserved | `parameter_combinations`, `properties`, `live_smoke`, `live_edge_cases` | Component, System |
| | `filter` encoding (non-ASCII, quotes, lists, empty, numbers) | `filter_encoding`, `parameter_combinations`, `properties`, `live_edge_cases` | Component, System |
| | `filter` returns only the requested values (one value; two combined with OR) | `live_smoke` | System |
| | Combinations of the four parameters | `parameter_combinations` | Component |
| | Request target and parameters per dataset; a dataset name or News path with `/`, `?` or `#` stays one encoded segment | `dataset_contract`, `url_building` | Component |
| | Query arguments keyword-only and in one order in `get_dataset`, `DatasetApi.get` and `records` | `eds_client` | Component |
| | Typed records: model objects, query passed on, `HTTPError`, `ValidationError`, `TypeError` when the API has no model | `typed_records` | Component |
| News | Endpoint paths, parameters sent with exact case | `news_api` | Component |
| | 400 for missing `category` and invalid `date`, 204 for unknown category, 404 for unknown path | `live_edge_cases` | System |
| | Calendar agrees with archive, schema of live items | `live_smoke` | System |
| Dataset status | Still published and updated (metadata: `active`, title, update interval); the check that would have caught the discontinued `Elspotprices` | `live_smoke`, `dataset_contract` | System, Component |
| Data quality | Newest records of `CO2Emis` and `DayAheadPrices`: fresh, no gaps, DK1 and DK2, Danish time matching UTC, plausible values | `live_data_quality` | System |
| Contract | JSON Schema of samples (both datasets, news); datasets require the envelope `records`, `total`, `limit`, `dataset` | `schema_validation`, `dataset_contract`, `news_api` | Component |
| | JSON Schema of live responses | `schema_validation`, `live_smoke` | System |
| | Pydantic parsing: timestamps become `datetime`, price area is a `Literal`; valid, missing field, bad time, unknown area, extra field, empty | `models` | Component |
| | A body that is not the expected JSON (not JSON, not an object, no list under `records`) raises `InvalidResponseError` | `models`, `typed_records` | Component |
| | The operations and parameters the client uses are still in the published OpenAPI specification; the detector reports a missing path, parameter and wrong type | `openapi_drift` | System, Component |
| | The 100 newest live records of both datasets fit the models | `live_data_quality` | System |
| Client robustness | Retry on 429 then success; exhaustion (503, News); zero retries; refused connection; `Retry-After` as seconds and as an HTTP date | `retry_behavior` | Integration |
| | No retry on 400, 401 and 404 | BDD `resilience` | Integration |
| | A `Retry-After` above the limit (60 s) ends the request at once; at the limit it is waited; no limit waits any time; the limit survives retries | `retry_after_cap`, BDD `resilience` | Integration |
| | Retry, backoff, jitter and per-dataset overrides (an override serves its dataset only, also with a query string, and its adapter is closed with the client); warning above 10 retries | `retry_config`, `eds_client` | Component |
| | Request line (status, duration), error body preview, wait before a retry and its reason, warning on exhaustion | `logging` | Integration |
| | Timeout passed on, read timeout surfaces as `ConnectionError`, session closed by `close()` and `with` | `eds_client` | Component, Integration |
| | Real JSON round-trip over HTTP | `dataset_contract` | Integration |
| Test infrastructure | Allure environment properties, including the note explaining empty Categories widgets | `allure_environment` | Component |
| | Allure failure categories for typical failure messages | `allure_categories` | Component |
| | Not tested on purpose: loading mocks from another working directory, injecting the empty-widget note into a report (checked by hand; tests of these helpers were removed on 2026-10-30 as low value) | none | none |
| Non-functional | Latency and error rate, 4 endpoints, 2 users, 30 s | `performance/` (JMeter) | Non-functional |
| | Style, bugs, pytest style, types | `ruff` (with `PT`), `mypy --strict` | Static |
| Security | Known vulnerabilities in pinned dependencies, secrets in tracked files | `pip-audit`, `detect-secrets` (`Security` workflow) | Static |

The Allure report groups tests by the same areas (epic and feature labels), which is the project's form of traceability:
there is no formal requirements document, so features rather than requirement IDs are traced.

## 4. Coverage of test techniques

| Technique | Applied to |
| --- | --- |
| Equivalence partitioning | filter values, record validity, URL variants |
| Boundary value analysis | `limit`, `offset` |
| Decision table | the four optional dataset parameters |
| Property-based testing | filters, parameters in the URL, negative `limit`, news URLs |
| Executable specification (Gherkin) | query parameters, retry and give-up behaviour, News parameters |
| Error guessing | unknown column/path/category, invalid date, offset far beyond data, a body that is not JSON |
| Contract testing | JSON Schemas of the responses; drift of the published OpenAPI specification |
| Random order | the offline suite runs in a different order every run (`pytest-randomly`) |
| State-based | retry sequences against the scripted server (failures, then success) |

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
- The published OpenAPI specification declares only status 200 and has no response schema for `/dataset/{datasetName}`, so it
  cannot be an oracle for error statuses or the main response (the JSON Schemas do that). Fuzzing it (Schemathesis) is not
  done: it would send unbounded `limit` and `offset` to a public API. The drift test only checks that what the client uses is still documented.
- Only `CO2Emis` and `DayAheadPrices` are tested.
- Boundary values are tested at the lower bound only (`limit` 0 and 1, `offset` 0, a negative value of each): no upper bound
  (`int32` in the specification) and no `offset=1`.
- Data values are not compared with an authoritative source; only shape, types, order and error messages.
- The EDS guide documents a 429 only by its message, not a `Retry-After` header; the client relies on the header the API has
  been observed to send (see the [test strategy](test-strategy.md#2-scope)).
- A live 429 is never provoked on purpose, so rate-limit handling is proven only against the local server (the wait and its
  logging, also with jitter, a refused connection and a timeout). The real API has answered 429 with `Retry-After` up to 300 s;
  the client refuses waits above 60 s by default (`RetryConfig.max_retry_after`) and fails with `RetryAfterTooLongError`.
- Live `DayAheadPrices` checks share a single query per run, a precaution kept from the discontinued `Elspotprices` (one query
  per ~300 s). `DayAheadPrices` has no measured limit (two runs seconds apart passed); if one exists, two runs less than five
  minutes apart could collide.
- Performance is a low-load baseline only; no stress, soak or spike test. No security or TLS tests.
- The CI publish guard is verified by simulating exit codes, not by an automated test.
- The JavaScript explaining empty Categories widgets has no automated test; it was verified against real Allure reports in
  headless Chrome for five situations (green first build, green with history, a failing run, green after a failing run, only a
  skipped test) in the three places it writes a note (Overview widget, Categories page, Categories trend).
- Diagnostics log only the first 300 characters of an error body and never a successful body.
- The mutation catalogue is curated, not generated: it covers the behaviours in `scripts/mutation_check.py`, not every line of
  the client. About 40 offline tests kill none of its mutations (log lines, Allure tooling, mocks against schemas, model edge
  cases); mutations for the behaviours worth protecting are still to be added.
- `Mutation checks` has not run in Actions yet (first scheduled run: Monday 2026-11-02 04:00 UTC); the catalogue was run locally.

# Test coverage

What the tests cover and what they do not. Measured on `main` plus the per-dataset retry override fix (2026-10-30), Python 3.12. Related:
[test strategy](test-strategy.md) · [test cases](test-cases.md) · [test results](test-results.md) · [test report](test-report.md).

## 1. Code coverage

Command: `pytest -m "not live" --cov` (branch measurement is switched on in `pyproject.toml`)

| Package | Statements | Missed | Branches | Missed branches | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| `client/` | 182 | 0 | 26 | 0 | 100% |
| `models/` | 15 | 0 | 0 | 0 | 100% |
| **Total** | **197** | **0** | **26** | **0** | **100%** |

- Scope is `client/` and `models/` (the code under test). Test helpers and scripts are not measured.
- Only offline tests are needed to reach 100%; live tests add confidence in the real API, not coverage.
- CI enforces coverage of at least 90% (`fail_under` in `pyproject.toml`). Branch measurement is on, so the gate applies to the
  combined figure of statements and branches.

## 2. Why coverage alone is not trusted

Coverage shows which lines ran, not whether a test would fail if the line were wrong. An earlier version of the suite
had 100% coverage and still contained tests that only repeated what the mock returned. Therefore the suite is also
checked by mutations: one line of the client is changed or removed and the offline suite is run. Since 2026-10-29 a catalogue of
45 such mutations (client, models and schemas) runs automatically (`scripts/mutation_check.py`, weekly in the `Mutation checks` workflow); the table below is
the history of the first checks, done by hand. On 2026-10-30 the catalogue was run against the suite as of `main` after three
changes (typed records, a closable session, invalid responses): all 43 mutations were killed (45 after the per-dataset override fix, which added two and replaced one).

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

The last four checks were run on 2026-10-29 against the suite as of pull request #86; the `offset` and `sort` checks were repeated
then (9 and 10 failing tests), and one more change (all methods retried instead of GET only) survived because the client sends only GET. That change cannot be
seen from outside, so it was removed from the catalogue on 2026-10-30 and every mutation that survives is now a failure.
The first six checks were run once on 2026-10-28 against the suite as of pull request #61, the `offset` check against
the suite as of #66, the URL-encoding check while developing #75 (it is the red step of that change) and the four
`Retry-After` checks while developing #77; they are not part of CI.
Seven mutations (`offset`, `sort`, `filter`, negative `limit`, News `category` case, retried 4xx, ignored `Retry-After`) also
fail the BDD scenarios, which exercise the same code from a different angle. The live paging test also fails when `offset` is ignored. Before that
pull request, the same mutations were detected only by the parameter-focused modules (boundary values, parameter
combinations, filter encoding, properties) and by none of the dataset contract, pagination or negative-scenario tests;
see the [test report](test-report.md).

**Which test kills which mutation.** On 2026-10-30 each of the 40 mutations of that day was run against the whole offline suite
without stopping at the first failure. Ten mutations were killed by exactly one test (for example `metadata-path-wrong`,
`retry-after-limit-exclusive`, `backoff-jitter-ignored`, `model-price-optional`), so those tests are the only guard of their
behaviour. Five mutations were killed by seven to nine tests (`filter-not-sent`, `limit-not-sent`, `offset-not-sent`,
`dataset-path-wrong`, `news-path-lowercase`), which is where duplicates were. 51 of 121 tests killed no mutation. Ten were
removed as duplicates or trivial negatives; the rest protect behaviour the catalogue does not mention (log lines, the Allure
tooling, mocks against schemas, edge cases of the models) and stay until a mutation for them is added.

## 3. Functional coverage

| Area | Behaviour | Covered by (module `tests/test_*.py`) | Level |
| --- | --- | --- | --- |
| Dataset query | `limit`: negative (rejected before sending), 0 and 1 | `boundary_values`, `parameter_combinations`, `properties` | Component |
| | `offset`: negative (the server's 400 is passed through), 0; paging | `boundary_values`, `live_smoke`, `live_edge_cases` | Component, System |
| | `sort` expressions, case preserved | `parameter_combinations`, `properties`, `live_smoke`, `live_edge_cases` | Component, System |
| | `filter` encoding (non-ASCII, quotes, lists, empty, numbers) | `filter_encoding`, `parameter_combinations`, `properties`, `live_edge_cases` | Component, System |
| | `filter` returns only the requested values (one value; two values combined with OR) | `live_smoke` | System |
| | Combinations of the four parameters | `parameter_combinations` | Component |
| | Request target and parameters per dataset | `dataset_contract`, `url_building` | Component |
| | Query arguments are keyword-only and in one order in `EDSApiClient.get_dataset`, `DatasetApi.get` and `records` | `eds_client` | Component |
| | Typed records: `records()` returns model objects, passes the query on, raises `HTTPError`, `ValidationError` and a `TypeError` when the API has no model | `typed_records` | Component |
| News | Endpoint paths, parameters sent with exact case | `news_api` | Component |
| | 400 for missing `category` and invalid `date`, 204 for unknown category, 404 for unknown path | `live_edge_cases` | System |
| | Calendar agrees with archive, schema of live items | `live_smoke` | System |
| Dataset status | The dataset is still published and updated (metadata: `active`, title, update interval); this is the check that would have caught the discontinued `Elspotprices` | `live_smoke`, `dataset_contract` | System, Component |
| Data quality | Newest records of `CO2Emis` and `DayAheadPrices` are fresh, without gaps, for DK1 and DK2, with Danish time matching UTC and values in a plausible range | `live_data_quality` | System |
| Contract | JSON Schema of samples (both datasets, news); datasets require the response envelope `records`, `total`, `limit`, `dataset` | `schema_validation`, `dataset_contract`, `news_api` | Component |
| | JSON Schema of live responses | `schema_validation`, `live_smoke` | System |
| | Pydantic parsing: timestamps become `datetime`, price area is a `Literal`; valid, missing field, bad time, unknown area, extra field, empty | `models` | Component |
| | A body that is not the expected JSON (not JSON, not an object, no list under `records`) raises `InvalidResponseError` | `models`, `typed_records` | Component |
| | The operations and parameters the client uses are still documented in the published OpenAPI specification; the detector reports a missing path, a missing parameter and a wrong type | `openapi_drift` | System, Component |
| | The 100 newest live records of both datasets fit the models (types, timestamps, known price areas) | `live_data_quality` | System |
| Client robustness | Retry on 429 then success; exhaustion (503, News endpoints); zero retries; refused connection | `retry_behavior` | Integration |
| | No retry on 400, 401 and 404 | BDD `resilience` | Integration |
| | A `Retry-After` above the limit (60 s) ends the request at once; at the limit it is waited; no limit waits any time; the limit survives retries | `retry_after_cap`, BDD `resilience` | Integration |
| | Retry, backoff, jitter and per-dataset overrides configured (an override serves its dataset only, also with a query string, and its adapter is closed with the client); warning above 10 retries | `retry_config`, `eds_client` | Component |
| | Request line (status, duration), error body preview, wait before a retry and its reason, warning when retries are exhausted | `logging` | Integration |
| | Request timeout passed on, read timeout surfaces as `ConnectionError` ("Read timed out"), session closed by `close()` and by `with` | `eds_client` | Component, Integration |
| | Negative `limit` rejected before sending | `boundary_values`, `properties` | Component |
| | Real JSON round-trip over HTTP | `dataset_contract` | Integration |
| Test infrastructure | Allure environment properties, including the note that explains empty Categories widgets | `allure_environment` | Component |
| | Allure failure categories assign the expected category to typical failure messages | `allure_categories` | Component |
| | Not tested on purpose: loading of mocks from another working directory, the injection of the empty-widget note into a report (checked by hand; the tests of these helpers were removed on 2026-10-30 as low value) | none | none |
| Non-functional | Latency and error rate, 4 endpoints, 2 users, 30 s | `performance/` (JMeter, not pytest) | Non-functional |
| | Style, bugs, pytest style, types | `ruff` (with the `PT` rules), `mypy --strict` | Static |
| Security | Known vulnerabilities in the pinned dependencies and secrets in tracked files | `pip-audit`, `detect-secrets` (`Security` workflow) | Static |

The Allure report groups tests by the same areas (epic and feature labels), which is the project's form of traceability:
there is no formal requirements document, so features rather than requirement IDs are traced.

## 4. Coverage of test techniques

| Technique | Applied to |
| --- | --- |
| Equivalence partitioning | filter values, record validity, URL variants |
| Boundary value analysis | `limit`, `offset` |
| Decision table | the four optional dataset parameters |
| Property-based testing | filters, parameters in the URL, negative `limit`, news URLs |
| Executable specification (Gherkin) | query parameters, retry and give-up behaviour, News parameters (`tests/bdd/features/`) |
| Error guessing | unknown column/path/category, invalid date, offset far beyond data, a body that is not JSON |
| Contract testing | JSON Schemas of the responses; drift of the published OpenAPI specification |
| Random order | the whole offline suite runs in a different order on every run (`pytest-randomly`) |
| State-based | retry sequences against the scripted server (failures, then success) |

## 5. Coverage of environments

| Dimension | Covered | Not covered |
| --- | --- | --- |
| Python | 3.12 | other versions (no matrix) |
| Operating system | Linux (CI), Windows (local) | macOS |
| `urllib3` | 2.0.2 (verified minimum), 2.8.0 (CI) | versions below 2.0 (unsupported: no `backoff_jitter`) |
| `requests`, `pytest` | 2.33.0 and 9.0.3 (pinned; the earlier 2.32.3 and 8.3.3 had known vulnerabilities) | other versions |

## 6. Known gaps

- Client does not expose other EDS query parameters (for example `start`, `end`, `columns`, `timezone`), so they are untested.
  The same goes for the operations of the published specification that it does not call: `/dataset/{name}/download`,
  `/meta/Dataset` (list and search), `/meta/Group`, `/meta/Organization`, `/meta/Tag` and `/meta/TagGroup`.
- The published OpenAPI specification declares only status 200 and has no response schema for `/dataset/{datasetName}`, so it
  cannot serve as an oracle for error statuses or for the main response (the JSON Schemas of this repository do that), and
  fuzzing it (Schemathesis) is not done: it would also send unbounded `limit` and `offset` values to a public API.
  The drift test only checks that what the client uses is still documented.
- Only `CO2Emis` and `DayAheadPrices` are tested; other datasets are not.
- Boundary values are tested at the lower bound only (`limit` 0 and 1, `offset` 0, and a negative value of each). There is no case for
  the upper bound (`int32` in the specification) and none for `offset=1`.
- Data values are not compared with an authoritative source. Only shape, types, order and error messages are checked.
- The EDS guide documents a 429 only by its message in the body, not a `Retry-After` header; the client relies on the header the API has been observed to send (see the [test strategy](test-strategy.md#2-scope)).
- A live 429 is never provoked on purpose, so rate-limit handling is proven only against the local server. `Retry-After`
  handling is `urllib3`'s; the wait and its logging are tested against the local server. The real API has answered 429 with
  `Retry-After` of up to 300 s; the client refuses waits above 60 s by default (`RetryConfig.max_retry_after`, tested against the
  local server) and fails with `RetryAfterTooLongError`.
- Live `DayAheadPrices` checks use a single shared query per run, a precaution kept from the discontinued `Elspotprices`, which answered
  one query per ~300 s window. `DayAheadPrices` has no measured limit (two runs seconds apart both passed). They verify only that one
  request (sort order and schema), and if a limit exists two runs less than five minutes apart could collide.
- Performance covers a low-load baseline only; there is no stress, soak or spike test.
- No security or TLS tests.
- The CI publish guard is verified by simulating exit codes, not by an automated test.
- The JavaScript that explains empty Categories widgets has no automated test; it was verified against real Allure reports in headless Chrome for five situations (green first build, green with history, a failing run, green after a failing run, only a skipped test) in the three places it writes a note (Overview widget, Categories page, Categories trend): the note appears when nothing failed, broke or was skipped and disappears as soon as a run has failures; the trend note stays hidden while a failure is in the recorded history.
- Diagnostics log only the start (300 characters) of an error response body and never the body of a successful response.
- The mutation catalogue is curated, not generated: it covers the behaviours listed in `scripts/mutation_check.py`, not every line of the client.
  About 40 offline tests kill none of its mutations. They protect log lines, the Allure tooling, the agreement of mocks with
  schemas and edge cases of the models; mutations for the behaviours worth protecting are still to be added.
- The `Mutation checks` workflow has not run in Actions yet (first scheduled run: Monday 2026-11-02 04:00 UTC); the catalogue
  was run locally.

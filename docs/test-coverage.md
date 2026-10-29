# Test coverage

What the tests cover and what they do not. Measured on commit `3597f80` (2026-10-28), Python 3.12.2. Related:
[test strategy](test-strategy.md) · [test cases](test-cases.md) · [test results](test-results.md) · [test report](test-report.md).

## 1. Code coverage

Command: `pytest -m "not live" --cov --cov-branch`

| Package | Statements | Missed | Branches | Missed branches | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| `client/` | 146 | 0 | 20 | 0 | 100% |
| `models/` | 11 | 0 | 0 | 0 | 100% |
| **Total** | **157** | **0** | **20** | **0** | **100%** |

- Scope is `client/` and `models/` (the code under test). Test helpers and scripts are not measured.
- Only offline tests are needed to reach 100%; live tests add confidence in the real API, not coverage.
- CI enforces statement coverage of at least 90% (`fail_under` in `pyproject.toml`). Branch coverage is not part of the gate.

## 2. Why coverage alone is not trusted

Coverage shows which lines ran, not whether a test would fail if the line were wrong. An earlier version of the suite
had 100% coverage and still contained tests that only repeated what the mock returned. Therefore the suite is also
checked by hand-made mutations: one line of the client is changed or removed and the offline suite is run.

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

The first six checks were run once on 2026-10-28 against the suite as of pull request #61, the `offset` check against
the suite as of #66, the URL-encoding check while developing #75 (it is the red step of that change) and the four
`Retry-After` checks while developing #77; they are not part of CI.
Seven mutations (`offset`, `sort`, `filter`, negative `limit`, News `category` case, retried 4xx, ignored `Retry-After`) also
fail the BDD scenarios, which exercise the same code from a different angle. The live paging test also fails when `offset` is ignored. Before that
pull request, the same mutations were detected only by the parameter-focused modules (boundary values, parameter
combinations, filter encoding, properties) and by none of the dataset contract, pagination or negative-scenario tests;
see the [test report](test-report.md).

## 3. Functional coverage

| Area | Behaviour | Covered by (module `tests/test_*.py`) | Level |
| --- | --- | --- | --- |
| Dataset query | `limit` incl. 0, 1, 2, 100000 and negative | `boundary_values`, `parameter_combinations`, `properties` | Component |
| | `offset` incl. 0, 1, 100000, negative; paging | `boundary_values`, `pagination`, `live_edge_cases` | Component, System |
| | `sort` expressions, case preserved | `parameter_combinations`, `properties`, `live_smoke`, `live_edge_cases` | Component, System |
| | `filter` encoding (non-ASCII, quotes, lists, empty, numbers) | `filter_encoding`, `parameter_combinations`, `properties`, `live_edge_cases` | Component, System |
| | `filter` returns only the requested values (one value; two values combined with OR) | `live_smoke` | System |
| | Combinations of the four parameters | `parameter_combinations` | Component |
| | Request target and parameters per dataset | `dataset_contract`, `url_building` | Component |
| News | Endpoint paths, parameters sent with exact case | `news_api` | Component |
| | 400 for missing `category` and invalid `date`, 204 for unknown category, 404 for unknown path | `live_edge_cases` | System |
| | Calendar agrees with archive, schema of live items | `live_smoke` | System |
| Contract | JSON Schema of samples (both datasets, news); datasets require the response envelope `records`, `total`, `limit`, `dataset` | `schema_validation`, `dataset_contract`, `news_api` | Component |
| | JSON Schema of live responses | `schema_validation`, `live_smoke` | System |
| | Pydantic parsing: valid, missing field, wrong type, null, extra field, empty | `models` | Component |
| Client robustness | Retry on 429/503 then success; exhaustion; no retry on 400/404; zero retries; News endpoints | `retry_behavior` | Integration |
| | A `Retry-After` above the limit (60 s) ends the request at once; at the limit it is waited; no limit waits any time; the limit survives retries | `retry_after_cap`, BDD `resilience` | Integration |
| | Retry, backoff, jitter and per-dataset overrides configured; warning above 10 retries | `retry_config`, `eds_client` | Component |
| | Request line (status, duration), error body preview, wait before a retry and its reason, warning when retries are exhausted | `logging` | Integration |
| | Connect timeout, refused connection, request timeout | `negative_scenarios`, `eds_client` | Component |
| | Negative `limit` rejected before sending | `boundary_values`, `properties` | Component |
| | Real JSON round-trip over HTTP | `dataset_contract` | Integration |
| Test infrastructure | Allure environment properties, including the note that explains empty Categories widgets | `allure_environment` | Component |
| | Fixtures load from any working directory | `support_paths` | Component |
| | Allure failure categories assign the expected category to typical failure messages | `allure_categories` | Component |
| | The empty-widget note is added to a generated report once (the script's browser behaviour was checked by hand, not by a test) | `inject_report_notes` | Component |
| Non-functional | Latency and error rate, 4 endpoints, 2 users, 30 s | `performance/` (JMeter, not pytest) | Non-functional |
| | Style, bugs, types | `ruff`, `mypy --strict` | Static |

The Allure report groups tests by the same areas (epic and feature labels), which is the project's form of traceability:
there is no formal requirements document, so features rather than requirement IDs are traced.

## 4. Coverage of test techniques

| Technique | Applied to |
| --- | --- |
| Equivalence partitioning | filter values, record validity, URL variants |
| Boundary value analysis | `limit`, `offset` |
| Decision table | the four optional dataset parameters |
| Property-based testing | filters, parameters in the URL, negative `limit`, news URLs, record parsing |
| Executable specification (Gherkin) | query parameters, retry and give-up behaviour, News parameters (`tests/bdd/features/`) |
| Error guessing | unknown column/path/category, invalid date, offset far beyond data |
| State-based | retry sequences against the scripted server (failures, then success) |

## 5. Coverage of environments

| Dimension | Covered | Not covered |
| --- | --- | --- |
| Python | 3.12 | other versions (no matrix) |
| Operating system | Linux (CI), Windows (local) | macOS |
| `urllib3` | 2.0.2 (verified minimum), 2.8.0 (CI) | versions below 2.0 (unsupported: no `backoff_jitter`) |

## 6. Known gaps

- Client does not expose other EDS query parameters (for example `start`, `end`, `columns`, `timezone`), so they are untested.
- Only `CO2Emis` and `Elspotprices` are tested; other datasets are not.
- Data values are not compared with an authoritative source. Only shape, types, order and error messages are checked.
- The EDS guide documents a 429 only by its message in the body, not a `Retry-After` header; the client relies on the header the API has been observed to send (see the [test strategy](test-strategy.md#2-scope)).
- A live 429 is never provoked on purpose, so rate-limit handling is proven only against the local server. `Retry-After`
  handling is `urllib3`'s; the wait and its logging are tested against the local server. The real API has answered 429 with
  `Retry-After` of up to 300 s; the client refuses waits above 60 s by default (`RetryConfig.max_retry_after`, tested against the
  local server) and fails with `RetryAfterTooLongError`.
- Live `Elspotprices` checks use a single shared query per run because the API answers one query per ~300 s window. They cannot
  verify more than that one request (sort order and schema are checked on it), and two runs less than five minutes apart can collide.
- Performance covers a low-load baseline only; there is no stress, soak or spike test.
- No security or TLS tests.
- The CI publish guard is verified by simulating exit codes, not by an automated test.
- The JavaScript that explains empty Categories widgets has no automated test; it was verified against real Allure reports in headless Chrome for five situations (green first build, green with history, a failing run, green after a failing run, only a skipped test) in the three places it writes a note (Overview widget, Categories page, Categories trend): the note appears when nothing failed, broke or was skipped and disappears as soon as a run has failures; the trend note stays hidden while a failure is in the recorded history.
- Diagnostics log only the start (300 characters) of an error response body and never the body of a successful response.
- Mutation checks are manual and not repeated in CI.

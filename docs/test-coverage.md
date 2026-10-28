# Test coverage

What the tests cover and what they do not. Measured on commit `b304c99` (2026-10-28), Python 3.12.2. Related:
[test strategy](test-strategy.md) · [test cases](test-cases.md) · [test results](test-results.md) · [test report](test-report.md).

## 1. Code coverage

Command: `pytest -m "not live" --cov --cov-branch`

| Package | Statements | Missed | Branches | Missed branches | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| `client/` | 101 | 0 | 14 | 0 | 100% |
| `models/` | 11 | 0 | 0 | 0 | 100% |
| **Total** | **112** | **0** | **14** | **0** | **100%** |

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

These checks were run once on 2026-10-28 against the suite as of pull request #61 and are not part of CI. Before that
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
| | Combinations of the four parameters | `parameter_combinations` | Component |
| | Request target and parameters per dataset | `dataset_contract`, `url_building` | Component |
| News | Endpoint paths, parameters sent with exact case | `news_api` | Component |
| | 400 for missing `category` and invalid `date`, 204 for unknown category, 404 for unknown path | `live_edge_cases` | System |
| | Calendar agrees with archive, schema of live items | `live_smoke` | System |
| Contract | JSON Schema of samples (both datasets, news) | `schema_validation`, `dataset_contract`, `news_api` | Component |
| | JSON Schema of live responses | `schema_validation`, `live_smoke` | System |
| | Pydantic parsing: valid, missing field, wrong type, null, extra field, empty | `models` | Component |
| Client robustness | Retry on 429/503 then success; exhaustion; no retry on 400/404; zero retries; News endpoints | `retry_behavior` | Integration |
| | Retry, backoff, jitter and per-dataset overrides configured; warning above 10 retries | `retry_config`, `eds_client` | Component |
| | Warning logged when retries are exhausted | `logging` | Integration |
| | Connect timeout, refused connection, request timeout | `negative_scenarios`, `eds_client` | Component |
| | Negative `limit` rejected before sending | `boundary_values`, `properties` | Component |
| | Real JSON round-trip over HTTP | `dataset_contract` | Integration |
| Test infrastructure | Allure environment properties | `allure_environment` | Component |
| | Fixtures load from any working directory | `support_paths` | Component |
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
- A live 429 is never provoked on purpose, so rate-limit handling is proven only against the local server. `Retry-After`
  handling is `urllib3`'s and is not tested explicitly.
- Performance covers a low-load baseline only; there is no stress, soak or spike test.
- No security or TLS tests.
- The CI publish guard is verified by simulating exit codes, not by an automated test.
- Mutation checks are manual and not repeated in CI.

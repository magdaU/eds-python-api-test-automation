# Test architecture, decisions and risk map

Why the framework looks the way it does, which risk each group of tests answers, and what was deliberately left alone.
Related: [test strategy](test-strategy.md) · [test plan](test-plan.md) · [test coverage](test-coverage.md) ·
[test cases](test-cases.md).

## 1. Architecture and responsibilities

| Part | Responsibility | Size | Verdict |
| --- | --- | ---: | --- |
| `client/eds_client.py`: `EDSApiClient` | Transport: session, retry adapters, timeout, URLs, one log line per request | 164 lines | One reason to change (how the EDS API is called); the URL helpers and the logging are small enough to stay here |
| `client/eds_client.py`: `RetryConfig` | Retry settings as one immutable value | in the file above | Clear |
| `client/retry.py`: `LoggingRetry` | Logs each wait and refuses a `Retry-After` above the limit | 49 lines | Clear |
| `client/dataset_api.py`, `client/news_api.py` | API objects: know the path of one dataset or the News endpoints, hide the client | 29 and 30 lines | Thin by design |
| `client/parsers.py`, `models/` | Raw JSON to typed Pydantic records (timestamps as `datetime`, price areas as `Literal`) | 4 to 8 lines each | **Not used by the client**: only tests call them; the nightly data-quality check parses live records with them (open decision, below) |
| `tests/support/` | Mock loading, schema checks, dataset configuration, scripted local server, Allure helpers | 8 to 56 lines each | Clear; shared by the tests, not by the client |

**Verdict: no restructuring.** The whole production code (`client/` and `models/`) is about 300 lines, each class has one clear job, and the layers do not
leak (tests use API objects, API objects use the client, nothing goes the other way). Splitting `EDSApiClient` further
(a separate URL builder, a separate logger) would add files without removing a real problem, which is against the project's
KISS and YAGNI conventions. Reopen this only if a concrete pain shows up, for example a second transport or a client
that needs a third kind of endpoint.

Open decision (not a code smell, a scope question): `parse_records` and the Pydantic models are not part of any request path.
Either `DatasetApi` returns typed records, or they are treated as a separate helper whose tests are counted apart. Until that
is decided they cost about 25 tests. They are now stricter (a `Literal` for the price areas, `datetime` for the timestamps), and the nightly
data-quality run parses the newest live records with them, so a new price area or a changed timestamp format shows up there.
The `Literal` list is a choice: a new area in the data fails parsing on purpose, which a consumer of the library would feel as a break.

## 2. Decisions and why

| Decision | Why | Evidence |
| --- | --- | --- |
| Retry behaviour is tested against a local scripted HTTP server, not with `requests-mock` | `requests-mock` replaces the transport, so the retry adapter never runs against a mocked response | `tests/support/scripted_server.py`, `test_retry_behavior.py` |
| A `Retry-After` above 60 s ends the request at once (`RetryAfterTooLongError`) | The real API asked for up to 300 s; waiting it out made a full run last about 5.5 minutes | Test report, defects 11 and 12 |
| One shared live query to `DayAheadPrices` per run | Kept from `Elspotprices`, which answered one query per window of about 300 s (a second query got 429); the limit of `DayAheadPrices` is not measured | `tests/support/live.py` |
| Live tests are few, small and rerun only on network errors | The API is public and rate limited; a rerun on an assertion failure would hide a real defect | `test-strategy.md` section 5 |
| The metadata test checks the title and update interval, not only `active` | EDS discontinued `Elspotprices` after 2025-09-30 but its `active` flag stayed true; the tests were then moved to `DayAheadPrices` | `test_live_smoke.py` |
| Test names are `given/when/then` and every body has `# arrange`, `# act`, `# assert` | A test name reads as a test case, so `test-cases.md` can be generated from them | `scripts/generate_test_cases.py` |
| BDD only for a small set of behaviours | They read well as a specification; a scenario layer on every test would add indirection | `test-strategy.md` section 4 |
| Mutation checks are a curated catalogue run weekly, not a generated mutation tool | A one-line change to the client must make a test fail. A tool that generates every mutant would run for hours on the retry tests and needs Linux; 43 chosen changes take about 7 minutes and run anywhere | `scripts/mutation_check.py`, `mutation.yml` |
| Performance thresholds are not enforced yet | There is no baseline: the weekly run now prints p50, p95 and p99, and limits are set after a few runs | `performance.yml`, section 4 below |

## 3. Risk to test map

| Risk | Where it shows | Tests that answer it | Level |
| --- | --- | --- | --- |
| The API throttles (429) or fails (5xx) and the client hangs or hammers it | Slow or red CI, possible IP block | `test_retry_behavior`, `test_retry_after_cap`, `test_logging`, BDD `resilience` | Integration |
| A request parameter is dropped or changed before it reaches the API | Wrong data without an error | `test_boundary_values`, `test_parameter_combinations`, `test_filter_encoding`, `test_properties`, BDD `dataset_queries` | Component |
| A dangerous input leaves the client (negative `limit`, a dataset name that changes the path) | Millions of records, a different endpoint requested | `test_boundary_values`, `test_url_building`, `test_properties` | Component |
| Data stops arriving, has holes, is out of range or mislabels time (a dataset silently frozen) | Stale or wrong figures reach users without any error | `test_live_data_quality` (nightly), metadata test in `test_live_smoke` | System |
| The API changes its response (fields, statuses, messages) | Clients break silently | `test_schema_validation` (live), `test_live_edge_cases`, `test_live_smoke`, nightly run | System |
| A dataset is discontinued while its tests keep passing | Green tests about frozen data | `test_live_smoke` (metadata test) | System |
| The client waits forever on a silent server | Hanging CI | `test_eds_client` (timeout), `test_retry_behavior` (refused connection) | Component |
| The report lies or its history is lost | Wrong decisions | `test_allure_categories`, `test_allure_environment`, CI guard | Component |
| Latency or error rate degrades under light concurrency | Slow API for users | JMeter plan in `performance/` | Non-functional |
| Not covered on purpose | | Time range (`start`, `end`), `columns`, `timezone`, other datasets, data values, security, TLS | See [test coverage](test-coverage.md#6-known-gaps) |

## 4. Performance acceptance

| Setting | Value | Where |
| --- | --- | --- |
| Concurrency | 2 users (`threads`), 30 s, 1 s think time | `performance.yml`, `eds_api_load_test.jmx` |
| Pass rule today | Every sample returns 200 and finishes within 2000 ms (`max_response_ms`) | JMeter assertions |
| Percentiles | p50, p95, p99 and the sample count are printed in the job summary of each run; **not** a pass/fail rule yet | `performance.yml` |
| When to set limits | After a few weekly runs, from the observed p95 plus a margin | |

Why no p95 or p99 limit yet: there is no measured baseline, so a limit would be a guess and could turn the weekly run red
for no reason. With 2 users, a 1 s think time and 4 endpoints a run holds only dozens of samples, where p99 is almost the
maximum, so a p99 limit means little until the run is longer. The run also depends on a public API that throttles.

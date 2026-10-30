# Test architecture, decisions and risk map

Why the framework looks the way it does, which risk each group of tests answers, and what was deliberately left alone.
Related: [test strategy](test-strategy.md) · [test plan](test-plan.md) · [test coverage](test-coverage.md) ·
[test cases](test-cases.md).

## 1. Architecture and responsibilities

| Part | Responsibility | Size | Verdict |
| --- | --- | ---: | --- |
| `client/eds_client.py`: `EDSApiClient` | Transport: session (closable, also a context manager), retry adapters, timeout, URLs, one log line per request; query arguments keyword-only | 176 lines | One reason to change (how the EDS API is called); the URL helpers and the logging are small enough to stay here |
| `client/eds_client.py`: `RetryConfig` | Retry settings as one immutable value | in the file above | Clear |
| `client/retry.py`: `LoggingRetry` | Logs each wait and refuses a `Retry-After` above the limit | 49 lines | Clear |
| `client/dataset_api.py`, `client/news_api.py` | API objects: know the path of one dataset or the News endpoints, hide the client; `DatasetApi.records()` returns typed records | 58 and 30 lines | Thin by design |
| `client/parsers.py`, `models/` | Raw JSON to typed Pydantic records (timestamps as `datetime`, price areas as `Literal`); `InvalidResponseError` for an unexpected body | 11 to 18 lines each | Used by `DatasetApi.records()` and by the nightly data-quality check; optional for a caller (see below) |
| `tests/support/` | Mock loading, schema checks, dataset configuration, scripted local server (with an optional response delay), OpenAPI drift check, Allure helpers | 9 to 58 lines each | Clear; shared by the tests, not by the client |

**Verdict: no restructuring.** The whole production code (`client/` and `models/`) is about 350 lines, each class has one clear job, and the layers do not
leak (tests use API objects, API objects use the client, nothing goes the other way). Splitting `EDSApiClient` further
(a separate URL builder, a separate logger) would add files without removing a real problem, which is against the project's
KISS and YAGNI conventions. Reopen this only if a concrete pain shows up, for example a second transport or a client
that needs a third kind of endpoint.

Decided: the Pydantic models are optional and live behind one method. `DatasetApi.records()` returns the records of a page as
model objects when the API object was created with a `model`; without one it raises `TypeError`, and `get()` still returns the raw
response. A body that is not the expected JSON raises `InvalidResponseError`. The `Literal` list of price areas is a choice: a new
area in the data fails parsing on purpose, which a consumer of the library would feel as a break. The nightly data-quality run
parses the newest live records with the models, so a new price area or a changed timestamp format shows up there.

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
| Query arguments are keyword-only, in one order, in the client and the API object | The two used to differ in order, so a positional call passed `filters` as `offset`; keyword-only turns that into a `TypeError` | `test_eds_client.py` |
| Typed records through an optional `model` on `DatasetApi` | Callers who want raw responses (most tests, the live checks) keep `get()`; `records()` adds parsing and `InvalidResponseError` without a second client | `client/dataset_api.py`, `test_typed_records.py` |
| A drift test on the published OpenAPI specification instead of Schemathesis | The specification declares only status 200, has no response schema for `/dataset` and leaves `limit` and `offset` unbounded, so fuzzing would flag every real error and load a public API; one request that checks what the client uses is enough | `tests/support/openapi.py`, `test_openapi_drift.py` |
| A test is removed only after its mutations are known | A matrix of which test kills which mutation found ten duplicates and showed that two tests the plan had marked as duplicates were the only guard of two mutations | [test coverage](test-coverage.md#2-why-coverage-alone-is-not-trusted) |
| The offline suite runs in random order; dependencies and secrets are scanned | `pytest-randomly` exposes hidden dependencies between tests; `pip-audit` and `detect-secrets` (`Security` workflow) found vulnerable `requests` and `pytest` | `requirements.txt`, `security.yml` |

## 3. Risk to test map

| Risk | Where it shows | Tests that answer it | Level |
| --- | --- | --- | --- |
| The API throttles (429) or fails (5xx) and the client hangs or hammers it | Slow or red CI, possible IP block | `test_retry_behavior`, `test_retry_after_cap`, `test_logging`, BDD `resilience` | Integration |
| A request parameter is dropped or changed before it reaches the API | Wrong data without an error | `test_boundary_values`, `test_parameter_combinations`, `test_filter_encoding`, `test_properties`, BDD `dataset_queries` | Component |
| A dangerous input leaves the client (negative `limit`, a dataset name that changes the path) | Millions of records, a different endpoint requested | `test_boundary_values`, `test_url_building`, `test_properties` | Component |
| Data stops arriving, has holes, is out of range or mislabels time (a dataset silently frozen) | Stale or wrong figures reach users without any error | `test_live_data_quality` (nightly), metadata test in `test_live_smoke` | System |
| The API changes its response (fields, statuses, messages) | Clients break silently | `test_schema_validation` (live), `test_live_edge_cases`, `test_live_smoke`, nightly run | System |
| EDS stops documenting an operation or parameter the client uses | The published specification and the client part ways | `test_openapi_drift` | System |
| An answer is not the JSON the client expects (HTML error page, wrong shape) | A bare `JSONDecodeError` or `KeyError` far from the cause | `test_models`, `test_typed_records` | Component |
| A pinned dependency has a known vulnerability, or a secret is committed | Vulnerable environment, leaked credential | `Security` workflow (`pip-audit`, `detect-secrets`) | Static |
| A dataset is discontinued while its tests keep passing | Green tests about frozen data | `test_live_smoke` (metadata test) | System |
| The client waits forever on a silent server | Hanging CI | `test_eds_client` (timeout), `test_retry_behavior` (refused connection) | Component |
| The report lies or its history is lost | Wrong decisions | `test_allure_categories`, `test_allure_environment`, CI guard | Component |
| Latency or error rate degrades under light concurrency | Slow API for users | JMeter plan in `performance/` | Non-functional |
| Not covered on purpose | | Time range (`start`, `end`), `columns`, `timezone`, other datasets, the operations the client does not call (`download`, the `/meta/*` lists), data values, TLS | See [test coverage](test-coverage.md#6-known-gaps) |

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

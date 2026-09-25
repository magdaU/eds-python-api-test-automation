# Roadmap

Step-by-step plan for each unchecked item in the README's [Planned Improvements](README.md#-planned-improvements).

All plans favor mocked tests (`requests-mock`) for bulk/edge-case coverage, with only a small, bounded number of live smoke calls against the real EDS API — so the suite stays fast and never risks hammering or getting rate-limited by the public API.

---

## 1. Pagination testing

**Goal:** Verify the client and tests correctly handle `limit`/`offset`-based result paging (no page-token pagination exists in this API).

**Acceptance criteria:**
- `get_dataset` supports an `offset` param alongside existing `limit`.
- Mocked tests prove offset+limit returns the expected slice with no overlap/gaps between consecutive "pages".
- `limit=0` (return-all) behavior is explicitly tested and documented.
- Suite doesn't require many live calls to prove paging logic.

**Steps:**
1. Extend `EDSApiClient.get_dataset(dataset, limit=None, filter=None, offset=None)` — add `offset` to the `params` dict when set.
2. Add `requests-mock` to `requirements.txt` (dev/test dependency).
3. Add `tests/mocks/co2_page1.json`, `tests/mocks/co2_page2.json` — small hand-built fixtures with distinct, non-overlapping records.
4. Add `tests/test_pagination.py`: mock `GET /dataset/CO2Emis` for `limit=5&offset=0` and `limit=5&offset=5`, assert record counts and no ID overlap; add a case for `limit=0`.
5. Add one smoke test in `tests/test_co2_api.py` hitting the real API with `limit=5,offset=0` vs `limit=5,offset=5`, asserting no duplicate records.

**API-load note:** Bulk/edge-case paging logic is proven against mocked fixtures; only 2 small bounded live calls (`limit=5`) for a smoke check.

## 2. Sorting validation

**Goal:** Confirm the `sort` parameter is passed through correctly and that returned records are actually in the requested order.

**Acceptance criteria:**
- `get_dataset` supports a `sort` param (e.g. `"CO2Emission desc"`).
- Mocked test asserts client-side order-checking logic against a fixture with records in a known order.
- One bounded live smoke test confirms real ascending/descending order on a small result set.

**Steps:**
1. Extend `EDSApiClient.get_dataset` with an optional `sort` param, appended to `params` as-is (string passthrough, matching API syntax).
2. Add `tests/mocks/elspotprices_sorted.json` with 5 records in known ascending order (reuse for both ASC/DESC assertions by reversing in test).
3. Add `tests/test_sorting.py`: mock response for `sort=SpotPriceDKK` and `sort=SpotPriceDKK desc`, assert the record list is monotonically ordered on that field.
4. Add one bounded live smoke test (`limit=5, sort=SpotPriceDKK desc`) asserting the 5 returned records are in descending order.

**API-load note:** Order-correctness logic tested via mocked fixtures; only 1 bounded live call (`limit=5`).

## 3. Negative test scenarios

**Goal:** Verify the client and tests behave predictably on client/server errors (bad dataset, invalid params, retry-exhaustion, network failure).

**Acceptance criteria:**
- Invalid dataset name and malformed filter each produce an asserted, non-2xx response.
- Retry-exhaustion path (repeated 5xx/429) is proven to stop after `max_retries` without hanging.
- Connection-level failures (timeout) are handled/asserted without a real network dependency.
- At most 1 new live call added.

**Steps:**
1. Add `tests/test_negative_scenarios.py`.
2. Use `requests-mock` to stub: 400 for invalid dataset, 404 for unknown path, repeated 429/500 responses to prove retry count via mock's `call_count`, and a `ConnectTimeout` exception.
3. Assert that 4xx responses (e.g. 400) are *not* retried (mock `call_count == 1`) since only `RETRYABLE_STATUS_CODES` trigger retries.
4. Add one bounded live test: call `get_dataset("NotARealDataset")` against the real API and assert a non-200 status.

**API-load note:** All error/retry-exhaustion paths are mocked (no real 429s deliberately triggered); only 1 bounded live call for an invalid-dataset smoke check.

## 4. Schema validation

**Goal:** Catch API response-shape drift automatically by validating responses against an explicit JSON schema per dataset.

**Acceptance criteria:**
- A JSON schema file exists per dataset (CO2Emis, Elspotprices) describing the `{records: [...]}` shape and field types.
- Schema validation runs against both mocked edge-case responses and the existing live fixture responses.
- Test fails on missing required fields, wrong types, or unexpected structure (empty `records` list handled as a valid edge case, not an error).

**Steps:**
1. Add `jsonschema` to `requirements.txt`.
2. Add `schemas/co2emis_schema.json` and `schemas/elspotprices_schema.json`, derived from the current live response shape.
3. Add `tests/test_schema_validation.py` with a small `assert_matches_schema(json_body, schema_path)` helper.
4. Validate schema against 2-3 mocked edge cases (empty `records` list, a record missing an optional field) plus the existing `co2_response`/`elspotprices_response` fixtures from `conftest.py`.

**API-load note:** Edge cases run against mocks; live coverage reuses the *existing* per-test fixtures already in `conftest.py` — no new live calls added.

## 5. Pydantic models

**Goal:** Replace raw dict/JSON handling with typed models so response parsing is self-documenting and validated at the boundary.

**Acceptance criteria:**
- Typed models exist for CO2Emis and Elspotprices records, matching the schema files from item 4.
- A parsing helper converts a `requests.Response` (or its JSON) into a list of typed records, raising `pydantic.ValidationError` on mismatch.
- Existing tests are not required to change wholesale — only new/updated tests exercise the models.

**Steps:**
1. Add `pydantic` to `requirements.txt`.
2. Add `models/co2emis.py` (`CO2EmisRecord`) and `models/elspotprices.py` (`ElspotpricesRecord`), fields matching schemas from item 4.
3. Add `client/parsers.py` with `parse_records(response_json, model) -> list[model]` — pure function, no new HTTP calls.
4. Add `tests/test_models.py` with mocked JSON fixtures: one valid (asserts successful parse, spot-checks a couple of field values) and one invalid (missing field / wrong type, asserts `ValidationError` is raised).

**API-load note:** Entirely exercised against mocked/static JSON fixtures — zero new live calls.

## 6. Logging

**Goal:** Add structured logging so request behavior (attempts, retries, failures) is observable in CI and local runs.

**Acceptance criteria:**
- `EDSApiClient` logs at DEBUG before each request (URL/params) and at WARNING on a retryable status code.
- Log verbosity is configurable via `pytest.ini` (or an env var), not hardcoded.
- At least one test asserts a specific log message is emitted, using `caplog`.

**Steps:**
1. In `client/eds_client.py`, add `logger = logging.getLogger(__name__)`; log DEBUG before `session.get(...)`, log WARNING when the response status is in `RETRYABLE_STATUS_CODES`.
2. Add `log_cli = true` and `log_cli_level = INFO` to `pytest.ini`.
3. Add `tests/test_logging.py`: use `requests-mock` to return 429 then 200, and `caplog` to assert a WARNING log line was emitted.

**API-load note:** Logging behavior is verified via a mocked response sequence; no live calls needed.

## 7. Allure reporting

**Goal:** Produce rich, shareable HTML test reports for CI runs and portfolio demonstration.

**Acceptance criteria:**
- `allure-pytest` is installed and `pytest --alluredir=allure-results` produces valid results.
- `.github/workflows/tests.yml` is updated to generate (and ideally publish) the Allure report as a CI artifact.
- Key test modules are annotated with `@allure.feature`/`@allure.story` for readability, without changing test logic.

**Steps:**
1. Add `allure-pytest` to `requirements.txt`.
2. Add `@allure.feature("CO2Emis")` / `@allure.feature("Elspotprices")` decorators to `tests/test_co2_api.py` and `tests/test_elspotprices_api.py` (annotation only, no logic change).
3. Update `.github/workflows/tests.yml`: change the "Run tests" step to `pytest -v --alluredir=allure-results`, then add a step to upload `allure-results` as a build artifact (publishing to GitHub Pages is a further option — open question, see below).
4. Add local usage instructions (`allure serve allure-results`) to the README's "Getting Started" section.

**API-load note:** Pure reporting/CI concern — reuses existing (and future mocked) tests as-is, no additional calls.

## 8. Docker support

**Goal:** Make the suite runnable in an isolated, reproducible container without local Python setup.

**Acceptance criteria:**
- A `Dockerfile` builds an image that installs dependencies and runs `pytest` by default.
- Documented `docker build`/`docker run` commands work end-to-end.
- Container respects existing env-var-driven config (e.g., future retry-tuning env vars from item 9) without code changes.

**Steps:**
1. Add `Dockerfile` (slim Python 3.12 base matching CI's `python-version: "3.12"`, `pip install -r requirements.txt`, `CMD ["pytest", "-v"]`).
2. Add `.dockerignore` (`.venv`, `__pycache__`, `allure-results`, `.git`).
3. Add `docker build -t eds-api-tests .` / `docker run --rm eds-api-tests` instructions to the README.

**API-load note:** Only changes the execution environment; live-call volume is unchanged and still governed by the mocking approach in items 1-3 and 9.

## 9. Configurable retry/backoff tuning (jitter, per-dataset limits)

**Goal:** Allow retry/backoff behavior (including per-dataset overrides) to be tuned without code changes, verified without waiting on real retries.

**Acceptance criteria:**
- `EDSApiClient` accepts a way to override `max_retries`/`backoff_factor` per dataset (not just per client instance).
- Retry-count and backoff-config behavior is provable via mocks (assert call counts / `Retry` object state), not real elapsed time.
- Jitter support is either implemented or explicitly flagged as an open question (see below) rather than guessed at.

**Steps:**
1. Extend `EDSApiClient.__init__` to accept `dataset_overrides: dict[str, dict] | None` (e.g. `{"CO2Emis": {"max_retries": 5, "backoff_factor": 2.0}}`); mount a separate `HTTPAdapter`/`Retry` per overridden dataset path, or resolve the override at `get_dataset` call time.
2. Investigate `urllib3.util.retry.Retry(backoff_jitter=...)` (available since urllib3 ≥1.26.9) as the jitter mechanism; pin/verify the installed urllib3 version supports it before relying on it.
3. Add `tests/test_retry_config.py`: use `requests-mock` to return N failing responses (429/503) then a 200, assert the total call count matches the configured `max_retries`, for both default and per-dataset-override config.
4. Assert `backoff_factor`/`backoff_jitter` are correctly set on the constructed `Retry` object (inspect its attributes) rather than measuring real sleep time.

**API-load note:** Retry/backoff/jitter behavior tested entirely via mocked repeated-failure sequences — real 429s are never deliberately triggered against the live API.

## 10. Allure trend, executors and categories widgets

**Goal:** Make the Allure report's Trend/Duration trend/Retries trend, Executors, and Categories widgets populated instead of empty, so the report shows history and CI context, not just a single run's pass/fail list.

**Acceptance criteria:**
- Trend graphs (history-based) show data from the 2nd CI run onward, without requiring any local-only steps.
- The Executors widget shows GitHub Actions as the executor (build/run link) on CI-generated reports.
- Categories widget has an explicit `categories.json` so any future failures get grouped meaningfully instead of falling into Allure's defaults.

**Steps:**
1. Add a step in `.github/workflows/tests.yml` (before running pytest) that writes `allure-results/executor.json` with `name`, `type: "github"`, `buildName`, `buildUrl` (from `github.run_id`/`github.repository` env vars) so the Executors widget populates on CI-generated reports.
2. Add `categories.json` in the repo (e.g. `allure/categories.json`) defining at least "Product defects" vs "Test defects" matched on failure message patterns, and copy it into `allure-results` before generating the report (CI step + local doc note).
3. For trend history: since CI currently only uploads `allure-results` as a per-run artifact (no persistent hosting, per the earlier decision against GitHub Pages), trend needs history carried between runs. Add a step that downloads the previous run's `allure-results` artifact (via `actions/download-artifact` from the last successful workflow run) and copies its `history/` folder into the new `allure-results/history/` before generating, so trend accumulates run over run without standing up external hosting.
4. Document in the README that trend/executors/categories only populate on CI-generated reports (an ad hoc local `allure serve` run won't have executor/history data unless manually copied).

**API-load note:** N/A — purely CI/reporting configuration, no HTTP calls involved.

## 11. Allure Retries trend

**Goal:** Populate the Retries trend widget, which is currently empty even with history data flowing correctly, because it tracks pytest-level test reruns (a test failed, got automatically retried, then passed) — a different mechanism from `EDSApiClient`'s own HTTP-level retry/backoff (already covered by items 6 and 9).

**Acceptance criteria:**
- At least one test can be automatically rerun by pytest on failure and have that rerun show up in Allure's Retries trend.
- The chosen test is a real candidate for transient failure (not an artificially-flaky test added just to populate a graph).

**Steps:**
1. Add `pytest-rerunfailures` to `requirements.txt`.
2. Mark one of the existing live-API smoke tests (a good candidate: a `test_co2_api.py`/`test_elspotprices_api.py` smoke test that already hits the real, occasionally-rate-limited EDS API) with `@pytest.mark.flaky(reruns=2, reruns_delay=5)`.
3. Confirm locally that a forced failure gets rerun (e.g. temporarily point the client at a bad URL) and that Allure's results show the retry.
4. No CI workflow changes needed — `pytest-rerunfailures` hooks into the existing `pytest -v --alluredir=allure-results` run.

**API-load note:** Reruns only happen on an actual failure, and only for the one marked test with a small, bounded `reruns` cap (2) — no risk of runaway retries against the live API.

---

## Open questions

1. **Allure publishing target (item 7):** upload `allure-results`/`allure-report` as a downloadable CI artifact only, or also publish to GitHub Pages?
2. **Jitter support (item 9):** true randomized jitter needs urllib3 ≥1.26.9 (`backoff_jitter`), currently unpinned in `requirements.txt` — OK to pin it, or is a custom backoff implementation preferred?
3. **Docker (item 8):** plan is a single `Dockerfile` only, no `docker-compose.yml` (e.g. for an Allure-viewer container) — confirm that's in scope, or out.

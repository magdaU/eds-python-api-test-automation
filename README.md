# EDS API Automation Framework

[![Allure Report](https://img.shields.io/badge/allure-report-brightgreen)](https://magdau.github.io/eds-python-api-test-automation/)
[![Tests](https://github.com/magdaU/eds-python-api-test-automation/actions/workflows/tests.yml/badge.svg)](https://github.com/magdaU/eds-python-api-test-automation/actions/workflows/tests.yml)

Python-based API test automation framework for the [Energi Data Service (EDS)](https://www.energidataservice.dk/) API: pytest, Pydantic, Allure, GitHub Actions, JMeter. Built as a QA Automation portfolio project demonstrating REST API testing, parameterized/positive/negative testing, response validation, and CI/CD integration.

<p align="center">
  <a href="https://magdau.github.io/eds-python-api-test-automation/">
    <img src="docs/allure-report.png" alt="Allure report overview" width="500">
  </a>
</p>

## 📊 Test Results

| What | Where |
| --- | --- |
| Allure report (latest `main` run, with Trend, Retries, Executors, Categories) | **https://magdau.github.io/eds-python-api-test-automation/** |
| Test runs on GitHub Actions (build numbers in Allure, e.g. `#95`, are these runs) | [Tests workflow](https://github.com/magdaU/eds-python-api-test-automation/actions/workflows/tests.yml) |
| Nightly live API check (catches API drift) | [Live nightly workflow](https://github.com/magdaU/eds-python-api-test-automation/actions/workflows/live-nightly.yml) |
| Code quality (ruff, mypy, coverage) | [Quality workflow](https://github.com/magdaU/eds-python-api-test-automation/actions/workflows/quality.yml) |

## 📚 Test Documentation

| Document | Content |
| --- | --- |
| [Test architecture](docs/test-architecture.md) | Responsibilities of the code, the reasons behind the main decisions, risk to test map, performance acceptance |
| [Test strategy](docs/test-strategy.md) | Objectives, scope, test levels, techniques, environments, entry/exit criteria, risks |
| [Test plan](docs/test-plan.md) | What is tested, when, by what, and when testing is done |
| [Test cases](docs/test-cases.md) | Catalogue of all test cases (generated from the tests) |
| [Test coverage](docs/test-coverage.md) | Code coverage, mutation checks, functional coverage, known gaps |
| [Test results](docs/test-results.md) | Results of the latest CI run on `main` (generated from the Allure report) |
| [Test report](docs/test-report.md) | Summary, defects found and resolved, residual risks, recommendation |

Regenerate the generated ones with `python scripts/generate_test_cases.py` and `python scripts/generate_test_results.py`.

## 🛠️ Technologies

Python · pytest · pytest-bdd (Gherkin) · hypothesis · pytest-rerunfailures · pytest-randomly · ruff · mypy · pytest-cov · pre-commit · Requests · Pydantic · jsonschema · requests-mock · Docker · Allure · JMeter · Git · GitHub Actions · GitHub Pages

## 📁 Project Structure

```text
eds-python-api-test-automation/
│
├── client/
│   ├── eds_client.py    # EDSApiClient: transport, retry/backoff, per-dataset overrides, logging
│   ├── dataset_api.py   # DatasetApi: API object for one dataset (URL + get)
│   ├── news_api.py      # NewsApi: API object for /News endpoints
│   └── parsers.py       # raw JSON -> typed Pydantic models
│
├── models/               # Pydantic models (CO2EmisRecord, DayAheadPricesRecord)
├── schemas/               # JSON Schema per dataset / News item, for response validation
├── allure/
│   ├── categories.json   # Allure report failure categories
│   └── report-notes.js   # explains empty Categories widgets in the generated report
│
├── tests/
│   ├── conftest.py, support/, mocks/   # fixtures, shared helpers (scripted local server, schema asserts), requests-mock data
│   ├── bdd/                            # Gherkin scenarios (features/*.feature) and their step definitions
│   └── test_*.py                       # one module per concern: contract, News, retry, boundaries, encoding, schema,
│                                       # models, properties, logging, Allure, live smoke / edge cases / data quality / OpenAPI drift
│
├── .github/workflows/
│   ├── tests.yml         # CI: tests, Allure report, GitHub Pages publish
│   ├── quality.yml       # CI: ruff, mypy, offline tests with coverage gate
│   ├── security.yml      # CI: pip-audit (known vulnerabilities) and detect-secrets, also weekly
│   ├── live-nightly.yml  # CI: nightly live tests to catch API drift (also manual)
│   ├── performance.yml   # CI: JMeter run (manual / weekly)
│   └── mutation.yml      # CI: weekly mutation checks (scripts/mutation_check.py)
├── performance/
│   ├── eds_api_load_test.jmx   # JMeter plan (low-load baseline)
│   └── endpoints.csv           # endpoints the plan iterates over
│
├── docs/                  # test documentation (strategy, plan, cases, coverage, results, report) + README images
├── scripts/               # generators for docs/test-cases.md and docs/test-results.md, report note injector, mutation checks
│
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt   # ruff, mypy, pytest-cov, type stubs, pre-commit, detect-secrets
├── .pre-commit-config.yaml # local hooks: ruff, mypy, detect-secrets, offline tests before a push
├── pyproject.toml         # ruff, mypy and coverage configuration
├── pytest.ini
├── README.md
├── ROADMAP.md
├── LICENSE
└── .gitignore
```

## 🧪 Current Test Coverage

164 tests (130 offline, 34 live) across the `CO2Emis` and `DayAheadPrices` datasets and the `News` API, mostly mocked (`requests-mock`)
with a few bounded live tests against the real API. The [Allure report](https://magdau.github.io/eds-python-api-test-automation/)
shows 152 of them: the 12 data-quality checks run only in the nightly `Live nightly` job. They cover:

* Status code, content type and structure; `limit`, `filter`, `offset` and `sort` (`limit=0` returns every record, a negative `limit` is rejected)
* Negative scenarios: refused connection, 4xx not retried, invalid dataset and unknown path against the live API
* News API (`/News`, `/actual`, `/calendar`, `/archived`): paths, parameters with their exact case, samples vs. schema, live 400/204/404 checks
* API specification drift (live): every operation and parameter the client uses is still in the public OpenAPI specification
* Dataset status from the metadata endpoint (it caught that `Elspotprices` had been discontinued)
* Data quality of the newest records (nightly): freshness, gaps, DK1/DK2, Danish time against UTC, plausible values
* JSON Schema validation and Pydantic parsing (valid and invalid data, also on live records)
* Boundary values, parameter combinations (decision table), filter encoding, URL building, property-based tests (`hypothesis`)
* Real retry behavior against a local scripted server (503/429 then 200, exhaustion, no retry on 4xx), a timeout on every call,
  per-dataset retry/backoff/jitter tuning, and diagnostics: one log line per request, the wait before each retry and why
  (a `Retry-After` above 60 s ends the request at once), a warning when retries are exhausted
* BDD scenarios (`pytest-bdd`) for query parameters, retries and News
* pytest-level reruns on live tests (network errors only), feeding Allure's Retries trend

## 🚀 Getting Started

```bash
git clone https://github.com/magdaU/eds-python-api-test-automation.git && cd eds-python-api-test-automation
python -m venv .venv
.venv\Scripts\activate      # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
pytest -v
```

Tests that hit the real EDS API carry the `live` marker. Skip them for a fast, offline run:

```bash
pytest -v -m "not live"
```

On GitHub, pull requests run only the offline tests; the full suite (including live) runs on `main`.
A nightly workflow (`live-nightly.yml`, also runnable manually) runs only the live tests to catch API drift. It also runs the data-quality
checks (`-m data_quality`: freshness, gaps, DK1/DK2, Danish time, value range), which the run on `main` skips so a data problem does not turn the build red.

> **Rate limit.** The public API throttles by dataset (the discontinued `Elspotprices` answered one query per ~300 s window).
> A full run sends exactly one query to `DayAheadPrices`, whose limit is not measured (a push to `main` and `Live nightly` share the concurrency group `eds-live-api`, so two live runs never overlap; a run still waiting in that group is cancelled when a newer one arrives, so a pending run can be dropped); if a repeated run is throttled it fails fast
> with `RetryAfterTooLongError`. For repeated local runs use `pytest -m "not live"`.

**CI guard against empty reports.** The `Tests` workflow runs `pytest --collect-only` first and publishes the Allure
report only when pytest exits with `0` or `1` and `allure-results` is not empty. Otherwise it skips the report and the
`gh-pages` publish and fails the job, because a collection error once produced a 0-test report that reset the Trend history.

Mutation checks (do the tests notice a deliberately broken client? takes about 6 minutes, offline; run on a clean tree):

```bash
python scripts/mutation_check.py
```

Code quality (same checks as the `Quality` workflow; install dev tools with `pip install -r requirements-dev.txt`):

```bash
ruff check .                         # lint, import order, bug patterns, complexity, pytest style (PT)
mypy                                 # type check (client, models)
pytest -m "not live" --cov           # offline tests; fails under 90% coverage
```

The same tools run locally before each commit, with [pre-commit](https://pre-commit.com), using the versions pinned in `requirements-dev.txt`.
Set it up once:

```bash
pip install -r requirements-dev.txt
pre-commit install --install-hooks --hook-type pre-commit --hook-type commit-msg --hook-type pre-push
```

A commit runs `ruff check`, `ruff format --check`, `mypy` and `detect-secrets`; a push runs the offline tests. A commit message with an AI
co-author line, and a commit of the author's private notes (`LESSONS_LEARNED.md`, `CODE_REVIEW_NOTES.md`), are refused.
To run every hook on every file: `pre-commit run --all-files`.

For an Allure HTML report:

```bash
pytest --alluredir=allure-results
allure serve allure-results
```

The live report is published on every push to `main`. A local run shows only that run, without the trend, executor and
categories data. The Environment widget is written automatically whenever `--alluredir` is used.

The **Categories** widget lists only failed, broken and skipped tests (`allure/categories.json`), so "0 items total" means
no failures. The published report says so itself (`allure/report-notes.js`).

### Performance tests (JMeter)

A low-load JMeter plan lives in `performance/` (requires JMeter 5.6+). Run it from that directory:

```bash
jmeter -n -t eds_api_load_test.jmx -l results.jtl -e -o report
```

Override defaults with `-Jthreads=2 -Jduration=30 -Jthinktime=1000 -Jmax_response_ms=2000`.
It hits the public EDS API, so keep the load low. In CI it runs only manually or weekly
(`performance.yml`) and uploads the HTML report as an artifact.

<p align="center">
  <img src="docs/jmeter-report.png" alt="JMeter dashboard report" width="500">
</p>

### Run in Docker

```bash
docker build -t eds-api-tests .
docker run --rm eds-api-tests
```

The container runs as a non-root user and defaults to the offline tests (`-m "not live"`); for the live ones use
`docker run --rm eds-api-tests pytest -v -m live`.

<details>
<summary>One-time GitHub Pages setup (only when forking/recreating this repo)</summary>

The workflow publishes the report to the `gh-pages` branch, but GitHub serves it only after two manual steps:

1. The repository must be **public** (Pages for a private repo needs a paid plan).
2. Push to `main` once so the branch exists, then set `Settings → Pages → Source` to **"Deploy from a branch"**,
   branch `gh-pages`, folder `/ (root)`.

After that every push to `main` updates the report.
</details>

## 🔌 API Under Test

[Energi Data Service](https://www.energidataservice.dk/) — public API, see [API docs](https://www.energidataservice.dk/guides/api-guides).

<p align="center">
  <a href="https://www.energidataservice.dk/guides/api-guides">
    <img src="docs/eds-api-guide.png" alt="Energi Data Service API guide" width="500">
  </a>
</p>

## ✅ Completed Improvements

* [x] API client abstraction
* [x] pytest fixtures
* [x] Parameterized tests
* [x] Additional EDS datasets
* [x] API client retry with exponential backoff
* [x] GitHub Actions CI pipeline
* [x] Pagination testing
* [x] Sorting validation
* [x] Negative test scenarios
* [x] Schema validation
* [x] Pydantic models
* [x] Logging
* [x] Allure reporting
* [x] Docker support
* [x] Configurable retry/backoff tuning (jitter, per-dataset limits)
* [x] Allure trend, executors and categories widgets
* [x] Allure Retries trend
* [x] News API endpoint tests (`/News`, `/actual`, `/calendar`, `/archived`)
* [x] JMeter performance tests
* [x] CI guard against empty or broken Allure reports

All planned items are done. See [ROADMAP.md](ROADMAP.md) for the step-by-step plan behind each one.

## 👩‍💻 About the Project

A solo QA Automation portfolio project, built incrementally with a focus on clean test design and realistic QA practices.

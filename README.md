# EDS API Automation Framework

[![Allure Report](https://img.shields.io/badge/allure-report-brightgreen)](https://magdau.github.io/eds-python-api-test-automation/)

Python/pytest API test automation framework for the [Energi Data Service (EDS)](https://www.energidataservice.dk/) API. Built as a QA Automation portfolio project demonstrating REST API testing, parameterized/positive/negative testing, response validation, and CI/CD integration.

## 🛠️ Technologies

Python · pytest · Requests · Pydantic · jsonschema · requests-mock · Docker · Allure · Git · GitHub Actions · GitHub Pages

## 📁 Project Structure

```text
eds-python-api-test-automation/
│
├── client/
│   ├── eds_client.py    # EDSApiClient: retry/backoff, per-dataset overrides, logging
│   └── parsers.py       # raw JSON -> typed Pydantic models
│
├── models/               # Pydantic models (CO2EmisRecord, ElspotpricesRecord)
├── schemas/               # JSON Schema per dataset, for response validation
├── allure/
│   └── categories.json   # Allure report failure categories
│
├── tests/
│   ├── conftest.py
│   ├── mocks/                        # requests-mock fixture data
│   ├── test_co2_api.py               # CO2Emis: status/JSON/structure/limit/filter (mocked) + live smoke tests
│   ├── test_elspotprices_api.py      # Elspotprices: same, + sorting smoke test
│   ├── test_eds_client.py            # default/custom retry configuration
│   ├── test_pagination.py            # limit/offset paging
│   ├── test_sorting.py               # sort parameter
│   ├── test_negative_scenarios.py    # invalid dataset, 404, connection timeout
│   ├── test_schema_validation.py     # JSON Schema validation
│   ├── test_models.py                # Pydantic parsing
│   ├── test_logging.py               # retryable-status logging
│   └── test_retry_config.py          # per-dataset retry/backoff/jitter tuning
│
├── .github/workflows/tests.yml   # CI: tests, Allure report, GitHub Pages publish
├── Dockerfile
├── requirements.txt
├── pytest.ini
├── README.md
├── ROADMAP.md
└── .gitignore
```

## 🧪 Current Test Coverage

48 tests across the `CO2Emis` and `Elspotprices` datasets, mostly mocked (`requests-mock`)
with a handful of bounded live smoke tests against the real API:

* HTTP status code, JSON content-type, response structure
* `limit`, `filter`, `offset` (pagination), `sort` parameters
* Negative scenarios: invalid dataset, unknown path, connection timeout
* JSON Schema validation of API responses
* Pydantic model parsing (valid + invalid data)
* Client logging on retryable status codes
* Retry/backoff configuration, including per-dataset overrides and jitter

## 🚀 Getting Started

```bash
git clone <repository-url> && cd eds-python-api-test-automation
python -m venv .venv
.venv\Scripts\activate      # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
pytest -v
```

For an Allure HTML report:

```bash
pytest --alluredir=allure-results
allure serve allure-results
```

The live, always-up-to-date report (with Trend, Duration/Retries trend, Executors and
Categories populated across CI runs) is published on every push to `main`:
**https://magdau.github.io/eds-python-api-test-automation/**

An ad hoc local `allure serve` run only shows that single run — it won't have the
trend/executor/categories data unless you copy it in yourself.

### Run in Docker

```bash
docker build -t eds-api-tests .
docker run --rm eds-api-tests
```

<details>
<summary>One-time GitHub Pages setup (only needed once, when forking/recreating this repo)</summary>

The workflow publishes the generated report to the `gh-pages` branch via
`peaceiris/actions-gh-pages`, but GitHub won't serve it until two manual,
one-time steps are done — no workflow step can do these for you:

1. The repository must be **public** (Pages hosting for a private repo needs a
   paid GitHub plan, and would default to a private site anyway).
2. Push to `main` at least once so the workflow creates the `gh-pages` branch,
   **then** go to `Settings → Pages → Build and deployment → Source` and switch
   it to **"Deploy from a branch"**, branch `gh-pages`, folder `/ (root)`. It
   can't be set before the branch exists — the dropdown has nothing to point at.

After that one-time setup, every push to `main` updates the live report
automatically.
</details>

## 🔌 API Under Test

[Energi Data Service](https://www.energidataservice.dk/) — public API, see [API docs](https://www.energidataservice.dk/guides/api-guides).

## 📌 Planned Improvements

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
* [ ] Allure Retries trend

See [ROADMAP.md](ROADMAP.md) for the step-by-step plan behind each unchecked item.

## 👩‍💻 About the Project

A solo QA Automation portfolio project, built incrementally with a focus on clean test design and realistic QA practices.
</content>
</invoke>

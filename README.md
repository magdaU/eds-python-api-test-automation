# EDS API Automation Framework

[![Allure Report](https://img.shields.io/badge/allure-report-brightgreen)](https://magdau.github.io/eds-python-api-test-automation/)

Python/pytest API test automation framework for the [Energi Data Service (EDS)](https://www.energidataservice.dk/) API. Built as a QA Automation portfolio project demonstrating REST API testing, parameterized/positive/negative testing, response validation, and CI/CD integration.

## 🛠️ Technologies

Python · pytest · Requests · Git · GitHub Actions

## 📁 Project Structure

```text
eds-api-automation/
│
├── client/
│   └── eds_client.py
│
├── tests/
│   ├── conftest.py
│   ├── test_co2_api.py
│   ├── test_elspotprices_api.py
│   └── test_eds_client.py
│
├── requirements.txt
├── README.md
└── .gitignore
```

## 🧪 Current Test Coverage

Covers the `CO2Emis` and `Elspotprices` datasets: HTTP status codes, JSON/response structure, `limit` param, `filter` param.

## 🚀 Getting Started

```bash
git clone <repository-url> && cd eds-api-automation
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

See [ROADMAP.md](ROADMAP.md) for the step-by-step plan behind each unchecked item.

## 👩‍💻 About the Project

A solo QA Automation portfolio project, built incrementally with a focus on clean test design and realistic QA practices.
</content>
</invoke>

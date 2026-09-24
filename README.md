# EDS API Automation Framework

![Tests](https://github.com/magdaU/eds-api-test-automation/actions/workflows/tests.yml/badge.svg)

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
* [ ] Schema validation
* [ ] Pydantic models
* [ ] Logging
* [ ] Allure reporting
* [ ] Docker support
* [ ] Configurable retry/backoff tuning (jitter, per-dataset limits)

See [ROADMAP.md](ROADMAP.md) for the step-by-step plan behind each unchecked item.

## 👩‍💻 About the Project

A solo QA Automation portfolio project, built incrementally with a focus on clean test design and realistic QA practices.
</content>
</invoke>

# EDS API Automation Framework

![Tests](https://github.com/magdaU/eds-api-test-automation/actions/workflows/tests.yml/badge.svg)

Python-based API test automation framework for testing the [Energi Data Service (EDS)](https://www.energidataservice.dk/) API.

The project is created as a QA Automation portfolio project and focuses on automated REST API testing using Python and pytest.

## 🎯 Project Goal

The goal of this project is to build a reusable and maintainable API test automation framework that can be used to validate different EDS API endpoints, parameters, response structures, and error scenarios.

The project also demonstrates practical QA engineering skills such as:

* API testing
* Test automation
* Positive and negative testing
* Response validation
* Parameterized testing
* Test data management
* Test reporting
* CI/CD integration

## 🛠️ Technologies

* **Python**
* **pytest**
* **Requests**
* **Git**
* **GitHub Actions**

## 📁 Project Structure

```text
eds-api-automation/
│
├── client/
│   └── eds_client.py
│
├── tests/
│   └── test_co2_api.py
│
├── requirements.txt
├── README.md
└── .gitignore
```

The project structure will be extended as the framework grows.

## 🧪 Current Test Coverage

The initial test suite covers the `CO2Emis` dataset.

Current tests include:

* HTTP status code validation
* JSON response validation
* Response structure validation
* `limit` parameter validation
* `filter` parameter validation

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone <repository-url>
cd eds-api-automation
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

**Windows**

```bash
.venv\Scripts\activate
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the tests

```bash
pytest
```

For more detailed output:

```bash
pytest -v
```

## 🔌 API Under Test

The framework currently tests the public API provided by:

**Energi Data Service**

https://www.energidataservice.dk/

API documentation:

https://www.energidataservice.dk/guides/api-guides

## 📌 Planned Improvements

The framework will be gradually extended with:

* [x] API client abstraction
* [ ] pytest fixtures
* [x] Parameterized tests
* [ ] Additional EDS datasets
* [ ] Pagination testing
* [ ] Sorting validation
* [ ] Negative test scenarios
* [ ] Schema validation
* [ ] Pydantic models
* [ ] Logging
* [ ] Allure reporting
* [ ] Docker support
* [x] GitHub Actions CI pipeline

## 👩‍💻 About the Project

This project is developed as a practical QA Automation project to improve and demonstrate skills in Python-based API testing, test automation, and software quality engineering.

The framework is intentionally developed incrementally, with a focus on clean test design, maintainability, and realistic QA practices.
</content>
</invoke>

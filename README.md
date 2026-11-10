# EDS API Automation Framework

[![Allure Report](https://img.shields.io/badge/allure-report-brightgreen)](https://magdau.github.io/eds-python-api-test-automation/)
[![Tests](https://github.com/magdaU/eds-python-api-test-automation/actions/workflows/tests.yml/badge.svg)](https://github.com/magdaU/eds-python-api-test-automation/actions/workflows/tests.yml)

Python test automation for the [Energi Data Service (EDS)](https://www.energidataservice.dk/) API: pytest, Pydantic, Allure, GitHub Actions, JMeter.

## Results and documents

| What | Where |
| --- | --- |
| Allure report (latest run on `main`) | https://magdau.github.io/eds-python-api-test-automation/ |
| Test runs on GitHub Actions | [Tests workflow](https://github.com/magdaU/eds-python-api-test-automation/actions/workflows/tests.yml) |
| Test architecture | [docs/test-architecture.md](docs/test-architecture.md) |
| Test strategy | [docs/test-strategy.md](docs/test-strategy.md) |
| Test plan | [docs/test-plan.md](docs/test-plan.md) |
| Test cases (generated) | [docs/test-cases.md](docs/test-cases.md) |
| Test coverage and mutation checks | [docs/test-coverage.md](docs/test-coverage.md) |
| Test report | [docs/test-report.md](docs/test-report.md) |

## Current state (2026-11-10)

- **97 tests**: 95 pass, 2 expected failures (`xfail`, a documented rule the client does not implement yet). The limit for this project is 100 tests.
- **17 BDD cases** from 6 scenarios (`tests/bdd/`).
- **0 live tests.** The suite sends no requests to the EDS API. It runs on mocks and a local scripted server.
- **Coverage** of `client/` and `models/`: 100% of statements and branches.
- **Mutation checks**: 58 of 62 mutants killed. The 4 survivors are in the Pydantic models and JSON Schemas and are a recorded decision (see `docs/test-strategy.md`, section 13).

The suite covers the rules of the EDS API guide (GET requests, `name=value` query pairs, `limit`, `offset`, `sort`, `filter`, the News endpoints), negative and boundary cases, the retry and wait logic, Pydantic models and JSON Schemas, and property-based tests (`hypothesis`).

## Technologies

Python 3.12 · pytest · pytest-bdd · hypothesis · ruff · mypy · pytest-cov · pre-commit · Requests · Pydantic · jsonschema · requests-mock · Docker · Allure · JMeter · GitHub Actions

## Project structure

```text
client/        EDSApiClient (transport, retry, logging), DatasetApi, NewsApi, parsers
models/        Pydantic models of the dataset records
schemas/       JSON Schemas of the responses
tests/         pytest modules, BDD features (tests/bdd/), shared fixtures and helpers (tests/support/)
performance/   JMeter plan and endpoint list (manual run)
scripts/       generators for the test-case docs, mutation checks
docs/          test documentation
.github/workflows/   tests, quality, security, mutation, performance (manual), live-nightly
```

## Getting started

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows; on macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pytest -v
```

Code quality checks (install dev tools with `pip install -r requirements-dev.txt`):

```bash
ruff check .
ruff format --check .
mypy
pytest --cov --cov-branch
```

Mutation checks (offline, run on a clean working tree; takes several minutes):

```bash
python scripts/mutation_check.py
```

Allure report of a local run:

```bash
pytest --alluredir=allure-results
allure serve allure-results
```

Docker (offline tests by default):

```bash
docker build -t eds-api-tests .
docker run --rm eds-api-tests
```

## Performance tests (JMeter)

The JMeter plan in `performance/` is run by hand only, with minimal load, because it sends requests to the public EDS API:

```bash
cd performance
jmeter -n -t eds_api_load_test.jmx -Jthreads=1 -Jrampup=1 -Jduration=10 -Jthinktime=1000 -Jmax_response_ms=2000 -l results.jtl
```

Details and the options are in `know-how/PERFORMANCE_NOTE.md`. `performance.yml` has no schedule and runs only when started by hand.

## API under test

[Energi Data Service](https://www.energidataservice.dk/) is a public API. The [API guide](https://www.energidataservice.dk/guides/api-guides) states the request rules, and the [OpenAPI specification](https://api.energidataservice.dk/swagger/public/swagger.json) describes the endpoints.

The client's parameters match the specification (checked by hand on 2026-11-10): `datasetName`, `limit` and `offset` (int32), `sort` and `filter` (string), `category` and `date` for the News endpoints. The specification also documents `start`, `end`, `columns` and `timezone`, which the client does not use.

## About the project

A solo QA Automation portfolio project, built incrementally with a focus on clean test design and realistic QA practices. See [ROADMAP.md](ROADMAP.md) for the plan.

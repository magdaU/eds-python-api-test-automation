# Test report

Summary of the current state of the test framework on `main`. Figures were measured on 2026-11-26 on commit `78f710f`
(merge of PR #147), unless a line says otherwise. Related: [test strategy](test-strategy.md) · [test plan](test-plan.md) ·
[test cases](test-cases.md) · [test coverage](test-coverage.md) · [test results](test-results.md) ·
[test architecture](test-architecture.md).

## 1. Summary

The framework tests the client library for the [Energi Data Service (EDS)](https://www.energidataservice.dk/) API. The
suite runs offline on every pull request and push to `main`. It sends no requests to the public EDS API.

| Measure | Value | Source |
| --- | --- | --- |
| Tests collected | 97 (66 test functions; the rest are parametrized runs) | `pytest --collect-only -q` |
| Result of the offline suite | 95 passed, 2 expected failures (`xfail`) | `pytest` on 2026-11-26 |
| BDD test cases | 17, from 13 scenarios in 4 feature files | `tests/bdd/features/` |
| Live tests in the repository | 0 | `pytest -m live --collect-only` collects none |
| Statement and branch coverage of `client/` and `models/` | 100% (243 statements, 38 branches); gate 90% | `pytest --cov --cov-branch` |
| Mutation checks | See section 4 | `scripts/mutation_check.py` |
| Static analysis | `ruff`, `ruff format --check`, `mypy --strict`: no findings | `Quality` workflow |
| Known vulnerabilities and committed secrets | None found | `Security` workflow (`pip-audit`, `detect-secrets`) |
| Latest CI run of `Tests` on `main` | 95 passed, 0 failed, 0 broken, 2 skipped (the expected failures, as Allure reports them) | [test results](test-results.md), build #296 |

**Conclusion.** The offline suite gates changes to the client, the models and the schemas. Coverage and CI are green. The
live API is not checked automatically (section 5).

## 2. What is tested

As described in the [test plan](test-plan.md#2-features-to-be-tested): dataset queries (`CO2Emis`, `DayAheadPrices`), the
News endpoints, the response contract (JSON Schema and Pydantic models), the OpenAPI drift detector, client robustness
(retry, `Retry-After` cap, wait budget, timeouts, refused connections, logging), the test infrastructure, the BDD
specifications, a low-load performance baseline (JMeter), static analysis, dependency and secret scanning.

## 3. Test cases by level

All 97 cases are offline: component tests (mocks and parsing), integration tests (the real HTTP stack against a local scripted
server) and BDD scenarios. [test-cases.md](test-cases.md) is generated from the suite and lists every case, with its level.
No case runs against the live API.

## 4. Mutation checks

`scripts/mutation_check.py` applies one deliberate change at a time to the client, the models or a schema and checks that the
offline suite fails. The catalogue has 62 mutants.

Full run on 2026-11-26 (commit `78f710f`): **58 of 62 killed, 4 survived**. The 4 survivors are all in the Pydantic models and
JSON Schemas and are a recorded decision, not an open defect:

| Mutant | What it changes | Why it survives |
| --- | --- | --- |
| `model-time-required` | `TimeUTC` made required in `DayAheadPricesRecord` | No test parses a record without `TimeUTC` |
| `schema-co2-envelope-optional` | `limit` and `dataset` no longer required in the CO2Emis schema | No test fails on a response without them |
| `schema-price-optional` | `DayAheadPriceDKK` no longer required in the DayAheadPrices schema | No test fails on a record without the price |
| `schema-emission-any-type` | `CO2Emission` accepts any type in the CO2Emis schema | No test fails on a non-numeric emission |

All client mutants are killed. The script exits with code 1 while these 4 survive, so the weekly `Mutation checks` run
reports a failure until the list is changed or the survivors are killed (see section 6).

## 5. Live API: not checked automatically

No workflow sends requests to the public EDS API. This is a decision, not a gap in the framework: a scheduled run would load
a shared production API every day, and a scheduled job without tests fails. The live tests and the nightly workflow can be
enabled and run by hand. The rationale and the steps are in the [test strategy, section 8.1](test-strategy.md#81-live-and-nightly-tests-why-they-are-not-scheduled).

What this means for the results:

- A change in the EDS API (fields, statuses, messages, a discontinued dataset) is not detected automatically. The offline
  suite checks the recorded samples, the JSON Schemas and the documented operations in the OpenAPI drift detector.
- Rate limiting of the real API is covered only against the local scripted server. The client refuses a `Retry-After` above
  60 s (`RetryAfterTooLongError`).

## 6. Open items

- **Branch protection.** CI runs on every pull request, but a failing check blocks a merge only if branch protection on
  `main` requires it. Setting this is an open task for the repository owner (test strategy, section 9).
- **Untested areas.** The client does not use `start`, `end`, `columns` or `timezone`, the `/meta/*` lists and the download
  endpoint. Only `CO2Emis` and `DayAheadPrices` are covered. See [test coverage](test-coverage.md#6-known-gaps).
- **Performance thresholds.** The JMeter run reports p50, p95 and p99 but does not enforce limits yet; there is no baseline.
- **Mutation survivors.** The survivors listed in section 4 are a recorded decision, not a claim of full mutation coverage.

## 7. How this report is kept current

`test-cases.md` and `test-results.md` are generated (`scripts/generate_test_cases.py`, `scripts/generate_test_results.py`).
This report, the strategy, the plan, the architecture and the coverage document are edited by hand. When the suite changes,
update the figures in sections 1 and 4 and the date at the top. Earlier states are in the git history and in the merged pull
requests, not in this document.

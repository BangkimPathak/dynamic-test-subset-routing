# Dynamic Test-Subset Routing Framework

[![Dynamic Test-Subset Routing CI](https://github.com/BangkimPathak/dynamic-test-subset-routing/actions/workflows/ci.yml/badge.svg)](https://github.com/BangkimPathak/dynamic-test-subset-routing/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Academic Information
* **Course:** Automation in Software Development (V Semester)
* **Experiment / Lab:** Assignment 4.3 (`Exp/A_4_3`)
* **Topic:** Dynamic Test-Subset Routing
* **Student Name:** Bangkim Pathak
* **USN / Roll Number:** 24BTRAO006 (24BTRO006)
* **Institution:** Jain (Deemed-to-be University), Faculty of Engineering and Technology
* **Instructor:** Munukuntla Shiva Prasad (`shivaprasad-munukuntla`)

---

## 1. Executive Summary & Problem Statement

In enterprise Continuous Integration (CI) systems, running the complete test suite on every single commit or Pull Request creates a severe developer feedback bottleneck:
* **The Monolithic Test Suite Bottleneck:** As codebases grow to thousands of tests, executing the entire regression suite takes 30 to 60+ minutes per commit, stalling deployment velocity and costing massive cloud runner minutes.
* **Redundant Test Execution:** Over **80% of test runs execute tests completely unrelated** to the code modified in a pull request. For example, changing a product pricing calculation should not trigger database migration tests, warehouse inventory tests, or user authentication tests.
* **The Solution:** **Dynamic Test-Subset Routing (Predictive Test Impact Analysis)** solves this by analyzing the Git diff, mapping the Abstract Syntax Tree (AST) dependency graph, and dynamically routing execution to **only the precise subset of tests affected by the change**.

---

## 2. System Architecture

```text
                               +-----------------------------+
                               |     Git Push / PR Event     |
                               +--------------+--------------+
                                              |
                                              v
                              +-------------------------------+
                              |    Git Diff Change Detector   |
                              |   git diff origin/main...HEAD |
                              +---------------+---------------+
                                              |
                     +------------------------+------------------------+
                     |                                                 |
         [Docs / Assets Only?]                            [Core Config Modified?]
         (e.g., *.md, *.png)                              (requirements.txt, pytest.ini)
                     |                                                 |
            YES      v                                        YES      v
      +-----------------------------+                   +-----------------------------+
      |       STRATEGY: SKIP_ALL    |                   | STRATEGY: FULL_REGRESSION   |
      | - 0 tests executed          |                   | - 100% of test suite runs   |
      | - 0s runner time (>99% save)|                   | - Comprehensive safety gate |
      +-----------------------------+                   +-----------------------------+
                     | NO
                     v
      +-----------------------------------------------+
      |    AST Reverse Dependency Graph Traversal     |
      | - Identify modified modules                   |
      | - Trace transitive blast radius               |
      | - Cross-reference code-to-test matrix         |
      +-----------------------+-----------------------+
                              |
                              v
      +-----------------------------------------------+
      |         STRATEGY: TARGETED_SUBSET             |
      | - Execute ONLY impacted tests                 |
      | - Skip unaffected modules (50% - 85% savings) |
      | - Optional: Shard across parallel CI runners  |
      +-----------------------------------------------+
```

---

## 3. Repository Structure

```text
A_4_3/
├── .github/workflows/ci.yml       # Multi-stage routing CI workflow
├── .gitignore                     # Ignore rules (.venv, caches, logs)
├── requirements.txt               # Project dependencies
├── pytest.ini                     # Pytest configuration
├── src/
│   ├── __init__.py
│   ├── pricing.py                 # Pricing engine
│   ├── cart.py                    # Cart module (depends on pricing)
│   ├── inventory.py               # Inventory module (independent)
│   ├── user_service.py            # User management service
│   ├── payment_gateway.py         # Payment module (depends on user_service & pricing)
│   └── test_router.py             # Dynamic Test Router & TIA Engine
├── tests/
│   ├── __init__.py
│   ├── test_pricing.py            # Pricing unit tests (4 tests)
│   ├── test_cart.py               # Cart tests (3 tests)
│   ├── test_inventory.py          # Inventory tests (3 tests)
│   ├── test_user_service.py       # User service tests (3 tests)
│   ├── test_payment_gateway.py    # Payment tests (3 tests)
│   └── test_router_engine.py      # Router engine unit tests (6 tests)
├── benchmark_routing.py           # Empirical benchmarking suite
├── README.md                      # Complete documentation
└── Assignment_4_3_Dynamic_Test_Subset_Routing_Bangkim_24BTRAO006.pdf # Formal PDF report
```

---

## 4. Empirical Benchmark Results

Running `python benchmark_routing.py` proves the massive latency and compute savings:

| Scenario | Strategy | Selected Tests | Duration (s) | Efficiency / Savings |
| :--- | :---: | :---: | :---: | :--- |
| **1. Naive Full Run** | `FULL_REGRESSION` | 6 suites (22 tests) | 0.480s | 1.00x *(Baseline)* |
| **2. Documentation Only** | `SKIP_ALL` | 0 tests | **0.001s** | **480.5x Faster (100% Skipped)** |
| **3. Isolated Change (`inventory.py`)** | `TARGETED_SUBSET` | 1 suite (3 tests) | **0.080s** | **6.0x Faster (83% Skipped)** |
| **4. Transitive Change (`pricing.py`)** | `TARGETED_SUBSET` | 3 suites (10 tests) | **0.241s** | **2.0x Faster (50% Skipped)** |
| **5. 3-Way Parallel Sharding** | `PARALLEL_MATRIX` | 6 suites (sharded) | **0.161s** | **3.0x Faster (Concurrency)** |

---

## 5. Local Reproduction & Verification

### Run Complete Test Suite (22/22 Passed)
```bash
pytest -v
```

### Run Dynamic Test Router CLI
```bash
# Route based on changed files
python src/test_router.py src/inventory.py
```

### Run Empirical Benchmark Suite
```bash
python benchmark_routing.py
```

---

## 6. GitHub Actions CI Integration
Pushing changes triggers `.github/workflows/ci.yml`. The `analyze-and-route` job inspects the Git diff, determines the routing strategy, and conditionally passes targeted test files to the `execute-routed-tests` job.

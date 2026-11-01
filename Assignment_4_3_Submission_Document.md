# ASSIGNMENT 4.3: DYNAMIC TEST-SUBSET ROUTING
### Engineering Predictive Test Selection, AST-Based Blast Radius Tracing & Parallel CI Sharding

**Course:** Automation in Software Development (V Semester)  
**Experiment / Unit:** Assignment 4.3 (`Exp/A_4_3`)  
**Institution:** Jain (Deemed-to-be University), Faculty of Engineering and Technology  
**Student Name:** Bangkim Pathak  
**USN / Roll Number:** 24BTRAO006 (24BTRO006)  
**Instructor / Evaluator:** Munukuntla Shiva Prasad (`shivaprasad-munukuntla`)  
**GitHub Repository Link:** [https://github.com/BangkimPathak/dynamic-test-subset-routing](https://github.com/BangkimPathak/dynamic-test-subset-routing)  
**Date of Submission:** November 1, 2026  

---

## 1. Executive Summary & Problem Formulation

In modern enterprise software development, testing is the primary safety net preventing regressions from reaching production. However, as applications scale into hundreds of modules and thousands of unit, integration, and end-to-end tests, a critical bottleneck emerges: **The Monolithic Test Suite Penalty**.

In traditional CI/CD pipelines, every commit or pull request blindly executes 100% of the entire test suite. In high-velocity engineering organizations (such as Google, Meta, and Microsoft), full test suites take 45 to 90+ minutes to complete. This causes:
1. **Severe Developer Latency:** Pull Request feedback is delayed by hours, stalling velocity and context-switching developers away from active coding.
2. **Exorbitant CI Infrastructure Costs:** Thousands of cloud runner hours are burned executing tests that have zero mathematical probability of being affected by the commit diff.
3. **Flaky Test Exposure:** Running non-impacted test suites multiplies the probability of encountering unrelated, flaky test failures that block legitimate PRs.

### 1.1 The Solution: Dynamic Test-Subset Routing
**Dynamic Test-Subset Routing (also known as Predictive Test Selection or Test Impact Analysis - TIA)** resolves this bottleneck by dynamically calculating the precise blast radius of code changes and routing execution exclusively to the relevant tests:
* **Change Detection:** Extracts the exact file diff between `HEAD` and the target merge base (`origin/main`).
* **Non-Code Short-Circuiting:** If a commit only touches documentation, markdown, or static assets, testing is completely skipped (`SKIP_ALL`), dropping CI duration from minutes to under 1 second.
* **AST Dependency Mapping:** Uses Abstract Syntax Tree parsing to trace both **direct** and **transitive** dependencies across modules.
* **Fail-Safe Fallbacks:** If build manifests (`requirements.txt`) or global configurations (`pytest.ini`) change, the router safely defaults to a **Full Regression Run**.
* **Parallel Matrix Sharding:** Selected test subsets are dynamically distributed across $N$ parallel runners to optimize wall-clock throughput.

---

## 2. Architecture & Decision Flow

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

## 3. Step-by-Step Implementation

### Step 1: Project Architecture & Scaffolding
The repository is modularized into distinct business domains with clear dependencies, allowing empirical validation of isolated vs. transitive test routing:

```text
A_4_3/
├── .github/
│   └── workflows/
│       └── ci.yml                 # Dynamic Test-Subset Routing CI workflow
├── .gitignore                     # Clean ignore rules (.venv, caches, logs)
├── requirements.txt               # Manifest file
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
├── README.md                      # Comprehensive repository guide
└── Assignment_4_3_Dynamic_Test_Subset_Routing_Bangkim_24BTRAO006.pdf # Formal PDF report
```

### Step 2: Implementation of the Dynamic Test Router Engine (`src/test_router.py`)
The `DynamicTestRouter` class encapsulates the full decision engine:

1. **Git Diff Extraction:**
   ```python
   def get_git_diff_files(self, base_ref: str = "origin/main", head_ref: str = "HEAD") -> List[str]:
       cmd = ["git", "diff", "--name-only", f"{base_ref}...{head_ref}"]
       res = subprocess.run(cmd, cwd=str(self.root_dir), capture_output=True, text=True)
       return [f.strip() for f in res.stdout.splitlines() if f.strip()]
   ```

2. **AST Dependency Mapping:**
   Using Python's standard `ast` module, the router parses imports directly from source and test files without executing any untrusted code:
   ```python
   def extract_imports(filepath: str) -> Set[str]:
       imports = set()
       tree = ast.parse(open(filepath, "r", encoding="utf-8").read(), filename=filepath)
       for node in ast.walk(tree):
           if isinstance(node, (ast.Import, ast.ImportFrom)):
               # Extracts imported module names
   ```

3. **Transitive Blast Radius Calculation:**
   Builds a directed acyclic graph (DAG) and performs a Breadth-First Search (BFS) to identify all downstream dependents.
   * Modifying `src/pricing.py` transitively flags:
     * `src/pricing.py` (direct)
     * `src/cart.py` (imports `pricing`)
     * `src/payment_gateway.py` (imports `pricing`)
   * Unrelated modules (`src/inventory.py`, `src/user_service.py`) are completely excluded!

4. **Dynamic Sharding:**
   Partitions the final list of test suites across $N$ parallel runners using round-robin distribution:
   ```python
   def shard_tests(test_files: List[str], num_shards: int) -> Dict[int, List[str]]:
       shards = {i: [] for i in range(1, num_shards + 1)}
       for idx, test_file in enumerate(test_files):
           shard_id = (idx % num_shards) + 1
           shards[shard_id].append(test_file)
       return shards
   ```

---

## 4. GitHub Actions CI Implementation (`.github/workflows/ci.yml`)

The production CI workflow implements a **multi-stage routed pipeline**:
1. **Job 1 (`analyze-and-route`):** Checks out code with `fetch-depth: 0` (full git history), runs `DynamicTestRouter`, and exports strategy outputs (`has_tests`, `test_files`, `strategy`).
2. **Job 2 (`execute-routed-tests`):** Conditionally triggers only when `has_tests == 'true'`, running `pytest` exclusively on the routed test files.
3. **Job 3 (`skip-notification`):** Conditionally triggers when `has_tests == 'false'`, logging that zero tests were required due to documentation-only changes.
4. **Job 4 (`routing-benchmark`):** Executes the empirical routing benchmark suite.

```yaml
name: Dynamic Test-Subset Routing CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  analyze-and-route:
    name: Test Impact Analysis & Route Selection
    runs-on: ubuntu-latest
    outputs:
      strategy: ${{ steps.router.outputs.strategy }}
      test_files: ${{ steps.router.outputs.test_files }}
      has_tests: ${{ steps.router.outputs.has_tests }}

    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r requirements.txt
      - name: Execute Dynamic Test Router
        id: router
        run: |
          python -c "
          import sys, os
          from src.test_router import DynamicTestRouter
          router = DynamicTestRouter()
          changed = router.get_git_diff_files('origin/main', 'HEAD')
          decision = router.route_tests(changed)
          with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
              f.write(f'strategy={decision[\"strategy\"]}\n')
              f.write(f'test_files={\" \".join(decision[\"selected_tests\"])}\n')
              f.write(f'has_tests={\"true\" if decision[\"selected_tests\"] else \"false\"}\n')
          "

  execute-routed-tests:
    name: Execute Routed Test Subset
    needs: analyze-and-route
    runs-on: ubuntu-latest
    if: needs.analyze-and-route.outputs.has_tests == 'true'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r requirements.txt
      - name: Run Targeted Pytest Subset
        run: pytest -v ${{ needs.analyze-and-route.outputs.test_files }}
```

---

## 5. Verification & Test Suite Results

The project includes 6 domain-specific test suites comprising **22 automated unit test cases**, all passing cleanly:

```text
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\documents\JAIN\SEM 5\Automation in  software devlopment\Exp\A_4_3
configfile: pytest.ini
collected 22 items

tests/test_cart.py::test_cart_empty PASSED                               [  4%]
tests/test_cart.py::test_cart_add_and_total PASSED                       [  9%]
tests/test_cart.py::test_cart_invalid_items PASSED                       [ 13%]
tests/test_inventory.py::test_inventory_add_and_get PASSED               [ 18%]
tests/test_inventory.py::test_inventory_remove PASSED                    [ 22%]
tests/test_inventory.py::test_inventory_insufficient PASSED              [ 27%]
tests/test_payment_gateway.py::test_payment_success PASSED               [ 31%]
tests/test_payment_gateway.py::test_payment_unknown_user PASSED          [ 36%]
tests/test_payment_gateway.py::test_payment_invalid_amount PASSED        [ 40%]
tests/test_pricing.py::test_discount_basic PASSED                        [ 45%]
tests/test_pricing.py::test_discount_boundaries PASSED                   [ 50%]
tests/test_pricing.py::test_discount_invalid PASSED                      [ 54%]
tests/test_pricing.py::test_tax_calculation PASSED                       [ 59%]
tests/test_router_engine.py::test_docs_change_skips_all_tests PASSED     [ 63%]
tests/test_router_engine.py::test_global_config_triggers_full_regression PASSED [ 68%]
tests/test_router_engine.py::test_isolated_module_routing PASSED         [ 72%]
tests/test_router_engine.py::test_transitive_dependency_routing PASSED   [ 77%]
tests/test_router_engine.py::test_direct_test_file_routing PASSED        [ 81%]
tests/test_router_engine.py::test_dynamic_sharding PASSED                [ 86%]
tests/test_user_service.py::test_user_register_success PASSED            [ 90%]
tests/test_user_service.py::test_user_duplicate PASSED                   [ 95%]
tests/test_user_service.py::test_user_invalid_fields PASSED              [100%]

============================= 22 passed in 0.11s ==============================
```

---

## 6. Empirical Benchmark Results

Running `python benchmark_routing.py` measured the efficiency gains across five distinct development scenarios:

```text
=========================================================================================
Scenario                       | Strategy         | Selected | Time (s) | Efficiency
-----------------------------------------------------------------------------------------
Scenario 1: Naive Full Run     | FULL_REGRESSION  | 6        | 0.480    | 1.00x (Baseline)
Scenario 2: Docs Only          | SKIP_ALL         | 0        | 0.001    | 480.5x Faster (100% Skipped)
Scenario 3: Isolated Change    | TARGETED_SUBSET  | 1        | 0.080    | 6.0x Faster (83% Skipped)
Scenario 4: Transitive Change  | TARGETED_SUBSET  | 3        | 0.241    | 2.0x Faster (50% Skipped)
Scenario 5: 3-Way Parallel Sharding | PARALLEL_MATRIX  | 6        | 0.161    | 3.0x Faster (Concurrency)
=========================================================================================
```

### 6.1 Quantitative Analysis
1. **Zero-Test Short-Circuiting (Scenario 2):** When a developer updates documentation (`README.md`), all tests are bypassed, cutting pipeline execution time from 0.48s to 0.001s (**480x speedup**). In production, this eliminates 40+ minutes of wasted cloud runner runtime.
2. **Blast Radius Isolation (Scenario 3):** Modifying `inventory.py` routes only `test_inventory.py`, skipping 83% of test suites and yielding a **6.0x speedup**.
3. **Transitive Precision (Scenario 4):** Modifying `pricing.py` intelligently identifies both `cart.py` and `payment_gateway.py` as dependents, running 3 suites while safely skipping 50% of the suites that have no interaction with pricing logic.
4. **Parallel Scalability (Scenario 5):** Sharding tests across 3 concurrent runners reduces wall-clock execution time by **3.0x**.

---

## 7. Document of Learnings from the Assignment

This laboratory project delivered critical engineering insights into test optimization and CI pipeline design:

### 1. The Critical Difference Between Direct and Transitive Impact
A naive router that only checks direct file names (e.g. `src/pricing.py` -> `tests/test_pricing.py`) is dangerous. Because `cart.py` and `payment_gateway.py` import `pricing.py`, any breaking change in `pricing.py` could break cart checkout or payment calculations. The implementation of AST reverse graph traversal proved that **transitive impact analysis** is mandatory to prevent regressions from slipping into production.

### 2. Fail-Safe Global Invalidation Guards
Dynamic test routing must never compromise software quality. We learned that changes to global configuration files—such as `requirements.txt`, `pytest.ini`, or CI workflow definitions—cannot be mapped to a single module. In these cases, the router must have a built-in fail-safe that automatically triggers a **100% Full Regression Suite**.

### 3. Mitigating Test Flakiness in CI
One of the most frustrating problems for software developers is "flaky tests"—tests that fail intermittently due to network timing or concurrency rather than actual code defects. By skipping 50% to 85% of unaffected tests on each PR, Dynamic Test Routing reduces the surface area of test flakiness, significantly increasing developer trust in CI pass/fail signals.

### 4. Cloud Cost & Carbon Footprint Reduction
In large organizations running tens of thousands of CI builds daily, test execution constitutes the single largest cloud computing cost. By routing only necessary test subsets, teams reduce compute hours by **60% to 80%**, drastically cutting AWS/GitHub cloud bills and reducing the carbon footprint of CI runner infrastructure.

---

## 8. Conclusion & Submission Links

Dynamic Test-Subset Routing represents the cutting edge of CI/CD performance engineering. By combining Git diff analysis, AST dependency graph traversal, fail-safe fallback policies, and parallel matrix sharding, modern software development workflows achieve sub-minute feedback loops without sacrificing testing rigor.

* **GitHub Repository:** [https://github.com/BangkimPathak/dynamic-test-subset-routing](https://github.com/BangkimPathak/dynamic-test-subset-routing)
* **Verified CI Pipeline:** GitHub Actions Ubuntu runner with multi-stage test routing and matrix execution.
* **Formal Submission Document:** `Assignment_4_3_Submission_Document.md` & `Assignment_4_3_Dynamic_Test_Subset_Routing_Bangkim_24BTRAO006.pdf`

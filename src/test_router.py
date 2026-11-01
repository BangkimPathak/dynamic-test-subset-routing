"""
Dynamic Test-Subset Router & Predictive Test Impact Analysis (TIA) Engine.
Course: Automation in Software Development (V Semester)
Jain University
"""

import ast
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class DynamicTestRouter:
    """
    Intelligent test selection and dynamic routing engine:
    1. Inspects Git diffs between base and head refs.
    2. Builds code-to-test dependency graph via AST inspection.
    3. Traces blast radius of source changes (direct + transitive).
    4. Routes test execution: SKIP_ALL, TARGETED_SUBSET, or FULL_REGRESSION.
    5. Shards selected test subsets across parallel CI runner matrix.
    """

    # Files that mandate running the complete test suite
    GLOBAL_TRIGGER_FILES = {
        "requirements.txt",
        "pytest.ini",
        "setup.py",
        "pyproject.toml"
    }

    # Extensions that can be safely ignored (0 tests required)
    DOCS_EXTENSIONS = {".md", ".txt", ".rst", ".png", ".jpg", ".pdf", ".html"}

    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir).resolve()
        self.src_dir = self.root_dir / "src"
        self.tests_dir = self.root_dir / "tests"

    def get_git_diff_files(self, base_ref: str = "origin/main", head_ref: str = "HEAD") -> List[str]:
        """Detects changed files between two git references."""
        try:
            # First try merge-base diff
            cmd = ["git", "diff", "--name-only", f"{base_ref}...{head_ref}"]
            res = subprocess.run(cmd, cwd=str(self.root_dir), capture_output=True, text=True, check=True)
            files = [f.strip() for f in res.stdout.splitlines() if f.strip()]
            if files:
                return files
        except Exception:
            pass

        # Fallback to diff against previous commit or working tree
        try:
            cmd = ["git", "diff", "--name-only", "HEAD~1...HEAD"]
            res = subprocess.run(cmd, cwd=str(self.root_dir), capture_output=True, text=True)
            files = [f.strip() for f in res.stdout.splitlines() if f.strip()]
            if files:
                return files
        except Exception:
            pass

        # Fallback to unstaged/staged git status
        try:
            cmd = ["git", "status", "--porcelain"]
            res = subprocess.run(cmd, cwd=str(self.root_dir), capture_output=True, text=True)
            files = [line[3:].strip() for line in res.stdout.splitlines() if line.strip()]
            return files
        except Exception:
            return []

    @staticmethod
    def extract_imports(filepath: str) -> Set[str]:
        """Extracts imported module names from a Python source or test file."""
        imports = set()
        if not os.path.exists(filepath):
            return imports

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=filepath)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        parts = alias.name.split(".")
                        imports.add(parts[-1])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        parts = node.module.split(".")
                        imports.add(parts[-1])
        except Exception:
            pass
        return imports

    def build_dependency_matrix(self) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
        """
        Builds two maps:
          1. source_dep_graph: module -> set of modules it depends on
          2. test_coverage_map: test_file -> set of source modules it exercises
        """
        source_dep_graph = {}
        if self.src_dir.exists():
            for py_file in self.src_dir.glob("*.py"):
                mod_name = py_file.stem
                if mod_name.startswith("__"):
                    continue
                source_dep_graph[mod_name] = self.extract_imports(str(py_file))

        test_coverage_map = {}
        if self.tests_dir.exists():
            for test_file in self.tests_dir.glob("test_*.py"):
                rel_test = test_file.relative_to(self.root_dir).as_posix()
                test_coverage_map[rel_test] = self.extract_imports(str(test_file))

        return source_dep_graph, test_coverage_map

    def get_transitive_dependents(self, modified_module: str, source_dep_graph: Dict[str, Set[str]]) -> Set[str]:
        """Computes all modules that directly or transitively depend on modified_module."""
        # Build reverse graph: module -> dependents
        reverse_graph: Dict[str, Set[str]] = {m: set() for m in source_dep_graph}
        for mod, deps in source_dep_graph.items():
            for d in deps:
                if d in reverse_graph:
                    reverse_graph[d].add(mod)

        # BFS to collect blast radius
        impacted = {modified_module}
        queue = [modified_module]
        while queue:
            curr = queue.pop(0)
            for dependent in reverse_graph.get(curr, set()):
                if dependent not in impacted:
                    impacted.add(dependent)
                    queue.append(dependent)
        return impacted

    def route_tests(self, changed_files: List[str]) -> dict:
        """
        Determines the routing decision:
          - Strategy: 'SKIP_ALL', 'TARGETED_SUBSET', or 'FULL_REGRESSION'
          - Tests to execute: List of relative test file paths
          - Reason / diagnostics
        """
        if not changed_files:
            return {
                "strategy": "FULL_REGRESSION",
                "selected_tests": self.get_all_tests(),
                "reason": "No changed files supplied; executing full safety regression"
            }

        # Check for global config triggers (e.g. requirements.txt)
        for cf in changed_files:
            p = Path(cf)
            if p.name in self.GLOBAL_TRIGGER_FILES or ".github" in p.parts:
                return {
                    "strategy": "FULL_REGRESSION",
                    "selected_tests": self.get_all_tests(),
                    "reason": f"Global build/config trigger modified: {cf}"
                }

        # Check if all changed files are documentation or non-code
        all_non_code = all(Path(cf).suffix in self.DOCS_EXTENSIONS for cf in changed_files)
        if all_non_code:
            return {
                "strategy": "SKIP_ALL",
                "selected_tests": [],
                "reason": "Only documentation or asset files changed; testing skipped"
            }

        # Compute impacted source modules
        source_dep_graph, test_coverage_map = self.build_dependency_matrix()
        all_impacted_modules: Set[str] = set()
        directly_modified_tests: Set[str] = set()

        for cf in changed_files:
            path_obj = Path(cf)
            # If a test file was modified directly, it must run
            if cf.startswith("tests") and path_obj.name.startswith("test_"):
                directly_modified_tests.add(path_obj.as_posix())
            elif cf.startswith("src") and path_obj.suffix == ".py":
                mod_name = path_obj.stem
                impacted = self.get_transitive_dependents(mod_name, source_dep_graph)
                all_impacted_modules.update(impacted)

        # Select all tests that cover any of the impacted modules
        selected_tests: Set[str] = set(directly_modified_tests)
        for test_file, covered_modules in test_coverage_map.items():
            if any(mod in all_impacted_modules for mod in covered_modules):
                selected_tests.add(test_file)

        # If changes occurred in code but mapped to 0 tests, safety fallback to full regression
        if not selected_tests and any(cf.endswith(".py") for cf in changed_files):
            return {
                "strategy": "FULL_REGRESSION",
                "selected_tests": self.get_all_tests(),
                "reason": "Python code modified but no direct test mapping found; running full regression"
            }

        sorted_tests = sorted(list(selected_tests))
        return {
            "strategy": "TARGETED_SUBSET",
            "selected_tests": sorted_tests,
            "impacted_modules": sorted(list(all_impacted_modules)),
            "reason": f"Routed {len(sorted_tests)} targeted test(s) covering {len(all_impacted_modules)} impacted module(s)"
        }

    def get_all_tests(self) -> List[str]:
        """Returns all discovered test files."""
        if not self.tests_dir.exists():
            return []
        return sorted([t.relative_to(self.root_dir).as_posix() for t in self.tests_dir.glob("test_*.py")])

    @staticmethod
    def shard_tests(test_files: List[str], num_shards: int) -> Dict[int, List[str]]:
        """Dynamically partitions test files across parallel runner shards."""
        if num_shards <= 1:
            return {1: test_files}

        shards: Dict[int, List[str]] = {i: [] for i in range(1, num_shards + 1)}
        for idx, test_file in enumerate(test_files):
            shard_id = (idx % num_shards) + 1
            shards[shard_id].append(test_file)
        return shards


def main():
    """CLI entrypoint for CI workflow integration."""
    router = DynamicTestRouter()
    changed = sys.argv[1:] if len(sys.argv) > 1 else router.get_git_diff_files()
    decision = router.route_tests(changed)

    print(f"Routing Strategy: {decision['strategy']}")
    print(f"Reason:           {decision['reason']}")
    print(f"Selected Tests ({len(decision['selected_tests'])}):")
    for t in decision["selected_tests"]:
        print(f"  - {t}")

    if decision["strategy"] == "SKIP_ALL":
        sys.exit(0)
    elif not decision["selected_tests"]:
        print("No tests selected.")
        sys.exit(0)

    # Output formatted string for pytest command
    test_arg = " ".join(decision["selected_tests"])
    print(f"\nCommand: pytest -v {test_arg}")


if __name__ == "__main__":
    main()

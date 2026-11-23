"""`python3 -m unittest tests.<module>` でもテストが import できることを固定する（共通規約 13）。

pytest は `tests/` を sys.path に入れるが、`-m unittest tests.<module>` は入れない。
共有 helper（`_paths` など）を import するテストは、`tests/__init__.py` が
`tests/` を sys.path に入れることで解決する。

1 モジュールを 1 subprocess で import する。1 プロセスでまとめると、先に import
したモジュールの sys.path 挿入が、後のモジュールの失敗を隠す。
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor

from _paths import PLUGIN_ROOT

TESTS_DIR = PLUGIN_ROOT / "tests"


def _import_as_tests_package(module: str) -> tuple[str, int, str]:
    result = subprocess.run(
        [sys.executable, "-c", f"import importlib; importlib.import_module('tests.{module}')"],
        cwd=PLUGIN_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    last_line = (result.stderr.strip().splitlines() or [""])[-1]
    return module, result.returncode, last_line


class TestsPackageImportContractTests(unittest.TestCase):
    def test_every_test_module_imports_as_tests_package(self) -> None:
        modules = sorted(p.stem for p in TESTS_DIR.glob("test_*.py"))
        self.assertGreater(len(modules), 100)
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(_import_as_tests_package, modules))
        failures = [f"{m}: {err}" for m, code, err in results if code != 0]
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()

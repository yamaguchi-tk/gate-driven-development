"""`sys.path.insert` → `from tasklist_parse import ...` → `sys.path.remove` パターンが
import 例外時にも `sys.path` を汚染しないことを固定する回帰テスト。

対象は `hooks/scripts/lib` を一時的に `sys.path` へ入れて `tasklist_parse` を
top-level module として読む 3 箇所（PR #32 の Copilot レビューで指摘）。
try/finally で保護していないと、import が例外を送出した場合に挿入した path が
残留し、同一プロセス内の後続 import 解決に副作用を及ぼす
（`tests/_plugin_module_loader.py` のヘッダー参照）。

`sys.modules["tasklist_parse"] = None` を仕込むと `from tasklist_parse import X` が
確実に ImportError を送出する（PEP 328 の仕様）ため、実ファイルを書き換えずに
import 失敗を注入できる。サブプロセスで実行して現在の interpreter の sys.path を
汚染しないようにする。
"""
from __future__ import annotations

import re
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
TESTS_DIR = Path(__file__).resolve().parent

TARGETS = (
    "scripts/collect-gdd-telemetry.py",
    "scripts/gdd_task_binding.py",
    "hooks/scripts/validate-steering-write.py",
)

# `sys.path.insert(0, X)` の全出現（変数名 X は問わない）。
_SYS_PATH_INSERT_RE = re.compile(r"sys\.path\.insert\(0,\s*(\w+)\)")
# 上記のうち、直後の try/finally で **同じ変数 X** を sys.path.remove している
# （＝保護済みの）もの。バックリファレンス `\1` で変数名に依存せず判定するため、
# `_LIB_DIR` という特定名にハードコードしない（`lib_dir` / `scripts_dir` のような
# 別名でも同じ判定になる）。`[\s\S]*?` は改行を跨いで非貪欲に走査するため、
# try 本体・finally 内のガード（`if X in sys.path:` 等）の行数やインデントに
# 依存しない。
_PROTECTED_INSERT_RE = re.compile(
    r"sys\.path\.insert\(0,\s*(\w+)\)\n"
    r"\s*try:\n"
    r"[\s\S]*?"
    r"\s*finally:\n"
    r"[\s\S]*?"
    r"sys\.path\.remove\(\1\)"
)


def _find_unprotected_sys_path_inserts(text: str) -> list[str]:
    """`sys.path.insert(0, X)` のうち、try/finally で同じ X を
    `sys.path.remove` していないものの変数名を返す（固定リストではなく構造で検知）。
    """
    all_vars = {m.group(1) for m in _SYS_PATH_INSERT_RE.finditer(text)}
    protected_vars = {m.group(1) for m in _PROTECTED_INSERT_RE.finditer(text)}
    return sorted(all_vars - protected_vars)


def _run_import_failure_probe(script_relative_path: str) -> tuple[str, str]:
    """`script_relative_path` を `tests/_plugin_module_loader.load_plugin_module`
    経由でロードしつつ `tasklist_parse` の import を強制失敗させ、
    (import 失敗の有無, sys.path 残留の有無) を返す。
    """
    code = textwrap.dedent(
        f"""
        import sys
        sys.path.insert(0, {str(TESTS_DIR)!r})
        from _plugin_module_loader import load_plugin_module
        sys.modules["tasklist_parse"] = None
        try:
            load_plugin_module({script_relative_path!r})
        except ImportError:
            print("IMPORTERROR")
        else:
            print("NO_IMPORT_ERROR")
        leaked = [p for p in sys.path if p.endswith("hooks/scripts/lib")]
        print("LEAKED" if leaked else "CLEAN")
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    lines = result.stdout.strip().splitlines()
    if len(lines) != 2:
        raise AssertionError(
            f"unexpected probe output for {script_relative_path}: "
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )
    return lines[0], lines[1]


class SysPathRollbackOnImportFailureContractTests(unittest.TestCase):
    """`tasklist_parse` の import が失敗しても `hooks/scripts/lib` が
    `sys.path` に残らないことを、対象スクリプトごとに固定する。
    """

    def test_target_scripts_do_not_leak_lib_dir_on_import_failure(self) -> None:
        for script in TARGETS:
            with self.subTest(script=script):
                import_status, leak_status = _run_import_failure_probe(script)
                self.assertEqual(import_status, "IMPORTERROR")
                self.assertEqual(leak_status, "CLEAN")

    def test_no_unprotected_sys_path_insert_remains(self) -> None:
        """`sys.path.insert(0, X)`（X は変数名を問わない）のうち、try/finally で
        保護されていない箇所が新たに増えていないことを固定する
        （固定リストではなく構造で検知する）。
        """
        unprotected: dict[str, list[str]] = {}
        for path in PLUGIN_ROOT.rglob("*.py"):
            if "/tests/" in path.as_posix():
                continue
            text = path.read_text(encoding="utf-8")
            missing = _find_unprotected_sys_path_inserts(text)
            if missing:
                unprotected[path.relative_to(PLUGIN_ROOT).as_posix()] = missing
        self.assertEqual(unprotected, {})


if __name__ == "__main__":
    unittest.main()

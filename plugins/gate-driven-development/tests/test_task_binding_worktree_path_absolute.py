"""resolver は `worktree_path` が絶対パスの文字列でない binding を、今の worktree に一致させない。

事象（2026-10-14 実測）: GDD を使う別の repo には `worktree_path` の無い旧書式の
binding.json が git に commit されていて、worktree を作るたびに各 worktree の registry へ
複製されていた（292 個）。resolver（`scripts/gdd_task_binding.py`）は `_norm("")` を
プロセスの cwd に解決するので、worktree の top で動く hook から見ると、この binding が
今の worktree に一致した。done guard（Stop hook）は、旧書式の binding だけが一致すると
`steering_path` の検証で落とし、本物の binding と 2 件で一致すると複数一致で、どちらも
conflict（warn だけで停止を通す）に倒れていた。

契約: `worktree_path` が空・欠落・相対パス・文字列でない binding は一致の候補にしない
（done guard の `_validate_binding` が `steering_path` に絶対パスだけを受理するのと同じ規約）。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _plugin_module_loader import load_plugin_module  # noqa: E402
from _stop_hook_test_base import (  # noqa: E402
    _UNFINISHED_TASKLIST,
    _bind,
    _make_two_worktree_fixture,
    _stop_done,
)

TARGET = "20260822-target"
LEGACY = "20260608-legacy"


def _write_binding(worktree: Path, task_id: str, data: dict) -> None:
    path = worktree / ".gdd" / "tasks" / task_id / "binding.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _legacy_binding(worktree: Path) -> None:
    # 事象の旧書式（`worktree` は placeholder の文字列で、`worktree_path`・`steering_path` が無い）。
    _write_binding(worktree, LEGACY, {
        "task_id": LEGACY,
        "steering_slug": LEGACY,
        "worktree": "<local-worktree>",
        "branch": f"codex/{LEGACY}",
        "repo_root": "<repo-root>",
        "status": "human-check-waiting",
    })


def _foreign(worktree_path):
    return {
        "task_id": LEGACY,
        "worktree_path": worktree_path,
        "steering_path": "",
        "branch": f"codex/{LEGACY}",
    }


class _Cwd:
    def __init__(self, path: Path):
        self.path = path

    def __enter__(self):
        self.old = os.getcwd()
        os.chdir(self.path)

    def __exit__(self, *exc):
        os.chdir(self.old)


class ResolverTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_plugin_module("scripts/gdd_task_binding.py")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        _wtA, self.wt = _make_two_worktree_fixture(Path(self.tmp.name))

    def _resolve(self):
        # hook と同じく、プロセスの cwd を worktree の top にして解決する。
        with _Cwd(self.wt):
            return self.mod.resolve_task(repo_root=self.wt, cwd=self.wt)

    def test_binding_without_absolute_worktree_path_is_not_matched(self):
        cases = {
            "旧書式（欄なし）": None,
            "空": "",
            "相対（.）": ".",
            "相対（名前）": "wtB",
            "文字列でない": 123,
            "リスト": [str(self.wt)],
        }
        for name, value in cases.items():
            with self.subTest(name):
                if value is None:
                    _legacy_binding(self.wt)
                else:
                    _write_binding(self.wt, LEGACY, _foreign(value))
                result = self._resolve()
                self.assertNotEqual(result.get("task_id"), LEGACY, result)
                self.assertNotEqual(result.get("status"), "resolved", result)

    def test_binding_whose_path_cannot_be_normalized_does_not_break_resolution(self):
        # NUL・孤立サロゲートは `realpath` の lstat が ValueError / UnicodeEncodeError を投げる。
        # 1 件で `resolve_task()` 全体が落ちると、done guard は conflict（warn）に下がる。
        _bind(self.wt)
        cases = {
            "worktree_path に NUL": {"worktree_path": "/x\u0000"},
            "worktree_path に孤立サロゲート": {"worktree_path": "/\ud800"},
            "steering_path が数値": {"worktree_path": "/nonexistent", "steering_path": 1},
            "steering_path に NUL": {"worktree_path": "/nonexistent", "steering_path": "/x\u0000"},
        }
        for name, fields in cases.items():
            with self.subTest(name):
                _write_binding(self.wt, LEGACY, {**_foreign(""), **fields})
                result = self._resolve()
                self.assertEqual(result.get("status"), "resolved", result)
                self.assertEqual(result.get("task_id"), TARGET, result)

    def test_binding_under_an_unreadable_directory_does_not_break_resolution(self):
        # Python 3.12 以前の `Path.exists()` は EACCES を投げ直す（3.13 以降は False を返す）。
        # 版に依らず分岐を通すため、その binding の `exists()` だけ PermissionError にする。
        _bind(self.wt)
        locked = Path(self.tmp.name) / "locked" / "wt"
        _write_binding(self.wt, LEGACY, _foreign(str(locked)))
        real_exists = Path.exists

        def exists(path, *args, **kwargs):
            # resolver は正規化した値（macOS では /var → /private/var）で exists() を呼ぶ。
            if os.path.realpath(path) == os.path.realpath(locked):
                raise PermissionError(13, "Permission denied", str(path))
            return real_exists(path, *args, **kwargs)

        with mock.patch.object(Path, "exists", exists):
            result = self._resolve()
        self.assertEqual(result.get("status"), "resolved", result)
        self.assertEqual(result.get("task_id"), TARGET, result)

    def test_cli_output_survives_a_lone_surrogate_in_an_unmatched_binding(self):
        # 一致しない binding の値も `invalid_bindings`・`candidates` として出力に載る。
        # strict な UTF-8 の stdout で print が落ちると、detect-steering.sh・gate-ledger.sh は
        # 空出力として fallback に進む。
        _bind(self.wt)
        _write_binding(self.wt, LEGACY, {"task_id": "\ud800", "worktree_path": "/\udcff"})
        script = Path(__file__).resolve().parents[1] / "scripts" / "gdd_task_binding.py"
        proc = subprocess.run(
            [sys.executable, str(script), "resolve", "--repo-root", str(self.wt), "--cwd", str(self.wt)],
            capture_output=True, cwd=self.wt,
            env={**os.environ, "PYTHONIOENCODING": "utf-8:strict"},
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result.get("status"), "resolved", result)
        self.assertEqual(result.get("task_id"), TARGET, result)

    def test_tilde_worktree_path_is_not_matched(self):
        # HOME を worktree の親にすると、`~/<名前>` は展開すれば今の worktree になる。
        _write_binding(self.wt, LEGACY, _foreign(f"~/{self.wt.name}"))
        with mock.patch.dict(os.environ, {"HOME": str(self.wt.parent)}):
            result = self._resolve()
        self.assertNotEqual(result.get("task_id"), LEGACY, result)

    def test_real_binding_resolves_beside_a_binding_without_worktree_path(self):
        _bind(self.wt)
        for name, value in {"旧書式": None, "空": "", "相対": ".", "文字列でない": 123}.items():
            with self.subTest(name):
                if value is None:
                    _legacy_binding(self.wt)
                else:
                    _write_binding(self.wt, LEGACY, _foreign(value))
                result = self._resolve()
                self.assertEqual(result.get("status"), "resolved", result)
                self.assertEqual(result.get("task_id"), TARGET, result)


class DoneGuardTests(unittest.TestCase):
    """入口（Stop hook）から: 本物の binding の未完了 tasklist で止まる。

    worktree に steering を 2 つ置く。steering が 1 つだけなら、bind が conflict でも
    done guard はその 1 つを検査する（`resolve_guard_tasklist` の fallback）ので、欠陥が見えない。
    """

    def _fixture(self, tmp):
        _wtA, wt = _make_two_worktree_fixture(Path(tmp))
        (wt / ".steering" / TARGET / "tasklist.md").write_text(_UNFINISHED_TASKLIST, encoding="utf-8")
        other = wt / ".steering" / "20260823-other"
        other.mkdir(parents=True)
        (other / "tasklist.md").write_text(_UNFINISHED_TASKLIST, encoding="utf-8")
        _bind(wt)
        return wt

    def test_fixture_blocks_with_only_the_real_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            wt = self._fixture(tmp)
            _code, out, err = _stop_done(wt)
            self.assertIn('"decision": "block"', out, f"out={out}\nerr={err}")
            self.assertIn(str(wt / ".steering" / TARGET), out)

    def test_legacy_binding_beside_the_real_one_does_not_turn_the_block_into_a_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            wt = self._fixture(tmp)
            _legacy_binding(wt)
            _code, out, err = _stop_done(wt)
            self.assertIn('"decision": "block"', out, f"out={out}\nerr={err}")
            self.assertIn(str(wt / ".steering" / TARGET), out)

    def test_binding_with_a_non_string_worktree_path_does_not_disable_the_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            wt = self._fixture(tmp)
            _write_binding(wt, LEGACY, _foreign(123))
            _code, out, err = _stop_done(wt)
            self.assertIn('"decision": "block"', out, f"out={out}\nerr={err}")
            self.assertIn(str(wt / ".steering" / TARGET), out)

    def test_binding_with_an_unnormalizable_steering_path_does_not_disable_the_guard(self):
        for name, value in {"数値": 1, "NUL": "/x\u0000"}.items():
            with self.subTest(name), tempfile.TemporaryDirectory() as tmp:
                wt = self._fixture(tmp)
                _write_binding(wt, LEGACY, {**_foreign("/nonexistent"), "steering_path": value})
                _code, out, err = _stop_done(wt)
                self.assertIn('"decision": "block"', out, f"out={out}\nerr={err}")
                self.assertIn(str(wt / ".steering" / TARGET), out)

    def test_binding_json_that_overflows_the_parser_does_not_disable_the_guard(self):
        # 深い入れ子は `json.loads` が RecursionError（ValueError ではない）を投げる。
        with tempfile.TemporaryDirectory() as tmp:
            wt = self._fixture(tmp)
            path = wt / ".gdd" / "tasks" / LEGACY / "binding.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("[" * 1_000_000, encoding="utf-8")
            _code, out, err = _stop_done(wt)
            self.assertIn('"decision": "block"', out, f"out={out}\nerr={err}")
            self.assertIn(str(wt / ".steering" / TARGET), out)


if __name__ == "__main__":
    unittest.main()

"""`tests/_timing_budget.py`（`timing_budget()` / `hook_timeout_seconds()` / `hang_guard_seconds()`）の契約テスト。

実行:
  python3 -m pytest plugins/gate-driven-development/tests/test_timing_budget_contract.py -v

`_timing_budget.py` は性能回帰テスト 5 本（`T`）の CPU/壁時計計測と、
`run_root_branch_guard` などの subprocess の打ち切り（`hang_guard_seconds()`）の唯一の導出元。
本ファイルは、この導出元を作ったときの completion-check で検出された testing gap
（このヘルパー自体を固定する契約テストが 0 本だった）を埋める。5 本の
テストファイル側は「timing_budget() を呼べば数値が返る」ことしか間接的に
確認しておらず、fail-loud 分岐（未確定値の早期読み出し・timeout 解決不能）
はどのテストからも直接検証されていなかった。

本ファイルが固定すること:
- `timing_budget()` の with ブロック内で `cpu_seconds` / `wall_seconds` を
  読むと `RuntimeError`（design.md M-2「未確定状態を持たせない」契約）
- with ブロック退出後は両方とも `float` かつ `>= 0`
- **`cpu_seconds` は孫プロセスの CPU も捕捉する**（`RUSAGE_CHILDREN` 項が
  無いと、subprocess ベースの #1/#2/#3 の CPU assert が恒真の dead
  assertion になり、mutation 実測（impl-gate）で
  実際に検出された退行）
- **`cpu_seconds` は自プロセス内の CPU も捕捉する**（`time.process_time()`
  項が無いと、in-process 計測の #4/#5 の CPU assert が恒真の dead
  assertion になる。上の `RUSAGE_CHILDREN` 欠落の鏡像側で、
  completion-check の mutation 実測で検出された。計測式の
  両項がそれぞれ独立に mutation で固定されている）
- **`wall_seconds` は CPU を消費しない待機（`sleep`）も捕捉する**が
  `cpu_seconds` はほぼ 0 のままで、両者が別の性質を測っていることを固定する
- `hook_timeout_seconds()` は一意な hit で該当 timeout を返す
- `hook_timeout_seconds()` は 0 hit で `LookupError`（fail-loud、既定値
  フォールバックなし）
- `hook_timeout_seconds()` は 2+ hit が timeout 不一致のとき `LookupError`
- `hook_timeout_seconds()` は timeout が非数値・0 以下のとき `LookupError`
- `hang_guard_seconds()` は hooks.json の timeout の 6 倍を返し、
  `run_root_branch_guard` の既定の打ち切りと `run_root_branch_guard_raw` の打ち切りはその値である
- `hang_guard_seconds()` は 0 hit で `LookupError`（既定値フォールバックなし）

Contract Surface Coverage（`_timing_budget.py` の 3 関数。外部 API 呼び出しなし）:
- success path: applicable -> `TimingBudgetTests.test_normal_usage_returns_nonnegative_floats` /
  `test_cpu_seconds_captures_child_process_cpu` / `test_cpu_seconds_captures_in_process_cpu` /
  `test_wall_seconds_captures_sleep_that_cpu_seconds_does_not` /
  `HookTimeoutSecondsTests.test_unique_hit_returns_its_timeout` /
  `HangGuardSecondsTests.test_six_times_the_synthetic_timeout` /
  `test_root_branch_guard_helper_defaults_to_the_hang_guard` /
  `test_root_branch_guard_raw_helper_uses_the_hang_guard`
- no-op / silent success path: not_applicable（既定値フォールバックを持たない設計そのものが
  本ファイルの検証対象）
- external API response variants: applicable -> `HookTimeoutSecondsTests`（合成 `hooks.json` の
  0 hit / 複数 hit 一致 / 複数 hit 不一致 / 非数値 timeout / timeout<=0 の 5 形）
- external API failure / unavailable path: not_applicable（`hooks.json` はローカルファイルで
  ネットワーク等の外部依存を持たない）
- validation / sanitize / fail-closed path: applicable -> `TimingBudgetTests.test_reading_cpu_seconds_before_exit_raises` /
  `test_reading_wall_seconds_before_exit_raises` / `HookTimeoutSecondsTests` 全 fail-loud ケース /
  `HangGuardSecondsTests.test_zero_hit_raises_without_a_fallback`
- formatting / output schema path: not_applicable（構造化出力契約なし。戻り値は number 型のみ）
- duplicate / idempotency / lock path: not_applicable（状態を持たないヘルパー）
- user-visible side effect path: not_applicable（純粋な計測ヘルパーで副作用なし）
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import _root_branch_guard_support
from _timing_budget import hang_guard_seconds, hook_timeout_seconds, timing_budget


class TimingBudgetTests(unittest.TestCase):
    def test_normal_usage_returns_nonnegative_floats(self):
        with timing_budget() as t:
            sum(range(200_000))
        self.assertIsInstance(t.cpu_seconds, float)
        self.assertIsInstance(t.wall_seconds, float)
        self.assertGreaterEqual(t.cpu_seconds, 0.0)
        self.assertGreaterEqual(t.wall_seconds, 0.0)

    def test_cpu_seconds_captures_child_process_cpu(self):
        """#1/#2/#3 は subprocess（`_run_guard` / `_run_hook`）越しに CPU を測る。

        `cpu_seconds` が `RUSAGE_CHILDREN` を含まず自プロセスの
        `time.process_time()` だけになる mutation（impl-gate で
        実測確認）が入ると、`subprocess.run` を待つだけの
        親プロセスの CPU はほぼ 0 のままになり、退行（子プロセス側の CPU
        律速の遅さ）を検出できない恒真の dead assertion になる。子プロセスに
        測定可能な量の計算をさせ、その CPU が確実に計上されることを固定する。
        """
        with timing_budget() as t:
            subprocess.run(
                [sys.executable, "-c", "sum(range(30_000_000))"],
                check=True,
            )
        # 子プロセスの計算量は環境で変動するため、mutation 時の値
        # （自プロセスの CPU がほぼ 0 になる）から明確に離れた閾値にする。
        self.assertGreater(
            t.cpu_seconds,
            0.02,
            msg=(
                f"cpu_seconds={t.cpu_seconds:.4f}s: 子プロセスの CPU が"
                " 捕捉されていない可能性（RUSAGE_CHILDREN 欠落 mutation）"
            ),
        )

    def test_cpu_seconds_captures_in_process_cpu(self):
        """#4/#5 は subprocess を起動せず in-process で CPU を測る。

        `cpu_seconds` が自プロセスの `time.process_time()` 項を含まず
        `RUSAGE_CHILDREN`（常に子プロセス 0 件で 0）だけになる mutation
        （completion-check で実測確認。上の mutation の鏡像側の
        欠落）が入ると、in-process の CPU 律速の遅さ（#4/#5 が検出対象と
        する退行）を測れず `cpu_seconds` が恒等的に 0.0 になり、
        `assertLess(cpu, …)` が恒真の dead assertion になる。
        """
        with timing_budget() as t:
            sum(range(30_000_000))
        self.assertGreater(
            t.cpu_seconds,
            0.02,
            msg=(
                f"cpu_seconds={t.cpu_seconds:.4f}s: in-process の CPU が"
                " 捕捉されていない可能性（time.process_time() 欠落 mutation）"
            ),
        )

    def test_wall_seconds_captures_sleep_that_cpu_seconds_does_not(self):
        """CPU を消費しない待機は `wall_seconds` にだけ反映される。

        `wall_seconds` が `cpu_seconds` のエイリアスになる mutation が入ると、
        壁時計 backstop（#1〜#5 共通）が CPU 側閾値と同じ値になり、独立した
        性質を守れなくなる。両者が別の量を測っていることを直接固定する。
        """
        with timing_budget() as t:
            time.sleep(0.3)
        self.assertGreaterEqual(t.wall_seconds, 0.25)
        self.assertLess(t.cpu_seconds, 0.1)

    def test_reading_cpu_seconds_before_exit_raises(self):
        with timing_budget() as t:
            with self.assertRaises(RuntimeError):
                t.cpu_seconds

    def test_reading_wall_seconds_before_exit_raises(self):
        with timing_budget() as t:
            with self.assertRaises(RuntimeError):
                t.wall_seconds

    def test_values_settle_even_when_block_raises(self):
        """`with` ブロック内で例外が飛んでも `finally` で確定させる（design.md 契約）。"""
        t_ref = None
        with self.assertRaises(ValueError):
            with timing_budget() as t:
                t_ref = t
                raise ValueError("boom")
        self.assertGreaterEqual(t_ref.cpu_seconds, 0.0)
        self.assertGreaterEqual(t_ref.wall_seconds, 0.0)


def _write_hooks_json(root: Path, hooks: list[dict]) -> None:
    hooks_dir = root / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    payload = {"hooks": {"PreToolUse": [{"hooks": hooks}]}}
    (hooks_dir / "hooks.json").write_text(json.dumps(payload), encoding="utf-8")


class HookTimeoutSecondsTests(unittest.TestCase):
    """合成 `hooks.json` で `hook_timeout_seconds()` の fail-loud 分岐を直接固定する。

    本番の `hooks.json` は timeout 不一致・非数値等の異常形を持たないため、
    `_timing_budget.PLUGIN_ROOT` を一時ディレクトリへ差し替えて合成する。
    """

    def _run_with_synthetic_root(self, hooks: list[dict], script_basename: str):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_hooks_json(root, hooks)
            with mock.patch("_timing_budget.PLUGIN_ROOT", root):
                return hook_timeout_seconds(script_basename)

    def test_unique_hit_returns_its_timeout(self):
        result = self._run_with_synthetic_root(
            [{"command": "bash run-merge-gate-hook.sh", "timeout": 10}],
            "run-merge-gate-hook.sh",
        )
        self.assertEqual(result, 10.0)

    def test_multiple_agreeing_hits_return_the_shared_timeout(self):
        result = self._run_with_synthetic_root(
            [
                {"command": "bash a/run-merge-gate-hook.sh", "timeout": 10},
                {"command": "bash b/run-merge-gate-hook.sh", "timeout": 10},
            ],
            "run-merge-gate-hook.sh",
        )
        self.assertEqual(result, 10.0)

    def test_zero_hits_raise_lookup_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_hooks_json(root, [{"command": "bash other.sh", "timeout": 10}])
            with mock.patch("_timing_budget.PLUGIN_ROOT", root):
                with self.assertRaises(LookupError):
                    hook_timeout_seconds("no-such-script.sh")

    def test_disagreeing_hits_raise_lookup_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_hooks_json(
                root,
                [
                    {"command": "bash a/run-merge-gate-hook.sh", "timeout": 10},
                    {"command": "bash b/run-merge-gate-hook.sh", "timeout": 5},
                ],
            )
            with mock.patch("_timing_budget.PLUGIN_ROOT", root):
                with self.assertRaises(LookupError):
                    hook_timeout_seconds("run-merge-gate-hook.sh")

    def test_non_numeric_timeout_raises_lookup_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_hooks_json(
                root, [{"command": "bash run-merge-gate-hook.sh", "timeout": "soon"}]
            )
            with mock.patch("_timing_budget.PLUGIN_ROOT", root):
                with self.assertRaises(LookupError):
                    hook_timeout_seconds("run-merge-gate-hook.sh")

    def test_zero_or_negative_timeout_raises_lookup_error(self):
        for bad_timeout in (0, -1):
            with self.subTest(timeout=bad_timeout):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    _write_hooks_json(
                        root,
                        [{"command": "bash run-merge-gate-hook.sh", "timeout": bad_timeout}],
                    )
                    with mock.patch("_timing_budget.PLUGIN_ROOT", root):
                        with self.assertRaises(LookupError):
                            hook_timeout_seconds("run-merge-gate-hook.sh")

    def test_bool_timeout_raises_lookup_error(self):
        """`bool` は `int` のサブクラスなので、明示的に除外していることを固定する。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_hooks_json(
                root, [{"command": "bash run-merge-gate-hook.sh", "timeout": True}]
            )
            with mock.patch("_timing_budget.PLUGIN_ROOT", root):
                with self.assertRaises(LookupError):
                    hook_timeout_seconds("run-merge-gate-hook.sh")


class HangGuardSecondsTests(unittest.TestCase):
    """hook を起動するテストの壁時計の打ち切りは、hooks.json の timeout の 6 倍から導く。"""

    def test_six_times_the_synthetic_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_hooks_json(root, [{"command": "bash run-x.sh", "timeout": 7}])
            with mock.patch("_timing_budget.PLUGIN_ROOT", root):
                self.assertEqual(hang_guard_seconds("run-x.sh"), 42.0)

    def test_root_branch_guard_helper_defaults_to_the_hang_guard(self):
        seen = []

        def fake_run(*args, **kwargs):
            seen.append(kwargs.get("timeout"))
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as tmp, mock.patch("subprocess.run", side_effect=fake_run):
            _root_branch_guard_support.run_root_branch_guard(Path(tmp), "ls")
        self.assertEqual(seen, [hook_timeout_seconds("run-worktree-command-guard.sh") * 6])

    def test_root_branch_guard_raw_helper_uses_the_hang_guard(self):
        seen = []

        def fake_run(*args, **kwargs):
            seen.append(kwargs.get("timeout"))
            return subprocess.CompletedProcess(args, 0, stdout=b"", stderr=b"")

        with mock.patch("subprocess.run", side_effect=fake_run):
            _root_branch_guard_support.run_root_branch_guard_raw(b"{}")
        self.assertEqual(seen, [hook_timeout_seconds("run-worktree-command-guard.sh") * 6])

    def test_zero_hit_raises_without_a_fallback(self):
        # 既定値に倒すと、hook 名の typo や hooks.json の構造変更で打ち切りが黙って別の値になる
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_hooks_json(root, [{"command": "bash run-x.sh", "timeout": 7}])
            with mock.patch("_timing_budget.PLUGIN_ROOT", root):
                with self.assertRaises(LookupError):
                    hang_guard_seconds("run-missing.sh")


if __name__ == "__main__":
    unittest.main()

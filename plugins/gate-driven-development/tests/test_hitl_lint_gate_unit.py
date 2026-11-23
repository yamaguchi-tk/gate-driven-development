"""Unit tests for lib.hitl_lint_gate (HITL lint 配線).

既存の6本のHITL品質lintは判定ロジックとして正しく動くが、呼び出し手順がどこにも
無いため実運用でほぼ実行されない。本モジュールは
新しい判定ロジックを一切追加せず、既存の3本（display-integrity / human-check-
language / complexity）を human-check-waiting の Stop hook 経路から呼び出す配線
だけを担う。decision-quality（自由文trigger-wordによる偽陽性）・stage-plan
（自由文寄りの節内容判定でlintの適用範囲外の書き方まで正誤を強制する）・
outcome-audit（対象アーティファクトが最終HITL本文と異なる）はv1の配線対象から
意図的に除外している（`hooks/scripts/lib/hitl_lint_gate.py`のモジュール
docstring / CHANGELOGに実測根拠を記録）。

lint を通らない HITL も差し戻さず、結果を記録し、ユーザーに見せる警告文を返す
（経緯は`hitl_lint_gate.py`のモジュールdocstring）。

Run from plugins/gate-driven-development/:
  python3 -m unittest tests.test_hitl_lint_gate_unit -v
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "hooks" / "scripts"))

from lib.hitl_lint_gate import HITL_MARKER, enforce_hitl_lint_gate, run_hitl_lints, should_score_hitl_text

from _paths import PLUGIN_ROOT
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "hitl-lint-gate"
GOLD_PASS_TEXT = (FIXTURE_DIR / "gold-pass.md").read_text(encoding="utf-8")
QUALITY_FAIL_TEXT = (FIXTURE_DIR / "quality-fail.md").read_text(encoding="utf-8")


class ShouldScoreHitlTextTests(unittest.TestCase):
    """前段ガード: 実際に human-check-waiting の最終HITL面だけを採点する。"""

    def test_true_when_reason_matches_and_marker_present(self):
        text = f"## 確認\n...\n{HITL_MARKER}"
        self.assertTrue(should_score_hitl_text("human-check-waiting", text))

    def test_false_when_reason_is_not_human_check_waiting(self):
        text = f"## 完了\n...\n<gdd-stop reason=\"done\">"
        self.assertFalse(should_score_hitl_text("done", text))

    def test_false_when_marker_absent_from_last_output(self):
        """tool_result にしかマーカーが無い、または markerless fallback 経路。

        display-integrity lint 自身が守ろうとしている面（main session が
        subagent の HITL を再要約して削った状態）を、ここで誤って採点しない。
        last_output にマーカーが無いテキストを採点対象にすると、無関係な
        テキストを HITL として lint することになる。
        """
        text = "適当な継続テキストです。マーカーはありません。"
        self.assertFalse(should_score_hitl_text("human-check-waiting", text))


class RunHitlLintsTests(unittest.TestCase):
    """3本のlintを実際に起動して結果を集約する層。判定ロジックそのものは変えない。"""

    def test_gold_fixture_passes_all_wired_lints(self):
        """配線前提: 3本を同時に通すHITL実例が存在する（RED時点ではこれが無かった）。"""
        failures, errors = run_hitl_lints(PLUGIN_ROOT, GOLD_PASS_TEXT)
        self.assertEqual(failures, [], f"gold fixture should pass all wired lints, got: {failures}")
        self.assertEqual(errors, [], f"gold fixture should not error, got: {errors}")

    def test_quality_fail_fixture_fails_at_least_one_wired_lint(self):
        failures, errors = run_hitl_lints(PLUGIN_ROOT, QUALITY_FAIL_TEXT)
        failed_names = {name for name, _ in failures}
        self.assertIn("lint-hitl-display-integrity", failed_names)
        self.assertIn("lint-human-check-language", failed_names)
        self.assertEqual(errors, [])

    def test_missing_lint_script_is_an_error_not_a_failure(self):
        """fail-open: lint 自体を実行できない状態は「内容不良」と区別する。"""
        with tempfile.TemporaryDirectory() as tmp:
            fake_root = Path(tmp)
            (fake_root / "scripts").mkdir()
            # 3本のうち1本だけ用意し、残り2本は無い状態を作る。
            real_script = PLUGIN_ROOT / "scripts" / "lint-hitl-complexity.py"
            (fake_root / "scripts" / "lint-hitl-complexity.py").write_text(
                real_script.read_text(encoding="utf-8"), encoding="utf-8"
            )
            lib_dir = fake_root / "scripts" / "lib"
            lib_dir.mkdir()
            for name in ("lint_base.py", "hitl_budget.py", "__init__.py"):
                src = PLUGIN_ROOT / "scripts" / "lib" / name
                if src.exists():
                    (lib_dir / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
                else:
                    (lib_dir / name).write_text("", encoding="utf-8")

            failures, errors = run_hitl_lints(fake_root, GOLD_PASS_TEXT)
            self.assertEqual(failures, [])
            error_names = {e.split(":", 1)[0] for e in errors}
            self.assertIn("lint-hitl-display-integrity", error_names)
            self.assertIn("lint-human-check-language", error_names)
            self.assertNotIn("lint-hitl-complexity", error_names)

    def test_all_scripts_missing_reports_one_summary_error_not_three(self):
        """独立レビュー finding 12: plugin_root未解決環境（＝配線対象3本が
        全滅）でHITL 1回あたりhook-errors.logに3行積まれるのを避ける。
        3本とも見つからない場合は1行に集約する。"""
        with tempfile.TemporaryDirectory() as tmp:
            fake_root = Path(tmp)
            (fake_root / "scripts").mkdir()
            failures, errors = run_hitl_lints(fake_root, GOLD_PASS_TEXT)
            self.assertEqual(failures, [])
            self.assertEqual(len(errors), 1, f"expected 1 summary error, got: {errors}")


class EnforceHitlLintGateTests(unittest.TestCase):
    """try_stop_with_done_guard から呼ばれるエントリポイント全体の振る舞い。
    どの入力でも stdout に書かず、SystemExit も投げない（停止を止めない）。"""

    def _run_and_capture(self, *args, **kwargs):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            try:
                warning = enforce_hitl_lint_gate(*args, **kwargs)
            except SystemExit:  # pragma: no cover - テストが失敗を報告する
                self.fail("enforce_hitl_lint_gate must not exit")
        self.assertEqual(buf.getvalue(), "")
        return warning

    def _log(self, proj_root: Path, name: str = "hook-errors.log") -> str:
        log_path = proj_root / ".gdd" / name
        return log_path.read_text(encoding="utf-8") if log_path.exists() else ""

    def test_failing_hitl_returns_a_warning_and_logs_without_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj_root = Path(tmp)
            text = f"{QUALITY_FAIL_TEXT}\n{HITL_MARKER}"
            for _ in range(3):
                warning = self._run_and_capture(
                    proj_root, "human-check-waiting", text, plugin_root=PLUGIN_ROOT,
                )
                self.assertIn("lint-hitl-display-integrity", warning)
            self.assertFalse((proj_root / ".claude").exists(), "state に何も書かない")

    def test_warning_carries_the_lint_head_and_detail_lines(self):
        """警告文には lint の最初の行と詳細行（`- ` で始まる行）を載せる。期待値は lint を直接走らせた出力から取る。"""
        script = PLUGIN_ROOT / "scripts" / "lint-hitl-display-integrity.py"
        direct = subprocess.run([sys.executable, str(script), str(FIXTURE_DIR / "quality-fail.md")],
                                capture_output=True, text=True, check=False).stdout.splitlines()
        details = [line for line in direct if line.startswith("- ")]
        with tempfile.TemporaryDirectory() as tmp:
            warning = self._run_and_capture(
                Path(tmp), "human-check-waiting", f"{QUALITY_FAIL_TEXT}\n{HITL_MARKER}", plugin_root=PLUGIN_ROOT,
            )
        self.assertIn(direct[0], warning)
        self.assertIn(details[0], warning)
        self.assertNotIn(details[3], warning, "詳細行は lint ごとに 3 行まで")

    def test_lint_failures_go_to_their_own_log_not_hook_errors(self):
        """lint を通らない HITL は日常的に出るので、故障の記録（hook-errors.log）を埋めない。全文は hitl-lint.log に残す。"""
        with tempfile.TemporaryDirectory() as tmp:
            proj_root = Path(tmp)
            self._run_and_capture(
                proj_root, "human-check-waiting", f"{QUALITY_FAIL_TEXT}\n{HITL_MARKER}", plugin_root=PLUGIN_ROOT,
            )
            self.assertNotIn("lint-hitl-display-integrity", self._log(proj_root))
            records = [json.loads(line) for line in self._log(proj_root, "hitl-lint.log").splitlines()]
            display = [r for r in records if r["message"].startswith("lint-hitl-display-integrity:")]
            self.assertEqual(len(display), 1)
            self.assertGreater(len(display[0]["message"].splitlines()), 4, "全文を残す")

    def test_warning_does_not_advertise_self_serve_bypass_to_the_model(self):
        """環境変数での無効化は人間の判断で使うもので、警告文で案内しない。"""
        with tempfile.TemporaryDirectory() as tmp:
            warning = self._run_and_capture(
                Path(tmp), "human-check-waiting", f"{QUALITY_FAIL_TEXT}\n{HITL_MARKER}",
                plugin_root=PLUGIN_ROOT,
            )
            self.assertNotIn("GDD_SKIP_HITL_LINT", warning)

    def test_plugin_root_resolution_failure_is_fail_open_not_a_crash(self):
        """`_resolve_plugin_root()`（os.getcwdを含む）が例外を投げても落ちず、記録して空を返す。"""
        import unittest.mock as mock

        with tempfile.TemporaryDirectory() as tmp:
            proj_root = Path(tmp)
            with mock.patch(
                "lib.hitl_lint_gate._resolve_plugin_root",
                side_effect=OSError("cwd is gone"),
            ):
                warning = self._run_and_capture(
                    proj_root, "human-check-waiting", f"{QUALITY_FAIL_TEXT}\n{HITL_MARKER}",
                )
            self.assertEqual(warning, "")
            self.assertIn("cwd is gone", self._log(proj_root))

    def test_skip_env_var_bypasses_everything(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj_root = Path(tmp)
            old = os.environ.get("GDD_SKIP_HITL_LINT")
            os.environ["GDD_SKIP_HITL_LINT"] = "1"
            try:
                warning = self._run_and_capture(
                    proj_root, "human-check-waiting", f"## 確認\n{QUALITY_FAIL_TEXT}\n{HITL_MARKER}",
                    plugin_root=PLUGIN_ROOT,
                )
            finally:
                if old is None:
                    os.environ.pop("GDD_SKIP_HITL_LINT", None)
                else:
                    os.environ["GDD_SKIP_HITL_LINT"] = old
            self.assertEqual(warning, "")
            self.assertEqual(self._log(proj_root), "")

    def test_reason_not_human_check_waiting_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self._run_and_capture(
                Path(tmp), "done", QUALITY_FAIL_TEXT, plugin_root=PLUGIN_ROOT,
            ), "")

    def test_marker_absent_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self._run_and_capture(
                Path(tmp), "human-check-waiting", "マーカーなしテキスト", plugin_root=PLUGIN_ROOT,
            ), "")

    def test_a_passing_hitl_returns_no_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self._run_and_capture(
                Path(tmp), "human-check-waiting", GOLD_PASS_TEXT, plugin_root=PLUGIN_ROOT,
            ), "")


if __name__ == "__main__":
    unittest.main()

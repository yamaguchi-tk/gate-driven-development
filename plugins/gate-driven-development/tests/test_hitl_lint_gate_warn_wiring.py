"""Unit tests for the warn-only HITL lint wiring.

方針メモ（2026-09-15、ユーザー確認）: `lint-hitl-required-fields.py`
（該当なし明記 + Option軸必須）は `HITL_LINT_SCRIPTS` とは別の
`HITL_LINT_WARN_SCRIPTS` として配線する。契約は次の2点:
  1. hook-errors.log には記録される（＝実際に発火することを実測できる）
  2. 警告文（systemMessage）にも block にも出さない（stdout に何も書かない）

Run from plugins/gate-driven-development/:
  python3 -m unittest tests.test_hitl_lint_gate_warn_wiring -v
"""
from __future__ import annotations

import contextlib
import inspect
import io
import sys
import tempfile
import time
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "hooks" / "scripts"))

from lib.hitl_lint_gate import (  # noqa: E402
    HITL_LINT_WARN_SCRIPTS,
    HITL_MARKER,
    _run_and_log_warn_lints,
    enforce_hitl_lint_gate,
    run_hitl_lints,
)

from _paths import PLUGIN_ROOT

# 4節を丸ごと欠き、Option 軸も無い最小の HITL（lint-hitl-required-fields.py が
# 必ず exit 1 になるテキスト）。ただし block 対象3本（display-integrity /
# human-check-language / complexity）は通すため、それらが要求する固定語は
# 満たしておく（このテストが確認したいのは warn 経路だけを単離することであり、
# block 経路を巻き込んで結果を混同しないため）。
_BLOCK_LINT_COMPLIANT_BUT_WARN_NONCOMPLIANT_TEXT = f"""\
## 確認

### なぜやるか（WHY・根本原因）
テストのためのダミー本文です。

### 何を作るか（整理した要件）
整理した要件のダミーです。

### どう作るか（実装する方法・内容）
実装する方法・内容のダミーです。

**変更予定ファイル（WHERE）**: dummy.py

### どう確かめるか（検証する方法・内容）
検証する方法・内容のダミーです。

### 現在地
完了フェーズ: dummy / 今やること: OK 判断 / OK後: dummy / 残タスク: dummy

### どこまで自走するか（どこまで自走するのか）
- OKで進む範囲: dummy
- OKでも許可されないこと: merge / deploy
- 人間に戻す条件: scope / AC が変わる場合

### 判断ポイント
1. ダミー判断 — 変更前: dummy / 変更後: dummy / 採用しない案: dummy
   - この案を選ぶと次に何が起きるか: dummy
   - 無回答時のデフォルト: dummy

### 段階実装（段階実装サマリー）
single-stage: dummy

### ズレ確認
完了条件の変換: dummy zure kakunin content that is long enough.

{HITL_MARKER}
"""


class RunHitlLintsWithWarnScriptsTests(unittest.TestCase):
    """`run_hitl_lints(scripts=HITL_LINT_WARN_SCRIPTS)` が実際に配線対象を実行する。"""

    def test_noncompliant_text_is_reported_as_a_warn_finding(self):
        failures, errors = run_hitl_lints(
            PLUGIN_ROOT, "## 確認\n\n" + HITL_MARKER, scripts=HITL_LINT_WARN_SCRIPTS
        )
        self.assertEqual(errors, [])
        names = {name for name, _ in failures}
        self.assertIn("lint-hitl-required-fields", names)

    def test_compliant_text_produces_no_warn_findings(self):
        compliant = (
            "## 確認\n\n- 依頼との差: なし\n\n"
            '<gdd-hitl-fields options="none" arch="none" zure="none" multi-pr="none" stage="filled" request-diff="none">\n\n'
            + HITL_MARKER
        )
        failures, errors = run_hitl_lints(PLUGIN_ROOT, compliant, scripts=HITL_LINT_WARN_SCRIPTS)
        self.assertEqual(failures, [])
        self.assertEqual(errors, [])


class EnforceHitlLintGateWarnTests(unittest.TestCase):
    """`enforce_hitl_lint_gate` 経路での warn ログ記録と非 block を確認する。"""

    def _run_and_capture(self, *args, **kwargs):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            try:
                enforce_hitl_lint_gate(*args, **kwargs)
                exited = False
            except SystemExit as exc:
                exited = True
                self.assertEqual(exc.code, 0)
        return exited, buf.getvalue()


    def test_warn_finding_is_logged_but_does_not_block_or_consume_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj_root = Path(tmp)
            exited, out = self._run_and_capture(
                proj_root,
                "human-check-waiting",
                _BLOCK_LINT_COMPLIANT_BUT_WARN_NONCOMPLIANT_TEXT,
                plugin_root=PLUGIN_ROOT,
            )
            # block対象3本は満たしているので block されない（このテキストが
            # warn 経路だけを踏むことを担保する前提）。
            self.assertFalse(exited, f"should not block, but got: {out}")
            self.assertEqual(out, "")

            log_path = proj_root / ".gdd" / "hook-errors.log"
            self.assertTrue(log_path.exists(), "warn finding should be logged to hook-errors.log")
            log_text = log_path.read_text(encoding="utf-8")
            self.assertIn("lint-hitl-required-fields", log_text)

    def test_fully_compliant_hitl_leaves_no_warn_trace(self):
        compliant = (
            _BLOCK_LINT_COMPLIANT_BUT_WARN_NONCOMPLIANT_TEXT.replace(HITL_MARKER, "")
            + '<gdd-hitl-fields options="none" arch="none" zure="none" multi-pr="none" stage="filled">\n\n'
            + HITL_MARKER
        )
        with tempfile.TemporaryDirectory() as tmp:
            proj_root = Path(tmp)
            exited, out = self._run_and_capture(
                proj_root, "human-check-waiting", compliant,
                plugin_root=PLUGIN_ROOT,
            )
            self.assertFalse(exited)
            self.assertEqual(out, "")
            log_path = proj_root / ".gdd" / "hook-errors.log"
            if log_path.exists():
                self.assertNotIn(
                    "lint-hitl-required-fields", log_path.read_text(encoding="utf-8")
                )


class SharedDeadlineBudgetRegressionTests(unittest.TestCase):
    """独立レビュー finding（high/fail-open）: `enforce_hitl_lint_gate` は
    block パス（既存3本）と warn パス（`lint-hitl-required-fields`）の両方で
    `run_hitl_lints` を呼ぶ。修正前は呼び出しごとに新しい
    `_TOTAL_BUDGET_SECONDS` の予算を確保しており、合計の subprocess 実行
    時間が Stop hook 全体の timeout（`hooks.json` で10秒）に近づき、追加した
    warn パスのせいで既存の HITL lint の block ゲート自体が timeout により到達不能に
    なりうる構造だった。修正後は `enforce_hitl_lint_gate` が単一の
    `shared_deadline` を計算し、両方の `run_hitl_lints` 呼び出しに明示的に
    渡す。ここでは `run_hitl_lints` / `_run_and_log_warn_lints` が `deadline`
    を実際に受け取り尊重すること（新しい独立した予算を黙って確保しないこと）
    を固定する。
    """

    def test_run_hitl_lints_accepts_and_honors_an_already_expired_deadline(self):
        """既に過ぎた `deadline` を渡すと、新しい予算を確保し直さずに
        即座に'budget exceeded'として扱う（scriptを実行しない）。"""
        expired_deadline = time.monotonic() - 1
        failures, errors = run_hitl_lints(
            PLUGIN_ROOT,
            "## 確認\n\n" + HITL_MARKER,
            scripts=HITL_LINT_WARN_SCRIPTS,
            deadline=expired_deadline,
        )
        self.assertEqual(failures, [], "期限切れの予算では script を実行してはならない")
        self.assertTrue(
            any("budget exceeded" in e for e in errors),
            f"budget exceeded の記録が無い: {errors}",
        )

    def test_run_and_log_warn_lints_requires_an_explicit_deadline(self):
        """`_run_and_log_warn_lints` は `deadline` を keyword-only 必須引数として
        持つ（呼び出し元が明示的に共有予算を渡すことを強制する。省略して
        新しい独立の予算を黙って確保できてしまう退行を構造的に防ぐ）。"""
        signature = inspect.signature(_run_and_log_warn_lints)
        deadline_param = signature.parameters["deadline"]
        self.assertEqual(deadline_param.kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertEqual(
            deadline_param.default,
            inspect.Parameter.empty,
            "deadline に既定値があると、呼び出し元が省略した場合に独立した予算を"
            "黙って確保してしまう退行を検出できない",
        )

    def test_run_and_log_warn_lints_skips_script_when_shared_budget_already_spent(self):
        """block パスが予算を使い切った後（＝共有 deadline が既に過去）に
        warn パスを呼んでも、warn パス自身が新しい予算を確保して script を
        実行してしまわないことを確認する。"""
        with tempfile.TemporaryDirectory() as tmp:
            proj_root = Path(tmp)
            expired_deadline = time.monotonic() - 1
            _run_and_log_warn_lints(
                proj_root, PLUGIN_ROOT, "## 確認\n\n" + HITL_MARKER, deadline=expired_deadline
            )
            log_path = proj_root / ".gdd" / "hook-errors.log"
            self.assertTrue(log_path.exists())
            log_text = log_path.read_text(encoding="utf-8")
            self.assertIn("budget exceeded", log_text)
            # script が実際に実行されていれば "lint-hitl-required-fields:" に
            # 続けて lint 自身のエラーメッセージ（<gdd-hitl-fields> の指摘等）が
            # 記録されるはずだが、予算切れでスキップされた場合はそれが無い。
            self.assertNotIn("の宣言がありません", log_text)

    def test_enforce_hitl_lint_gate_passes_the_same_deadline_to_block_and_warn_paths(self):
        """PR #92 レビュー指摘（Medium）: 上の2テストは「期限切れ deadline を
        尊重する」「deadline が必須引数」までしか固定しておらず、
        `enforce_hitl_lint_gate` 自身が block パス（直接の `run_hitl_lints`
        呼び出し）と warn パス（`_run_and_log_warn_lints` 経由の
        `run_hitl_lints` 呼び出し）に**同じ** deadline 値を渡すことまでは
        固定していなかった。呼び出しを独立予算に戻す退行を注入しても、
        既存テストはすべて通ってしまう（実測済み）。ここでは
        `run_hitl_lints` をモックして、実際に渡された deadline 引数の値
        そのものを比較する。
        """
        import lib.hitl_lint_gate as hitl_lint_gate_module

        recorded_deadlines: list[float | None] = []

        def fake_run_hitl_lints(plugin_root, hitl_text, *, scripts=HITL_LINT_WARN_SCRIPTS, deadline=None):
            recorded_deadlines.append(deadline)
            return [], []

        with tempfile.TemporaryDirectory() as tmp:
            proj_root = Path(tmp)
            with unittest.mock.patch.object(
                hitl_lint_gate_module, "run_hitl_lints", side_effect=fake_run_hitl_lints
            ):
                hitl_lint_gate_module.enforce_hitl_lint_gate(
                    proj_root,
                    "human-check-waiting",
                    "## 確認\n\n" + HITL_MARKER,
                    plugin_root=PLUGIN_ROOT,
                )

        self.assertEqual(len(recorded_deadlines), 2, recorded_deadlines)
        self.assertIsNotNone(recorded_deadlines[0])
        self.assertEqual(
            recorded_deadlines[0],
            recorded_deadlines[1],
            "block パスと warn パスの deadline が異なる — 呼び出しごとに"
            "独立した予算を確保する退行が入っている",
        )



if __name__ == "__main__":
    unittest.main()

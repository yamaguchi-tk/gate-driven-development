"""E2E: HITL品質lint 3本の Stop hook 配線。

gdd_stop_hook.py をサブプロセスとして実行し、human-check-waitingの最終HITL本文が
配線済みlint（display-integrity / human-check-language / complexity）を通らないとき、
停止は止めずに、結果を systemMessage でユーザーに知らせ、.gdd/hitl-lint.log に記録する
ことを確認する（差し戻しの往復をやめた。経緯は`hitl_lint_gate.py`のモジュールdocstring）。

Run from plugins/gate-driven-development/:
  python3 -m unittest tests.test_stop_hook_hitl_lint_gate_e2e -v
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _stop_hook_test_base import (  # noqa: E402
    _make_transcript_jsonl,
    _run_hook,
    _write_state_file,
)

from lib.state_io import parse_state  # noqa: E402

from _paths import PLUGIN_ROOT
import test_stop_hook_e2e_block_content as _block_content
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "hitl-lint-gate"
GOLD_PASS_TEXT = (FIXTURE_DIR / "gold-pass.md").read_text(encoding="utf-8")
QUALITY_FAIL_TEXT = (FIXTURE_DIR / "quality-fail.md").read_text(encoding="utf-8")

_PLUGIN_ROOT_ENV = {"GDD_PLUGIN_ROOT": str(PLUGIN_ROOT)}


class HitlLintGateE2ETests(unittest.TestCase):
    _setup = _block_content.TestHookE2ENextActionBlock._setup

    def test_quality_passing_hitl_pauses_without_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript = self._setup(ws, GOLD_PASS_TEXT)
            code, out, _ = _run_hook(
                ws, transcript, session_id="test-session", env_overrides=_PLUGIN_ROOT_ENV,
            )
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)
            self.assertNotIn("systemMessage", out)
            self.assertTrue((ws / ".claude" / "gdd-dev.local.md").exists())

    def test_quality_failing_hitl_pauses_with_a_warning_instead_of_a_block(self):
        """不足のある HITL でも差し戻さずに止まり、不足は systemMessage と記録に残す。
        何度出しても同じで、差し戻しの予算のような状態は state に書かない。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript = self._setup(ws, QUALITY_FAIL_TEXT)
            for _ in range(3):
                code, out, _ = _run_hook(
                    ws, transcript, session_id="test-session", env_overrides=_PLUGIN_ROOT_ENV,
                )
                self.assertEqual(code, 0)
                payload = json.loads(out.strip())
                self.assertNotIn("decision", payload)
                self.assertIn("lint-hitl-display-integrity", payload["systemMessage"])
            state_frontmatter, _ = parse_state(ws / ".claude" / "gdd-dev.local.md")
            self.assertNotIn("hitl_lint_blocks", state_frontmatter)
            log = (ws / ".gdd" / "hitl-lint.log").read_text(encoding="utf-8")
            self.assertIn("lint-hitl-display-integrity", log)

    def test_skip_env_var_disables_gate_even_for_failing_hitl(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript = self._setup(ws, QUALITY_FAIL_TEXT)
            env = dict(_PLUGIN_ROOT_ENV)
            env["GDD_SKIP_HITL_LINT"] = "1"
            code, out, _ = _run_hook(
                ws, transcript, session_id="test-session", env_overrides=env,
            )
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)
            self.assertNotIn("systemMessage", out)

    def test_markerless_state_fallback_is_not_scored(self):
        """`Resume From: human-check-waiting` 経由のmarkerless fallbackは、
        last_outputが最終HITL面ではないため lint 対象にしない。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {
                "active": "true", "session_id": "test-session", "iteration": "1",
            })
            steering = ws / ".steering" / "20260101-example"
            steering.mkdir(parents=True)
            (steering / "state.md").write_text(
                "# State\n\n## Gate Status\n- Resume From: human-check-waiting\n",
                encoding="utf-8",
            )
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(
                transcript,
                assistant_text=(
                    "## 確認\n判断ポイント: 続きです。OKなら進めます。"
                    "\n\n## 👤 次にすること\nOKで承認してください"
                ),
            )
            code, out, _ = _run_hook(
                ws, transcript, session_id="test-session", env_overrides=_PLUGIN_ROOT_ENV,
            )
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)


if __name__ == "__main__":
    unittest.main()

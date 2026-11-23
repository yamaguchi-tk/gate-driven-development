"""gate 判定の区切り文字正規化と `Next Action` の所在に関する契約テスト。

背景:
`gdd_check_3field_gate` は `grep 'Requirements Review Status='` と **`=` 形式のみ**
を見ていた。一方、汎用の `gdd_extract_doc_field` は `:` と `=` の両方を受け付ける。
実データでは `:` 形式が多数派で、gate 判定を静かにすり抜け、
`GDD_TASKLIST_CANONICAL` が false のままだったため plan-reread hook はほとんど発火しなかった。

読み手だけが厳格な状態が最も悪いので、gate 判定を `gdd_extract_doc_field` と
同じ正規化に揃える。

副作用の緩和:
正規化すると新たに canonical になる task があり、`Next Action` が必須化されて
fail-closed する。`gdd_validate_active_state_fields` は `Next Action` を tasklist.md
からしか探していなかったが、実データでは state.md 側に持っているものが多い。
どちらからでも受け付けるようにすると大半が救済され、残りは
「どちらにも無い」= routing source 欠落なので fail-closed が正しい挙動。
"""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT as ROOT
LIB = ROOT / "hooks" / "scripts" / "lib" / "detect-steering.sh"

_APPROVED_FIELDS = ("Requirements Review Status", "Design Review Status", "Human Check Status")


def _write_state(d: Path, delimiter: str = "=", extra: str = "") -> None:
    d.mkdir(parents=True, exist_ok=True)
    lines = [f"{f}{delimiter}approved | evidence: x" for f in _APPROVED_FIELDS]
    lines += ["Resume From: gdd-subagent-driven-implementation",
              "Route In Progress: none",
              "Started At: 2026-07-28T00:00:00Z"]
    (d / "state.md").write_text("\n".join(lines) + "\n" + extra, encoding="utf-8")


def _write_tasklist(d: Path, next_action: str | None = None) -> None:
    body = "## Current Task\n### Task: T-1\n- AC-1: x\n"
    if next_action:
        body += f"\n## Review Status\nNext Action={next_action}\n"
    (d / "tasklist.md").write_text(body, encoding="utf-8")


def _bash(steering: Path, body: str) -> str:
    script = f'set -euo pipefail\nsource "{LIB}"\nGDD_STEERING_DIR="{steering}"\n{body}'
    r = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    return (r.stdout + r.stderr).strip()


def _canonical(steering: Path) -> str:
    return _bash(steering, 'gdd_check_3field_gate\necho "$GDD_TASKLIST_CANONICAL"')


def _validate(steering: Path) -> str:
    return _bash(
        steering,
        'gdd_check_3field_gate\n'
        'if gdd_validate_active_state_fields; then echo OK; '
        'else echo "NG:$GDD_ACTIVE_STATE_MISSING"; fi',
    )


class GateDelimiterNormalizationTests(unittest.TestCase):
    def test_colon_form_is_recognized(self, ) -> None:
        """`:` 形式でも canonical と判定される（この修正の本体）"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "s"
            _write_state(d, delimiter=": ")
            _write_tasklist(d, "gdd-implementation-gating")
            self.assertEqual(_canonical(d), "true", "`:` 形式が gate 判定で無視されている")

    def test_equals_form_still_recognized(self) -> None:
        """`=` 形式の従来挙動は不変（非退行）"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "s"
            _write_state(d, delimiter="=")
            _write_tasklist(d, "gdd-implementation-gating")
            self.assertEqual(_canonical(d), "true")

    def test_unapproved_stays_non_canonical(self) -> None:
        """未 approved は canonical にしない（gate を緩めない）"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "s"
            d.mkdir(parents=True)
            (d / "state.md").write_text(
                "Requirements Review Status: approved\n"
                "Design Review Status: in_review\n"
                "Human Check Status: approved\n", encoding="utf-8")
            _write_tasklist(d, "gdd-implementation-gating")
            self.assertEqual(_canonical(d), "false", "未 approved を通してはいけない")


class NextActionSourceTests(unittest.TestCase):
    def test_next_action_from_tasklist_is_accepted(self) -> None:
        """従来どおり tasklist.md 側の Next Action で通る"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "s"
            _write_state(d, delimiter="=")
            _write_tasklist(d, "gdd-implementation-gating")
            self.assertEqual(_validate(d), "OK")

    def test_next_action_from_state_md_is_accepted(self) -> None:
        """tasklist.md に無くても state.md 側にあれば通る（この修正の副作用の緩和）"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "s"
            _write_state(d, delimiter=": ", extra="Next Action: gdd-implementation-gating\n")
            _write_tasklist(d, None)
            self.assertEqual(
                _validate(d), "OK",
                "state.md 側の Next Action を routing source として認めるべき",
            )

    def test_missing_everywhere_still_fails_closed(self) -> None:
        """どちらにも無ければ fail-closed（routing source 欠落なので正しい）"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "s"
            _write_state(d, delimiter=": ")
            _write_tasklist(d, None)
            self.assertIn(
                "NG:", _validate(d),
                "Next Action がどこにも無い場合は止めるべき",
            )


if __name__ == "__main__":
    unittest.main()

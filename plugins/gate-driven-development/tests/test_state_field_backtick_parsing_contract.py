"""`state.md` のフィールド値がバッククォート囲みでも読めることを固定する契約テスト。

`gdd_task_binding.py` の `_field()` にあった silent failure（行全体から
バッククォートを strip したせいで値の先頭に ` が残る）と同型の欠陥が、
他の「書き手は複数の形で書くが読み手は 1 つの形しか認めない」箇所にも
無いことを固定する。

対象:
- `scripts/setup-gdd-loop.sh` に埋め込まれた `parse_field()`
- `scripts/collect-gdd-telemetry.py` の `extract_field()`

どちらも値がバッククォート付きのまま返ると、比較対象のリテラル
（`"done"` / `"approved"` / git branch 名）に一致せず、
エラーを出さないまま誤った分類をする。
"""

from __future__ import annotations

import importlib.util
import re
import sys
import unittest


from _paths import PLUGIN_ROOT as ROOT
LOOP_SCRIPT = ROOT / "scripts" / "setup-gdd-loop.sh"
TELEMETRY_SCRIPT = ROOT / "scripts" / "collect-gdd-telemetry.py"


def load_loop_parse_field():
    """`setup-gdd-loop.sh` の heredoc から parse_field 系の定義だけを取り出す。"""

    source = LOOP_SCRIPT.read_text(encoding="utf-8")
    blocks = []
    backtick = re.search(r"^BACKTICK = .*$", source, re.MULTILINE)
    assert backtick, f"BACKTICK definition not found in {LOOP_SCRIPT}"
    blocks.append(backtick.group(0))
    for name in ("normalize_line", "strip_fenced_blocks", "parse_field"):
        match = re.search(rf"^def {name}\(.*?(?=^def |\n^[a-zA-Z@#])", source, re.MULTILINE | re.DOTALL)
        assert match, f"{name} definition not found in {LOOP_SCRIPT}"
        blocks.append(match.group(0))
    namespace: dict = {}
    exec("\n".join(blocks), namespace)  # noqa: S102 - shipped source を直接検証するため
    return namespace["parse_field"]


def load_telemetry_module():
    spec = importlib.util.spec_from_file_location("collect_gdd_telemetry", TELEMETRY_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    # dataclass の annotation 解決が sys.modules 経由で行われるため先に登録する
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestSetupGddLoopParseField(unittest.TestCase):
    def setUp(self) -> None:
        self.parse_field = load_loop_parse_field()

    def test_backticked_value_drops_backticks(self) -> None:
        text = "- Active Branch: `gdd/20260616-sample`\n"
        self.assertEqual(self.parse_field(text, ["Active Branch"]), "gdd/20260616-sample")

    def test_backticked_terminal_state_is_recognized(self) -> None:
        text = "- Next Action: `done`\n"
        self.assertEqual(self.parse_field(text, ["Next Action"]), "done")

    def test_plain_value_is_unchanged(self) -> None:
        text = "- Task ID: 20260616-sample\n"
        self.assertEqual(self.parse_field(text, ["Task ID"]), "20260616-sample")

    def test_fully_backticked_line_still_parses(self) -> None:
        text = "- `Resume From: gdd-test-driven-development`\n"
        self.assertEqual(self.parse_field(text, ["Resume From"]), "gdd-test-driven-development")


class TestTelemetryExtractField(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_telemetry_module()

    def test_backticked_gate_status_is_counted_as_approved(self) -> None:
        text = "- Requirements Review Status: `approved` | evidence: fixture\n"
        self.assertEqual(self.mod.extract_field(text, "Requirements Review Status"), "approved")

    def test_backticked_next_action_matches_terminal_literal(self) -> None:
        text = "- Next Action: `done`\n"
        self.assertEqual(self.mod.extract_field(text, "Next Action"), "done")

    def test_plain_gate_status_is_unchanged(self) -> None:
        text = "- Design Review Status: approved | evidence: fixture\n"
        self.assertEqual(self.mod.extract_field(text, "Design Review Status"), "approved")


if __name__ == "__main__":
    unittest.main()

"""done guard（Stop hook）が LF / CR 以外の行区切り文字を含む tasklist を block する契約。

独立レビュー R23 #1（high / fail-open / pre-existing）: `str.splitlines()` は
`\\x0b \\x0c \\x1c \\x1d \\x1e \\x85 U+2028 U+2029` でも行を分ける。行の途中に
`U+2028## X` を置くと、guard はそこで `## Verification` 節が終わったと判断し、後ろの
`fail` 行が節の外になって done が通っていた。閉じた文法の改行は LF / CR / CRLF だけ
（`references/self-contained-contract.md` の `ws` 定義は U+2028 を ws にも改行にもしない）
なので、これらの文字を含む tasklist は解析の前提が崩れたものとして block する（fail-closed）。

- 8 種類のどれを含んでも block し、理由に `U+XXXX` の表記を出す（文字そのものは載せない）
- LF / CRLF の tasklist は従来どおり done を許可する
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks" / "scripts"))

from _stop_hook_test_base import _bind, _stop_done, _write_steering  # noqa: E402

_SLUG = "20260911-line-break-chars"
# `gdd_stop_hook._done_block_payload` が理由と推奨アクションの間に置く区切り
_HINTS_SEPARATOR = "--- 推奨アクション ---"
_LINE_BREAK_CHARS = ("\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029")


def _tasklist(verification_body: str, newline: str = "\n") -> str:
    text = (
        "# Tasklist\n\n"
        "## Current Task\n- なし\n\n"
        "## Pending Tasks\n- なし\n\n"
        "## Completed Tasks\n- T1 | AC-01 | done\n\n"
        "## Verification\n\n"
        "| method | status | evidence | notes |\n"
        "|---|---|---|---|\n"
        f"{verification_body}\n\n"
        "## Status\nNext Action=done\n"
    )
    return text.replace("\n", newline)


def _run(tasklist_text: str) -> tuple[int, str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp)
        _write_steering(ws, _SLUG, tasklist_text)
        _bind(ws, _SLUG)
        return _stop_done(ws)


class LineBreakCharsBlockTests(unittest.TestCase):
    def _reason(self, tasklist_text: str) -> str:
        code, out, err = _run(tasklist_text)
        self.assertNotEqual(out.strip(), "", f"allow になっている（行区切り文字で done が通る）: err={err}")
        payload = json.loads(out.strip())
        self.assertEqual(payload["decision"], "block", f"out={out}\nerr={err}")
        return payload["reason"]

    def test_hidden_section_break_with_each_char_blocks(self):
        # R23 #1 の再現形: pass 行の途中の区切り文字 + `## Hidden` で節を切り、後ろの fail 行を隠す
        for ch in _LINE_BREAK_CHARS:
            with self.subTest(char=f"U+{ord(ch):04X}"):
                body = f"| method=ac:AC-1 | pass | x | - |{ch}## Hidden\n| method=ac:AC-2 | fail | x | - |"
                reason = self._reason(_tasklist(body))
                self.assertIn("行区切り文字", reason)
                self.assertIn(f"U+{ord(ch):04X}", reason)
                self.assertNotIn(ch, reason)

    def test_char_in_an_otherwise_clean_tasklist_blocks(self):
        # 隠す構造が無くても、解析の前提（行 = LF / CR 区切り）が崩れている tasklist は通さない
        reason = self._reason(_tasklist("| method=ac:AC-1 | pass | pytest\u2028通過 | - |"))
        self.assertIn("行区切り文字", reason)
        self.assertIn("U+2028", reason)


class LineBreakReasonAndHintTests(unittest.TestCase):
    """impl-gate R21 M-1: 理由は文字のある原文行番号と「削除」を示し、LF への置き換えを勧めない。

    LF に置き換えると `U+2028## Hidden` が本物の見出しになり、後ろの fail 行が節の外に出て
    done が通る（R23 と同じ結果）。推奨アクションも行区切り文字の案内を出し、「唯一の回復手順」を
    出さない（区切り文字で割れた断片が schema 違反になっても、解除手順は文字の削除）。
    """

    def _reason(self, tasklist_text: str) -> str:
        return LineBreakCharsBlockTests._reason(self, tasklist_text)

    def test_reason_points_to_one_indexed_line_and_deletion(self):
        row = "| method=ac:AC-1 | pass | pytest\u2028通過 | - |"
        text = _tasklist(row)
        line_no = text.split("\n").index(row) + 1
        reason = self._reason(text)
        self.assertIn(f"行 [{line_no}]", reason)
        # 理由（error_msg）と推奨アクションを分けて見る。連結した reason に assertIn すると片方の
        # 退行が通る（impl-gate R23 M-1）
        cause, _, hints = reason.partition(_HINTS_SEPARATOR)
        self.assertTrue(hints, "推奨アクションの区切りが見つからない")
        self.assertIn("該当文字を削除してください", cause)
        self.assertIn("行区切り文字 →", hints)
        self.assertIn("削除してください", hints)
        # 案内は削除だけ。半角空白への置き換えは、行頭のタスク行を字下げにして Check 1 から
        # 見えなくし、未完了のまま done を通す（impl-gate R23 H-1 / 2026-09-11 ユーザー決定）
        self.assertNotIn("半角空白", cause)
        self.assertNotIn("半角空白", hints)
        self.assertNotIn("通常の改行（LF）に置き換えてください", reason)

    def test_recovery_hint_is_deletion_not_sole_rewrite(self):
        # セル内の区切り文字で表の行が 2 つの断片に割れ、両方が schema 違反になる形。抑止が無ければ
        # 「唯一の回復手順」が出る入力で、案内と抑止を固定する（impl-gate R22 M-1）
        reason = self._reason(_tasklist("| method=ac:AC-1 | pass | pytest\u2028通過 | - |"))
        self.assertIn("schema 違反行が", reason)
        self.assertIn("行区切り文字 →", reason)
        self.assertNotIn("唯一の回復手順", reason)

    def test_reason_lists_first_five_lines_and_the_rest_count(self):
        rows = [f"| method=ac:AC-{i} | pass | x\u2028y | - |" for i in range(1, 8)]
        text = _tasklist("\n".join(rows))
        lines = text.split("\n")
        line_numbers = [lines.index(row) + 1 for row in rows]
        reason = self._reason(text)
        self.assertIn(f"行 {line_numbers[:5]} ほか 2 行", reason)


class LineBreakCharsOutsideVerificationTests(unittest.TestCase):
    """impl-gate R21 M-2: 検出範囲は tasklist 全体。Check 1 の節（Pending / Completed）や
    `## Verification Notes` にある区切り文字も block する（2ffefff では Pending の形で done が通った）。
    """

    def _reason(self, tasklist_text: str) -> str:
        return LineBreakCharsBlockTests._reason(self, tasklist_text)

    def test_char_in_other_sections_blocks(self):
        base = _tasklist("| method=ac:AC-1 | pass | pytest 通過 | - |")
        variants = {
            "pending": base.replace(
                "## Pending Tasks\n- なし\n",
                "## Pending Tasks\n- なし\u2028## Completed Tasks\n- T2 | AC-02 | todo\n",
            ),
            "completed": base.replace("- T1 | AC-01 | done\n", "- T1 | AC-01 | done\u2028x\n"),
            "notes": base.replace("## Status\n", "## Verification Notes\n散文\u2028続き\n\n## Status\n"),
        }
        for name, text in variants.items():
            with self.subTest(section=name):
                self.assertNotEqual(text, base)
                self.assertIn("行区切り文字", self._reason(text))


class OrdinaryNewlinesStillAllowTests(unittest.TestCase):
    def test_lf_and_crlf_tasklists_allow_done(self):
        for name, newline in (("LF", "\n"), ("CRLF", "\r\n")):
            with self.subTest(newline=name):
                code, out, err = _run(_tasklist("| method=ac:AC-1 | pass | pytest 通過 | - |", newline))
                self.assertEqual(code, 0, f"err={err}")
                self.assertEqual(out.strip(), "", f"block されている: out={out}\nerr={err}")


if __name__ == "__main__":
    unittest.main()

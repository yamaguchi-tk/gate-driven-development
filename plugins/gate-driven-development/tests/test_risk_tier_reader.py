"""リスクの段の読み手（`hooks/scripts/lib/risk_tier.py`）が、`低` を 1 形だけで読み、ほかは全部 `高` に倒すこと。

記録の書式は `agents/gdd-request-code-crosscheck.md` § リスクの段（1 行目は固定行 `リスクの段: 高` か `リスクの段: 低`）。
読めない・崩れた記録を `低` と読むと、PR-4 で human check を待たずに進む根拠になるので、読めなければ `高` にする。
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from _plugin_module_loader import load_plugin_module

LIB = load_plugin_module("hooks/scripts/lib/risk_tier.py")

BEGIN = "<!-- gdd-request-capture:begin -->\n## ユーザーの発言\n\n> 依頼\n"
LOW = "## 突き合わせ\n\n### リスクの段\n\nリスクの段: 低\n- 根拠: 高の 4 つのどれにも当たらない\n"


class RiskTierReaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.steering = Path(self._tmp.name) / ".steering" / "task"
        self.steering.mkdir(parents=True)
        self.record = self.steering / "request-crosscheck.md"
        (self.steering / "request.md").write_text(BEGIN, encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _tier(self, text: str | bytes | None) -> str:
        if isinstance(text, bytes):
            self.record.write_bytes(text)
        elif text is not None:
            self.record.write_text(text, encoding="utf-8")
        return LIB.read_risk_tier(self.steering)

    def test_only_a_regular_request_md_starting_with_the_hook_section_is_the_original(self) -> None:
        # 依頼の原文は、hook が作った（通常のファイルで hook の節で始まる）request.md だけ。state.md の欄の有無では
        # 決めない（欄は runner が書き漏らせ、後から消せる）。それ以外は記録が低でも高にする。
        state = self.steering / "state.md"
        request = self.steering / "request.md"
        for state_text in (None, "- Started At: 2026-10-31T20:00:00+09:00\n",
                           "- Started At: 2026-10-31T20:00:00+09:00\n- `Created In Session`: s1\n"):
            if state_text is None:
                state.unlink(missing_ok=True)
            else:
                state.write_text(state_text, encoding="utf-8")
            for text in (None, "<!-- gdd-request-capture:not-copied -->\n## hook は依頼の原文を写していない\n",
                         "# 依頼の原文\n\nmain が書いた依頼の要約\n", "\n<!-- gdd-request-capture:begin -->\n",
                         "\ufeff<!-- gdd-request-capture:begin -->\n"):
                with self.subTest(state=state_text, request=text):
                    request.unlink(missing_ok=True)
                    if text is not None:
                        request.write_text(text, encoding="utf-8")
                    self.assertEqual(self._tier(LOW), "高")
            with self.subTest(state=state_text, request="hook の節"):
                request.write_text(BEGIN, encoding="utf-8")
                self.assertEqual(self._tier(LOW), "低")
        request.unlink()
        target = self.steering / "elsewhere.md"
        target.write_text(BEGIN, encoding="utf-8")
        request.symlink_to(target)
        self.assertEqual(self._tier(LOW), "高")

    def test_unreadable_request_reads_high_without_raising(self) -> None:
        request = self.steering / "request.md"
        request.write_bytes(b"\xff\xfe<!-- gdd-request-capture:begin -->\n")
        self.assertEqual(self._tier(LOW), "高")
        request.unlink()
        request.mkdir()
        self.assertEqual(self._tier(LOW), "高")
        request.rmdir()
        os.mkfifo(request)
        self.assertEqual(self._tier(LOW), "高")

    def test_reads_low_only_from_the_fixed_line_right_after_the_heading(self) -> None:
        self.assertEqual(self._tier(LOW), "低")
        self.assertEqual(self._tier("### リスクの段\nリスクの段: 低  \n"), "低")

    def test_everything_else_is_high(self) -> None:
        cases = {
            "記録が無い": None,
            "節が無い": "## 突き合わせ\n\nリスクの段: 低\n",
            "1 行目が高": LOW.replace("リスクの段: 低", "リスクの段: 高"),
            "値に注記": LOW.replace("リスクの段: 低", "リスクの段: 低（文書だけ）"),
            "全角コロン": LOW.replace("リスクの段: 低", "リスクの段：低"),
            "太字": LOW.replace("リスクの段: 低", "**リスクの段: 低**"),
            "箇条": LOW.replace("リスクの段: 低", "- リスクの段: 低"),
            "1 行目が根拠": "### リスクの段\n- 根拠: なし\nリスクの段: 低\n",
            "節が 2 つ": LOW + "\n```\n### リスクの段\nリスクの段: 低\n```\n",
            "見出しの深さ違い": LOW.replace("### リスクの段", "## リスクの段"),
            "見出しに注記": LOW.replace("### リスクの段", "### リスクの段（暫定）"),
            "節の後が空": "### リスクの段\n\n",
            "UTF-8 でない": "### リスクの段\nリスクの段: 低\n".encode("shift_jis"),
            "BOM 付き": "\ufeff### リスクの段\nリスクの段: 低\n".encode("utf-8"),
            "U+2028 で割った行": "### リスクの段\u2028リスクの段: 低\n",
            "字下げした 2 つ目の見出し": LOW + "\n  ### リスクの段\n",
            "## の 2 つ目の見出し": LOW + "\n## リスクの段 ##\n",
            "ほかに高の行": LOW + "\n後の段で上げた:\nリスクの段：高\n",
            "判定できない": LOW.replace("- 根拠", "判定できない: 根拠が読めない\n- 根拠"),
        }
        for name, text in cases.items():
            with self.subTest(name):
                if self.record.exists():
                    self.record.unlink()
                self.assertEqual(self._tier(text), "高")

    def test_unreadable_record_is_high_without_raising(self) -> None:
        self.record.mkdir()
        self.assertEqual(LIB.read_risk_tier(self.steering), "高")
        self.record.rmdir()
        missing = self.steering.parent / "missing"
        self.assertEqual(LIB.read_risk_tier(missing), "高")

    def test_fifo_and_dangling_symlink_are_high_without_blocking(self) -> None:
        os.mkfifo(self.record)
        self.assertEqual(LIB.read_risk_tier(self.steering), "高")
        self.record.unlink()
        self.record.symlink_to(self.steering / "nowhere.md")
        self.assertEqual(LIB.read_risk_tier(self.steering), "高")

    @unittest.skipIf(os.geteuid() == 0, "root は読み取りの権限を無視する")
    def test_permission_denied_is_high_without_raising(self) -> None:
        self.record.write_text(LOW, encoding="utf-8")
        self.record.chmod(0)
        try:
            self.assertEqual(LIB.read_risk_tier(self.steering), "高")
        finally:
            self.record.chmod(0o644)


if __name__ == "__main__":
    unittest.main()

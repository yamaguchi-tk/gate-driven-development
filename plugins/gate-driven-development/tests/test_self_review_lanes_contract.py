"""Deterministic doc test for references/self-review-lanes.md.

各 assertion は「見出しの存在」ではなく **対象節に閉じた構造（表の行・列・値）** を読む。
期待値は可能な限りドキュメント内の独立した別箇所から機械導出し（3 レーン定義 ↔ 発火表、
分類表の `（3f X 型と対応）` 注記 ↔ A〜E 対応表）、literal の重複を空洞化防止アンカーに限る。
"""
from __future__ import annotations

import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
LANES_DOC = PLUGIN_ROOT / "references" / "self-review-lanes.md"


MERGE_GATE_HEADING = "## merge gate 証跡（`gh pr merge` の解除条件。正本）"

DETECT_STEERING_LIB = PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "detect-steering.sh"
MERGE_GATE_LIB = PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "merge-gate-evidence.sh"


def _run_shell(script: str) -> str:
    # `assert` は `python -O` で無効化され失敗を素通りさせるため、明示的に例外を送出する
    proc = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    if proc.returncode != 0:
        raise AssertionError(
            f"shell の実行に失敗した (returncode={proc.returncode}): {proc.stderr}"
        )
    return proc.stdout


class MergeGateEvidenceExampleContractTests(unittest.TestCase):
    """gate #13 F-B2 回帰: 記入例が `gdd_extract_doc_field` の実挙動に照らして承認証跡として成立しない。

    旧文面は「インデント bullet / bare 行は `gdd_extract_doc_field` が拾わない」と
    書いていたが、実挙動では **拾わないのはインデント行だけ**で bare 行は bullet と
    同じく拾われる。同節の記入例は bare 行で書かれていたため、散文と例が矛盾したうえ、
    「bare なら不活性」という誤った安心のもとに `Merge Approval` の下書きを state.md へ
    置くと gate に承認証跡として読まれる。本テストは (1) パーサの実挙動、
    (2) 記入例が canonical bullet 形であり、かつ verbatim では承認証跡として
    成立しないこと、の 2 点を実測で固定する。
    """

    def setUp(self) -> None:
        self.lines = LANES_DOC.read_text(encoding="utf-8").splitlines()
        start = self.lines.index(MERGE_GATE_HEADING) + 1
        end = start
        while end < len(self.lines) and not self.lines[end].startswith("#"):
            end += 1
        self.section = self.lines[start:end]
        fences = [i for i, line in enumerate(self.section) if line.strip() == "```"]
        self.assertEqual(len(fences), 2, "merge gate 証跡節のコードブロックはちょうど 1 つ")
        self.example_lines = self.section[fences[0] + 1:fences[1]]

    # (1) パーサの実挙動（doc が記述すべき事実そのもの）
    def test_extract_doc_field_actual_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.md"
            state.write_text(
                "## Gate Status\n"
                "Merge Approval: bare-value\n"
                "- Bot Review Received: bullet-value\n"
                "  - Independent Review: indented-value\n",
                encoding="utf-8",
            )
            out = _run_shell(
                f'source "{DETECT_STEERING_LIB}"; '
                f'for f in "Merge Approval" "Bot Review Received" "Independent Review"; do '
                f'printf "[%s]\\n" "$(gdd_extract_doc_field "{state}" "$f")"; done'
            ).splitlines()
        # bare も bullet も拾われる。拾われないのはインデント行だけ。
        self.assertEqual(out, ["[bare-value]", "[bullet-value]", "[]"])

    # (2) 記入例が canonical bullet 形で、かつ verbatim では証跡として成立しない
    def test_example_lines_are_canonical_bullets_and_never_valid_evidence(self) -> None:
        self.assertEqual(len(self.example_lines), 7)
        fields = []
        for line in self.example_lines:
            matched = re.match(r"^- ([A-Za-z][A-Za-z -]+?): ", line)
            self.assertIsNotNone(matched, f"記入例は canonical bullet 形であること: {line!r}")
            fields.append(matched.group(1))
        self.assertIn("Merge Approval", fields)
        self.assertIn("Medium Disposition", fields)

        # 記入例を verbatim で state.md に貼っても、placeholder のまま gate を通らない。
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.md"
            state.write_text(
                "## Gate Status\n" + "\n".join(self.example_lines) + "\n", encoding="utf-8"
            )
            checks = "; ".join(
                f'gdd_parse_merge_gate_field "{state}" "{f}" ""; printf "%s\\n" "$GDD_MG_VALID"'
                for f in fields
            )
            out = _run_shell(f'source "{MERGE_GATE_LIB}"; {checks}').split()
        self.assertEqual(out, ["false"] * len(fields), "記入例が承認証跡として valid になっている")


if __name__ == "__main__":
    unittest.main()

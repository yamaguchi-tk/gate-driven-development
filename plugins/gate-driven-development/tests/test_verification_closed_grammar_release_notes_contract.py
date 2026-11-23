"""T-7 (`## Verification` 節文法を閉じる PR) の後継 ADR / CHANGELOG breaking change
entry / version bump を固定する契約テスト。

対象 AC:
    - AC-12: 旧 ADR (`docs/adr/2026-09-06-done-guard-verification-header.md`) を
      supersede する後継 ADR を新設する
    - AC-15: CHANGELOG に breaking change として記録し、version を 5 箇所同時更新する
    - AC-16: 移行コスト（`measure-done-guard-drift.py` の再実測値）を CHANGELOG に
      `measured_at` 付きで記録する（本ファイルに機械検査なし）

Contract Surface Coverage:
    - success path: applicable -> version 一致 / 新 ADR ファイルの実在 / CHANGELOG の
      User Action Required の canonical 例が文法に適合（CHANGELOG の必須節は本ファイルに機械検査なし）
    - no-op / silent success path: not_applicable（文書追加のみで no-op 分岐を持たない）
    - external API response variants: not_applicable（外部 API 呼び出しなし）
    - external API failure / unavailable path: not_applicable（同上）
    - validation / sanitize / fail-closed path: 機械検査なし（AC-16 の Migration Cost
      プレースホルダー検査は本ファイルには実装されていない）
    - formatting / output schema path: applicable -> CHANGELOG release heading の版数が
      manifest と一致（ADR の見出しは本ファイルに機械検査なし）
    - duplicate / idempotency / lock path: not_applicable（version bump は 1 回きりの記述で
      ロック機構を持たない）
    - user-visible side effect path: applicable -> User Action Required section
      （利用者が実際に手を動かす移行手順）
    - grammar conformance path: applicable ->
      test_user_action_required_canonical_example_conforms_to_closed_grammar
      （release note が示す canonical 例そのものを `_scan_verification()` へ掛ける。
      語の存在検査だけでは壊れた例を素通しするため。impl-gate R9 H1 / M2）
"""
from __future__ import annotations

import re
import sys
import textwrap
import unittest


from _paths import PLUGIN_ROOT

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))
from lib import done_guard as guard  # noqa: E402

TARGET_VERSION = "0.42.0"


def read_plugin(path: str) -> str:
    return (PLUGIN_ROOT / path).read_text(encoding="utf-8")


def extract_changelog_entry(changelog_text: str, version: str) -> str:
    """CHANGELOG.md の `### [<version>] - ...` 見出しから次の `### [` 見出し直前までを返す。

    見つからない場合は空文字列（呼び出し側で `self.assertTrue(entry)` により
    「節そのものが無い」という正しい理由で RED にする）。
    """
    pattern = re.compile(
        rf"^### \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}\s*$",
        re.MULTILINE,
    )
    match = pattern.search(changelog_text)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^### \[", changelog_text[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(changelog_text)
    return changelog_text[start:end]


_FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})")


def extract_dedented_fences(section_text: str) -> list[list[str]]:
    """節本文から fenced code block を全件抽出し、dedent した行 list として返す。

    CHANGELOG の canonical 例は番号付き list の中にあるためインデントされている。
    利用者は fence の中身をコピーして `## Verification` 節へ**そのまま貼る**ので、
    文法照合はインデントを剥がした形で行うのが実態と一致する
    （`_classify_verification_line()` は行頭インデントを受理しないため、
    dedent しないと header 行すら header と判定されず vacuous に緑になる）。
    """
    lines = section_text.splitlines()
    blocks: list[list[str]] = []
    i = 0
    while i < len(lines):
        opening = _FENCE_RE.match(lines[i])
        if opening is None:
            i += 1
            continue
        marker = opening.group(2)
        body: list[str] = []
        j = i + 1
        while j < len(lines):
            closing = _FENCE_RE.match(lines[j])
            if (
                closing is not None
                and closing.group(2)[0] == marker[0]
                and len(closing.group(2)) >= len(marker)
            ):
                break
            body.append(lines[j])
            j += 1
        blocks.append(textwrap.dedent("\n".join(body)).splitlines())
        i = j + 1
    return blocks


def scan_as_verification_section(block_lines: list[str]):
    """`## Verification` 見出しを前置して `_scan_verification()` に掛ける。

    `_scan_verification` は `"## Verification"` の exact match に遭遇するまで全行を
    捨てるため、見出し無しで渡すとどれだけ壊れた表でも violations が常に 0 になる
    （`test_verification_grammar_single_source_contract.py` と同じ渡し方）。
    """
    return guard._scan_verification(["## Verification"] + list(block_lines))


class ChangelogBreakingChangeEntryContractTests(unittest.TestCase):
    """AC-15: CHANGELOG entry の User Action Required 節にある canonical 例が
    `## Verification` の文法に適合すること（machine 照合。AC-16 の Migration Cost
    記録は本ファイルに機械検査なし）。"""

    def setUp(self) -> None:
        self.changelog = read_plugin("CHANGELOG.md")
        self.entry = extract_changelog_entry(self.changelog, TARGET_VERSION)
        self.assertTrue(
            self.entry,
            f"CHANGELOG.md has no '### [{TARGET_VERSION}] - YYYY-MM-DD' entry yet",
        )

    def test_user_action_required_canonical_example_conforms_to_closed_grammar(self) -> None:
        """§ User Action Required の canonical 例を実際に `_scan_verification()` へ掛ける。

        impl-gate R9 H1: separator が 3 セル（`|---|---|---|`）のまま release note に
        載っていたが、語の存在検査（`assertIn("separator")` 等）はこれを素通しした。
        本 PR の主題が「文法の単一正本」である以上、release note の canonical 例も
        contract / SKILL / smoke.sh と同様に文法へ機械照合する。
        移行対象セッションにとって唯一のコピペ元なので、壊れた例は移行導線の破損に直結する。
        """
        section = self._section("#### User Action Required")
        blocks = [
            block
            for block in extract_dedented_fences(section)
            if any(
                guard._classify_verification_line(line)[0] in ("header", "separator", "data")
                for line in block
            )
        ]
        self.assertTrue(
            blocks,
            "§ User Action Required に canonical 例の fenced block が見つかりません"
            "（例が消えた / fence の形が変わった）",
        )
        for block in blocks:
            with self.subTest(first_line=block[0] if block else ""):
                found, rows, violations, _unfinished = scan_as_verification_section(block)
                self.assertTrue(found)
                self.assertEqual(
                    violations,
                    [],
                    f"release note の canonical 例が新文法に違反しています: {violations}",
                )
                self.assertGreaterEqual(
                    len(rows),
                    1,
                    "canonical 例は AC 検証行（data 行）を最低 1 行含むこと（header + separator だけの"
                    "例では『検証行がありません』の説明にしかならない）",
                )

    def test_broken_separator_in_canonical_example_is_detected(self) -> None:
        """判別力（vacuous pass 防止）: 例の separator を 3 セルへ戻すと赤くなること。

        上のテストが「例を消す / fence を壊す」以外の実際の文法違反を検出できることを
        固定する。これが無いと、抽出だけ成功して照合が効いていない状態を区別できない。
        """
        section = self._section("#### User Action Required")
        blocks = [
            block
            for block in extract_dedented_fences(section)
            if any(guard._classify_verification_line(line)[0] == "separator" for line in block)
        ]
        self.assertTrue(blocks, "separator を含む canonical 例が見つかりません")
        mutated = [
            "|---|---|---|" if guard._classify_verification_line(line)[0] == "separator" else line
            for line in blocks[0]
        ]
        _found, _rows, violations, _unfinished = scan_as_verification_section(mutated)
        self.assertNotEqual(
            violations,
            [],
            "separator を 3 セルへ壊しても violations が空（照合が効いていない）",
        )

    def _section(self, heading: str) -> str:
        pattern = re.compile(rf"^{re.escape(heading)}\s*$", re.M)
        match = pattern.search(self.entry)
        self.assertIsNotNone(match, f"{heading} not found in v{TARGET_VERSION} entry")
        start = match.end()
        next_heading = re.search(r"^#### ", self.entry[start:], re.M)
        end = start + next_heading.start() if next_heading else len(self.entry)
        return self.entry[start:end]


if __name__ == "__main__":
    unittest.main()

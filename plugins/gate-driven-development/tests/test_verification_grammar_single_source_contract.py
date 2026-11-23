"""`## Verification` 節の受理文法 BNF ブロックが contract / SKILL で単一正本であることの契約テスト
(AC-1 / AC-2 / AC-3, T-1)。T-5 で design.md § 6「旧文法署名の grep 0 件」と
vacuous pass 防止 (b-3) へ拡張した（(b-1)(b-2) の肯定形 test は語の存在検査のみだったため撤去済み）。
T-6 で S-7 / S-8（`scripts/external-verifier-smoke.sh`
対象）と「smoke 初期節の全量検査」を追加した（design.md § 6 / AC-13）。署名で残るのは
S-7 / S-8 だけで、`.md` 文書の語だけを見る S-1〜S-6 は撤去済み。

実行: `python3 -m pytest plugins/gate-driven-development/tests/test_verification_grammar_single_source_contract.py -v`

`<!-- verification-grammar:begin -->` / `:end` の HTML marker で挟んだ同一テキストの
BNF ブロックを `references/self-contained-contract.md` と `skills/gdd-ac-verification/SKILL.md`
の双方に置き、抽出比較で一致を pin する。「同一 canonical 例の存在」だけでは文法本文の
食い違いを止められないため、marker 抽出による文字列比較に確定する（AC-3）。

**T-6 owner（S-7 / S-8）**: `scripts/external-verifier-smoke.sh` は T-6 で canonical 化され
（`- 許容 status: ...` / `- 各行の形式: ROW-ID | method | status | evidence | notes` の
凡例 2 行を撤去）、S-7 / S-8 と「smoke 初期節の全量検査」は GREEN。
"""
from __future__ import annotations
import re, unittest
import sys

from _paths import PLUGIN_ROOT
CONTRACT = PLUGIN_ROOT / "references" / "self-contained-contract.md"
SKILL = PLUGIN_ROOT / "skills" / "gdd-ac-verification" / "SKILL.md"
SMOKE = PLUGIN_ROOT / "scripts" / "external-verifier-smoke.sh"
_BEGIN, _END = "<!-- verification-grammar:begin -->", "<!-- verification-grammar:end -->"
_BLOCK_RE = re.compile(re.escape(_BEGIN) + r"(.*?)" + re.escape(_END), re.DOTALL)

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))
from lib import done_guard as guard  # noqa: E402


def _extract(text: str) -> list[str]:
    return _BLOCK_RE.findall(text)


class VerificationGrammarSingleSourceContractTests(unittest.TestCase):
    def test_marker_exists_exactly_once_in_contract(self):
        self.assertEqual(len(_extract(CONTRACT.read_text(encoding="utf-8"))), 1)

    def test_marker_exists_exactly_once_in_skill(self):
        self.assertEqual(len(_extract(SKILL.read_text(encoding="utf-8"))), 1)

    def test_grammar_block_is_identical_text(self):
        c = _extract(CONTRACT.read_text(encoding="utf-8"))
        s = _extract(SKILL.read_text(encoding="utf-8"))
        self.assertEqual(c[0], s[0], "AC-3: contract と SKILL の文法ブロックは完全一致")


# ===========================================================================
# design.md § 6「旧文法署名の grep 0 件」: S-7 / S-8（scripts/external-verifier-smoke.sh
# 対象、コードが読む値を検査する）。旧 S-1〜S-6（.md 文書の語だけを見る署名）は、
# 文書の語・文だけを assert するテストを残さない方針（root CLAUDE.md § テスト）に
# 沿って撤去した。
# ===========================================================================


# ===========================================================================
# vacuous pass 防止 (b-3): 削除逃げの禁止。否定形（署名 0 件）だけでは「例ごと
# 削除する」で全緑になるため、canonical 例表そのものの文法妥当性を検査する
# （design.md § 6 (b-3)）。
# ===========================================================================


def _extract_canonical_blocks(text: str) -> list[list[str]]:
    """design.md § 6 (b-3): 「header 行に始まり separator + data 行で終わる塊」を全件抽出する。

    抽出単位は fence body ではなく、`_classify_verification_line()` が
    `header` と判定する行から始め、直後が `separator` であることを確認し、
    そこから連続する `data` 行だけを塊として拾う。行番号のハードコードは
    使わない（AC-2 / 書き直しで行がずれても壊れないようにする）。
    """
    lines = text.splitlines()
    blocks: list[list[str]] = []
    i = 0
    n = len(lines)
    while i < n:
        kind, _ = guard._classify_verification_line(lines[i])
        if kind == "header" and i + 1 < n:
            kind2, _ = guard._classify_verification_line(lines[i + 1])
            if kind2 == "separator":
                j = i + 2
                while j < n:
                    kind3, _ = guard._classify_verification_line(lines[j])
                    if kind3 != "data":
                        break
                    j += 1
                blocks.append(lines[i:j])
                i = j
                continue
        i += 1
    return blocks


class LegacyVerificationExampleGrammarValidityTests(unittest.TestCase):
    """(b-3): contract / SKILL の canonical 例表が文法として妥当であることを検査する。

    署名 grep（否定）だけでは「文法として妥当か」を見ない。ここが vacuous だと
    AC-1 の「contract 内の既存例が新文法に適合する」が無検査になる
    （design.md § 6 (b-3) / security R6 advisory 3-4 → planning R7 B-1）。
    """

    def _run(self, block_lines: list[str]):
        # `_scan_verification` は "## Verification" の exact match に遭遇するまで
        # 全行を捨てるため、見出し無しで渡すとどれだけ壊れた表でも violations は
        # 常に 0 になる（design.md § 6 (b-3)「入力の作り方」）。
        text = "## Verification\n" + "\n".join(block_lines)
        return guard._scan_verification(text.splitlines())

    def test_contract_canonical_blocks_are_valid_and_expected_count(self):
        text = CONTRACT.read_text(encoding="utf-8")
        blocks = _extract_canonical_blocks(text)
        # contract は 3 ブロック: AC 例 = 3 行 / external security evidence 例 = 3 行 /
        # refactor checkpoint 例 = 1 行（design.md § 6 (b-3)）
        self.assertEqual(len(blocks), 3, "contract の canonical 例ブロック数が変わった")
        expected_row_counts = [3, 3, 1]
        for block, expected_rows in zip(blocks, expected_row_counts):
            found, _rows, violations, _unfinished = self._run(block)
            self.assertTrue(found)
            self.assertEqual(violations, [], f"block={block[0]!r} violations={violations}")
            # T-9: `verification_data_rows` は AC 行だけを数えるようになったので（AC-9 第 5 形）、
            # 例表の行数は分類器から直接数える。`violations == []` へ弱めると行数の空虚化を
            # 検出できなくなる（このクラスの存在理由 = (b-3) の vacuous 化防止）
            data_lines = [ln for ln in block if guard._classify_verification_line(ln)[0] == "data"]
            self.assertEqual(len(data_lines), expected_rows, f"block={block[0]!r}")

    def test_skill_canonical_block_is_valid_and_expected_count(self):
        text = SKILL.read_text(encoding="utf-8")
        blocks = _extract_canonical_blocks(text)
        # SKILL 例表 = 8 行（AC 5 + security evidence 2 + refactor-checkpoint 1）
        self.assertEqual(len(blocks), 1, "SKILL の canonical 例ブロック数が変わった")
        found, _rows, violations, _unfinished = self._run(blocks[0])
        self.assertTrue(found)
        self.assertEqual(violations, [])
        # T-9: `verification_data_rows` は AC 行だけを数えるようになったので（AC-9 第 5 形）、
        # 例表の行数は分類器から直接数える。`violations == []` へ弱めると行数の空虚化を
        # 検出できなくなる（このクラスの存在理由 = (b-3) の vacuous 化防止）
        data_lines = [ln for ln in blocks[0] if guard._classify_verification_line(ln)[0] == "data"]
        self.assertEqual(len(data_lines), 8)

    def test_breaking_a_row_into_five_cells_is_detected(self):
        """判別力: 例表の 1 行を 5 セルに壊すと (b-3) が赤くなることを確認する。"""
        text = CONTRACT.read_text(encoding="utf-8")
        blocks = _extract_canonical_blocks(text)
        block = blocks[0]
        mutated = list(block)
        # 3 番目の行（先頭 data 行）に余分なセルを 1 つ挟んで 5 セルにする
        mutated[2] = mutated[2].replace(" | ", " | x | ", 1)
        found, rows, violations, _unfinished = self._run(mutated)
        self.assertNotEqual(violations, [], "5 セルへの破壊が検出されない")

    def test_dropping_the_verification_heading_is_detected(self):
        """判別力: `## Verification` 見出しを落とすと (b-3) が赤くなることを確認する。

        `_scan_verification` は `line.rstrip() == "## Verification"` に遭遇するまで
        全行を捨てる（design.md § 6 (b-3)「入力の作り方」）。本テストクラスの
        `_run()` はこの見出しを常に prepend しているが、それを忘れると
        どれだけ壊れた表でも `violations == []` かつ
        `verification_section_found is False` のまま黙って緑になる
        （否定形 assert だけでは検出できない）。この mutation で
        `verification_section_found` が意図どおり False に落ちる ―— つまり
        `_run()` の見出し prepend が実際に判定へ効いていること —— を固定し、
        本クラスの assert が vacuous でないことを示す。
        """
        text = CONTRACT.read_text(encoding="utf-8")
        blocks = _extract_canonical_blocks(text)
        block = blocks[0]
        # `_run()` を経由せず、見出しを付けずに直接 `_scan_verification` へ渡す
        found, rows, violations, _unfinished = guard._scan_verification(list(block))
        self.assertFalse(found, "見出し無しでも verification_section_found が True のまま")
        self.assertEqual(rows, [])
        self.assertEqual(violations, [])


# ===========================================================================
# smoke 初期節の全量検査（★ security R5 M-3, T-6 owner, design.md § 6）。
# S-7 / S-8 は凡例 2 行を名指しで潰すが、それだけでは初期節の他の行の
# 取りこぼしを検出できない。heredoc が書く初期節そのものを `_scan_verification`
# に掛けて violations 0 件であることを assert する。
# ===========================================================================

_SMOKE_HEREDOC_RE = re.compile(
    r"cat > \"[^\"]*tasklist\.md\" <<'EOF'\n(.*?)\nEOF\n", re.DOTALL
)


def _extract_smoke_initial_tasklist_lines(text: str) -> list[str]:
    """`external-verifier-smoke.sh` の heredoc（初期 tasklist.md 全文）を抽出する。

    heredoc は `## Verification` 見出しを含めて書くので、そのまま
    `_scan_verification` に渡せる（design.md § 6 (b-3)「同じ渡し方を smoke
    初期節の全量検査にも適用する」）。
    """
    match = _SMOKE_HEREDOC_RE.search(text)
    if match is None:
        raise AssertionError(
            "external-verifier-smoke.sh の heredoc tasklist.md が見つかりません"
            "（`cat > \"...tasklist.md\" <<'EOF'` の形が変わった可能性）"
        )
    return match.group(1).splitlines()


class SmokeInitialSectionFullScanTests(unittest.TestCase):
    """design.md § 6「smoke 初期節の全量検査」: heredoc の初期節を丸ごと検査する。"""

    def test_smoke_initial_verification_section_has_zero_violations(self):
        text = SMOKE.read_text(encoding="utf-8")
        lines = _extract_smoke_initial_tasklist_lines(text)
        found, _rows, violations, _unfinished = guard._scan_verification(lines)
        self.assertTrue(found, "heredoc に `## Verification` 見出しが見つからない")
        self.assertEqual(
            violations, [], f"smoke 初期節に文法違反が残っています: {violations}"
        )

    def test_smoke_heredoc_extraction_actually_finds_the_verification_section(self):
        """判別力: 抽出 helper 自体が壊れて空 list を返した場合に緑にならないこと。

        `_extract_smoke_initial_tasklist_lines` が heredoc を見つけられなくなると
        `_scan_verification([])` は `found=False, violations=[]` を返し、上のテストは
        誤って緑になる（vacuous pass）。見出しが実際に含まれることを別途固定する。
        """
        text = SMOKE.read_text(encoding="utf-8")
        lines = _extract_smoke_initial_tasklist_lines(text)
        self.assertIn("## Verification", [line.rstrip() for line in lines])

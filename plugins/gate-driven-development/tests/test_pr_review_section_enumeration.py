"""`gdd-pr-review` の「実行対象の列挙」と実在する追加チェック節の一致を機械照合する。

`tests/checks/pr-review-anticipation-tokens.sh` は列挙行を **literal で pin** するが、
literal の pin は「列挙が消えていない / 旧版に戻っていない」ことしか言えない。
節を 1 本足して列挙を更新し忘れる（あるいはその逆）と、pin は新 literal に合わせて
直せてしまい**不一致のまま通る**。分類 A（数値・列挙の自己不整合）そのものなので、
「列挙 == 実在節」は数え直しで固定する。
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills" / "gdd-pr-review" / "SKILL.md"

#: 手順 step 2 が「以下の追加チェック（...）を実施する」と列挙する括弧。
ENUMERATION_RE = re.compile(r"追加チェック（([^）]+)）")
#: 追加チェックの節見出し。`### 3d-2.` のような枝番も拾う。
SECTION_RE = re.compile(r"^### ([0-9]+[a-z]?(?:-[0-9]+)?)\.", re.M)


class PrReviewSectionEnumerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = SKILL.read_text(encoding="utf-8")

    def test_enumeration_matches_existing_sections_in_order(self) -> None:
        match = ENUMERATION_RE.search(self.text)
        self.assertIsNotNone(
            match, "手順 step 2 の「追加チェック（...）」列挙が見つからない"
        )
        declared = [item.strip() for item in match.group(1).split(",")]
        actual = SECTION_RE.findall(self.text)

        # 空洞化アンカー: どちらかが空なら照合が常に成立してしまう。
        self.assertTrue(declared, "列挙が空")
        self.assertTrue(actual, "追加チェックの節が 1 本も無い")

        self.assertEqual(
            declared,
            actual,
            "列挙と実在節が一致しない（順序を含む）。"
            f"宣言のみ={[x for x in declared if x not in actual]} / "
            f"実在のみ={[x for x in actual if x not in declared]}",
        )

    def test_enumerated_ids_are_unique(self) -> None:
        match = ENUMERATION_RE.search(self.text)
        assert match is not None
        declared = [item.strip() for item in match.group(1).split(",")]
        self.assertEqual(
            len(declared), len(set(declared)), f"列挙に重複がある: {declared}"
        )


if __name__ == "__main__":
    unittest.main()

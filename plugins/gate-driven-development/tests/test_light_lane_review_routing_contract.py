"""軽いレーンの独立レビューの振り分け（root CLAUDE.md 手順 6）の語彙が、3 か所でずれない契約テスト。

- 巡の件数に入れない `対応` の値（再掲 `re-reported`、② `next-pr`、③ `out-of-diff`）：CLAUDE.md が書かせる 3 値と、
  `review-log-present.sh` が件数から外す集合がちょうど一致する（検査側にだけ値を足せない）。受理集合にも入り、
  `review-log/README.md` も 6 値を書いている（件数から外すことは test_review_log_present.py が振る舞いで固定する）

片方だけ改名すると、再掲の行が検査で落ちる（または数えられる）。

- 差分巡の reviewer と全差分巡の reviewer の定義：本文が同じで、frontmatter は name・description・model・effort の
  ほかが同じ（全差分巡は opus・xhigh、差分巡は fable・high）
"""
from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT, REPO_ROOT
AGENT = REPO_ROOT / ".claude" / "agents" / "light-lane-independent-reviewer.md"
# canonical repo の目印は review-log の README にする。検査対象の agent 定義の有無を目印にすると、
# 定義を改名・削除したときに落ちずに skip になる
IN_CANONICAL_REPO = (REPO_ROOT / "plugins" / "gate-driven-development").resolve() == PLUGIN_ROOT.resolve() and (
    REPO_ROOT / "review-log" / "README.md"
).is_file()
UNCOUNTED = ("re-reported", "next-pr", "out-of-diff")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class RoutingVocabularyTests(unittest.TestCase):
    def setUp(self) -> None:
        if not IN_CANONICAL_REPO:
            self.skipTest("canonical repo 外では root の CLAUDE.md と agent 定義を検査しない")
        self.assertTrue(AGENT.is_file(), AGENT)
        self.claude = _read(REPO_ROOT / "CLAUDE.md")
        self.agent = _read(AGENT)
        self.check = _read(PLUGIN_ROOT / "tests" / "checks" / "review-log-present.sh")

    def test_uncounted_values_are_shared_by_claude_md_and_check(self) -> None:
        # 件数から外す値の集合は、CLAUDE.md が書かせる 3 つと一致させる。含まれるだけでは、
        # 検査側にだけ値が足されたときに、CLAUDE.md に無い値で high を件数から外せてしまう。
        # 右辺は行末まで集合リテラル 1 個だけに固定する（`| {"skip"}`・`.union(…)` で足す形を通さない）
        uncounted = re.search(r"^\s*UNCOUNTED_TAIOU_VALUES = \{([^}]*)\}[ \t]*(#.*)?$", self.check, re.M)
        self.assertIsNotNone(uncounted)
        # `|=` や再代入で、後から値を足せない
        self.assertEqual(len(re.findall(r"^\s*UNCOUNTED_TAIOU_VALUES\b", self.check, re.M)), 1)
        # 引用符の種類や `*名前` の展開で、集合の中身を数え損ねない（評価できない書き方は例外で落ちる）
        self.assertEqual(ast.literal_eval("{" + uncounted.group(1) + "}"), set(UNCOUNTED))
        for value in UNCOUNTED:
            self.assertIn(f"`{value}`", self.claude, value)
        # 件数から外す値は `対応` の受理集合にも入る。外れると手順どおりの行が値域で落ちる。
        # 右辺も全体を固定し、代入は 1 か所だけにする（受理側にだけ値を足す・union を外す・後から足す変更を通さない）
        accepted = re.search(r"^\s*TAIOU_VALUES = (.*?)[ \t]*(#.*)?$", self.check, re.M)
        self.assertIsNotNone(accepted)
        self.assertEqual(len(re.findall(r"^\s*TAIOU_VALUES\b", self.check, re.M)), 1)
        self.assertEqual(accepted.group(1), '{"fixed", "deferred", "accepted"} | UNCOUNTED_TAIOU_VALUES')

    def test_candidate_field_points_to_the_existing_script(self) -> None:
        # テンプレートの欄と CLAUDE.md が指すスクリプトが実在しないと、main は欄を埋められない
        script = "scripts/light-lane-review-candidates.py"
        self.assertTrue((REPO_ROOT / script).is_file())
        self.assertIn(f"python3 {script} .", self.agent)
        self.assertIn(f"`{script}`", self.claude)


def _split_front_matter(text: str) -> tuple[dict[str, str], str]:
    head, body = text[len("---\n"):].split("\n---\n", 1)
    fields = dict(line.split(": ", 1) for line in head.splitlines())
    return fields, body


class DiffRoundReviewerTests(unittest.TestCase):
    """差分巡の reviewer は、全差分巡の reviewer と観点・手順・テンプレートが同じ。model と effort だけが違う。

    片方の本文だけを直すと、差分巡では観点が抜けたまま（または古いまま）走るので、本文の一致を固定する。
    """

    def setUp(self) -> None:
        if not IN_CANONICAL_REPO:
            self.skipTest("canonical repo 外では root の agent 定義を検査しない")
        diff_agent = AGENT.with_name("light-lane-independent-reviewer-xhigh.md")
        for path in (AGENT, diff_agent):
            self.assertTrue(path.is_file(), path)
        self.full = _split_front_matter(_read(AGENT))
        self.diff = _split_front_matter(_read(diff_agent))

    def test_body_is_identical(self) -> None:
        self.assertEqual(self.diff[1], self.full[1])

    def test_only_name_description_model_and_effort_differ(self) -> None:
        full, diff = self.full[0], self.diff[0]
        self.assertEqual(diff["name"], "light-lane-independent-reviewer-xhigh")
        self.assertEqual((full["model"], full["effort"]), ("opus", "xhigh"))
        self.assertEqual((diff["model"], diff["effort"]), ("fable", "high"))
        ignored = {"name", "description", "model", "effort"}
        self.assertEqual(
            {k: v for k, v in diff.items() if k not in ignored},
            {k: v for k, v in full.items() if k not in ignored},
        )


if __name__ == "__main__":
    unittest.main()

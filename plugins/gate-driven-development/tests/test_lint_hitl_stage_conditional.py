"""段階実装の見出しを、`<gdd-hitl-fields ... stage="none">` を宣言した回だけ要求しない。

対象の lint は 3 本（display-integrity の `段階実装`、human-check-language と
decision-quality の `段階実装サマリー`）。宣言を読む位置は lint-hitl-required-fields.py
と同じ（stop marker の直前で、空行だけを飛ばした最初の非空行がタグ行。marker が
複数あれば全部）。タグが無い・`filled`・不正値・隣接していない・marker の一部だけが
none のときは、今までどおり要求する（fail-closed）。

scripts は subprocess で起動する（`scripts/lib/` と `hooks/scripts/lib/` は同名
パッケージ `lib` を持つため、同じプロセスで両方を import しない）。入口のテストは
`hooks/scripts/lib/hitl_lint_gate.run_hitl_lints` から通す。

Run from plugins/gate-driven-development/:
  python3 -m pytest tests/test_lint_hitl_stage_conditional.py -q
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "hooks" / "scripts"))

from lib.hitl_lint_gate import HITL_MARKER, run_hitl_lints  # noqa: E402

from _paths import PLUGIN_ROOT

SCRIPTS = PLUGIN_ROOT / "scripts"

# (script, 段階実装を要求したときに stdout に出る語)
STAGE_LINTS = (
    ("lint-hitl-display-integrity.py", "missing: 段階実装"),
    ("lint-human-check-language.py", "欄がありません: 段階実装サマリー"),
    ("lint-hitl-decision-quality.py", "missing decision marker: 段階実装サマリー"),
)

# 段階実装の語を 1 つも含まず、ほかの必須語は満たす本文（Stop hook が呼ぶ 3 本を通す）。
BODY_WITHOUT_STAGE = """\
## 確認

### なぜやるか（WHY・根本原因）
テストのための本文です。

### 何を作るか（整理した要件）
整理した要件の本文です。

### 判断ポイント
1. 判断 — 変更前: a / 変更後: b / 採用しない案: c
   - この案を選ぶと次に何が起きるか: 実装へ進む
   - 無回答時のデフォルト: b を採る

### どう作るか（実装する方法・内容）
実装する方法・内容の本文です。

**変更予定ファイル（WHERE）**: dummy.py

### どう確かめるか（検証する方法・内容）
検証する方法・内容の本文です。

### 現在地
完了フェーズ: 要件 / 今やること: OK 判断 / OK後: 設計 / 残タスク: 実装

### どこまで自走するか（どこまで自走するのか）
- OKで進む範囲: 実装 / テスト / PR 作成
- OKでも許可されないこと: merge / deploy
- 人間に戻す条件: scope / AC が変わる場合

### ズレ確認
完了条件の変換: 延期・削除: なし
"""


def _tag(stage: str | None) -> str:
    attrs = 'options="none" arch="none" zure="filled" multi-pr="none"'
    if stage is not None:
        attrs += f' stage="{stage}"'
    return f"<gdd-hitl-fields {attrs}>"


def _doc(stage: str | None, *, body: str = BODY_WITHOUT_STAGE, tagless: bool = False) -> str:
    tag_line = "" if tagless else _tag(stage) + "\n"
    return f"{body}\n{tag_line}{HITL_MARKER}\n## 👤 次にすること\nOK で承認\n"


def _run(script: str, text: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "hitl.md"
        path.write_text(text, encoding="utf-8")
        return subprocess.run(
            [sys.executable, "-I", str(SCRIPTS / script), str(path)],
            text=True,
            capture_output=True,
            check=False,
        )


class StageNoneSkipsStageWordTests(unittest.TestCase):
    def test_stage_none_does_not_require_stage_words(self):
        for script, message in STAGE_LINTS:
            with self.subTest(script=script):
                result = _run(script, _doc("none"))
                self.assertNotIn(message, result.stdout, result.stdout)
                self.assertNotIn("Traceback", result.stderr, result.stderr)

    def test_stage_none_passes_display_integrity_and_language_entirely(self):
        for script in ("lint-hitl-display-integrity.py", "lint-human-check-language.py"):
            with self.subTest(script=script):
                result = _run(script, _doc("none"))
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class StageNoneKeepsOtherWordsTests(unittest.TestCase):
    """`stage="none"` で外すのは段階実装の語だけで、ほかの必須語は今までどおり求める。"""

    OTHER_WORD_MESSAGES = (
        ("lint-hitl-display-integrity.py", "missing: 判断ポイント"),
        ("lint-human-check-language.py", "欄がありません: 判断ポイント"),
        ("lint-hitl-decision-quality.py", "missing decision marker: 判断ポイント"),
    )

    def test_stage_none_still_requires_non_stage_words(self):
        body = BODY_WITHOUT_STAGE.replace("### 判断ポイント", "### 決めること")
        self.assertNotIn("判断ポイント", body)
        for script, message in self.OTHER_WORD_MESSAGES:
            with self.subTest(script=script):
                result = _run(script, _doc("none", body=body))
                self.assertIn(message, result.stdout, result.stdout)
                self.assertNotEqual(result.returncode, 0, result.stdout)


class StageWordStillRequiredTests(unittest.TestCase):
    """宣言が none でなければ今までどおり要求する（fail-closed）。"""

    CASES = {
        "no tag": _doc(None, tagless=True),
        "tag without stage": _doc(None),
        "filled": _doc("filled"),
        "invalid value": _doc("single"),
        "template placeholder": _doc("none|filled"),
        "empty value": _doc(""),
    }

    def test_stage_words_are_required_unless_declared_none(self):
        for script, message in STAGE_LINTS:
            for name, text in self.CASES.items():
                with self.subTest(script=script, case=name):
                    result = _run(script, text)
                    self.assertEqual(result.returncode, 1, result.stdout)
                    self.assertIn(message, result.stdout, result.stdout)

    def test_tag_not_adjacent_to_marker_is_not_a_declaration(self):
        text = f"{BODY_WITHOUT_STAGE}\n{_tag('none')}\n\n本文の行\n\n{HITL_MARKER}\n"
        for script, message in STAGE_LINTS:
            with self.subTest(script=script):
                result = _run(script, text)
                self.assertIn(message, result.stdout, result.stdout)

    def test_every_marker_must_declare_none(self):
        """先に none の組があっても、後ろの marker に宣言が無ければ要求する。"""
        text = f"{_tag('none')}\n{HITL_MARKER}\n\n{BODY_WITHOUT_STAGE}\n{HITL_MARKER}\n"
        for script, message in STAGE_LINTS:
            with self.subTest(script=script):
                result = _run(script, text)
                self.assertIn(message, result.stdout, result.stdout)

    def test_two_markers_both_declaring_none_skip_stage_words(self):
        text = f"{_tag('none')}\n{HITL_MARKER}\n\n{BODY_WITHOUT_STAGE}\n{_tag('none')}\n{HITL_MARKER}\n"
        for script, message in STAGE_LINTS:
            with self.subTest(script=script):
                result = _run(script, text)
                self.assertNotIn(message, result.stdout, result.stdout)


class HookEntryPointTests(unittest.TestCase):
    """Stop hook が呼ぶ `run_hitl_lints`（Stop hook が呼ぶ 3 本）から通す。"""

    def test_single_stage_hitl_with_stage_none_has_no_findings(self):
        failures, errors = run_hitl_lints(PLUGIN_ROOT, _doc("none"))
        self.assertEqual(errors, [])
        self.assertEqual(failures, [], failures)

    def test_same_hitl_without_the_declaration_is_reported(self):
        failures, errors = run_hitl_lints(PLUGIN_ROOT, _doc(None, tagless=True))
        self.assertEqual(errors, [])
        names = {name for name, _ in failures}
        self.assertIn("lint-hitl-display-integrity", names)
        self.assertIn("lint-human-check-language", names)


if __name__ == "__main__":
    unittest.main()

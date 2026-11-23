"""human check の一次表示を、判断ポイントと OK の範囲だけにした形で lint が通る。

一次表示（`references/human-check-template-compact.md`）は、冒頭に前置き 3 行
（依頼・なぜやるか・現在地）を置き、整理した要件・実装する方法・検証する方法の中身は書かず、
`詳細:` の 1 行で `requirements.md` などの場所を指す。ズレ確認の節は、人に残った行があるときだけ書き、無ければ
`<gdd-hitl-fields ... zure="none">` を宣言する（段階実装の `stage="none"` と同じ扱い）。
宣言が無い・`filled` のときは、今までどおりズレ確認を要求する（fail-closed）。

Run from plugins/gate-driven-development/:
  python3 -m pytest tests/test_hitl_primary_surface_shape.py -q
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

# 新しい一次表示の形（判断ポイントと OK の範囲だけ。ズレ確認の節は無い）
PRIMARY_BODY = """\
## 確認

**依頼**: 通知が届かない人がいるので直してほしい
**なぜやるか**: 通知の送り先 a が退職者の宛先になっていて、届かない人がいるため
**現在地**: 要件のレビューまで済み、返事をもらえば設計に進む

決めてほしいことは 1 つで、通知の送り先です。OK は、1 を b で進めるという意味です。

### 判断ポイント
承認ポイント数: 1
1. 通知の送り先を変える — 変更前: a / 変更後: b / 採用しない案: c
   - 判断に影響する前提: なし
   - この案を選ぶと次に何が起きるか: 実装へ進む
   - 依頼との差: なし
   - 無回答時のデフォルト: b を採り、送り先を b にする

### どこまで自走するか（どこまで自走するのか）
- OKで進む範囲: 実装 / テスト / PR 作成
- OKでも許可されないこと: merge / deploy
- 人間に戻す条件: scope / AC が変わる場合
- 延期・削除: なし（完了条件の変換）
- 今やること: 判断ポイントへの返事 / OK後: 設計へ進む

詳細: 整理した要件・実装する方法・内容・変更予定ファイル（WHERE）・検証する方法・内容と、なぜやるかの根拠は `.steering/x/requirements.md`、工程の記録は `state.md`、依頼の原文との突き合わせは `request-crosscheck.md`
"""


def _doc(zure: str | None, *, body: str = PRIMARY_BODY) -> str:
    if zure is None:
        tag_line = ""
    else:
        tag_line = f'<gdd-hitl-fields options="none" arch="none" zure="{zure}" multi-pr="none" stage="none">\n'
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


class PrimarySurfacePassesTests(unittest.TestCase):
    def test_primary_surface_with_zure_none_passes_wired_lints(self):
        failures, errors = run_hitl_lints(PLUGIN_ROOT, _doc("none"))
        self.assertEqual(errors, [])
        self.assertEqual(failures, [], failures)

    def test_primary_surface_has_no_missing_decision_marker(self):
        result = _run("lint-hitl-decision-quality.py", _doc("none"))
        self.assertNotIn("missing decision marker", result.stdout, result.stdout)
        self.assertNotIn("Traceback", result.stderr, result.stderr)


class ZureStillRequiredTests(unittest.TestCase):
    """`zure="none"` の宣言が無ければ、ズレ確認を今までどおり要求する。"""

    def test_zure_filled_without_section_is_reported(self):
        result = _run("lint-hitl-display-integrity.py", _doc("filled"))
        self.assertIn("missing: ズレ確認", result.stdout, result.stdout)

    def test_missing_tag_requires_zure(self):
        result = _run("lint-hitl-display-integrity.py", _doc(None))
        self.assertIn("missing: ズレ確認", result.stdout, result.stdout)

    def test_unknown_value_requires_zure(self):
        result = _run("lint-hitl-display-integrity.py", _doc("na"))
        self.assertIn("missing: ズレ確認", result.stdout, result.stdout)


if __name__ == "__main__":
    unittest.main()

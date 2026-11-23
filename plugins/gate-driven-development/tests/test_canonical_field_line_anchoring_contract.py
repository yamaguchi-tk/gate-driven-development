"""canonical field 行を「行頭アンカー + bullet marker 1 個まで」に固定する契約テスト。

背景（2026-08-30 実測 / task 20260827-c6b-stage2-github-handler-split）:
`gh pr create` が `run-pre-pr-gate-hook.sh` に
`Next Action=gdd-implementation-gating（T-10 impl-gate Attempt #2 へ再入場）` で
block された。`state.md` の `Next Action` は `done` であり、`tasklist.md` の
先頭にも `- Next Action: done` があったが、hook は tasklist.md を先に読む。
`gdd_extract_doc_field` は先頭の `[[:space:]-]*` を**個数無制限で**除去してから
field 名を照合するため、本文 3203 行目の**入れ子 bullet の履歴メモ**

    - `Next Action=gdd-implementation-gating`（T-10 impl-gate Attempt #2 へ再入場）

が canonical field と区別できず、最初の一致として返っていた。
バッククォート除去も行全体に効くので、コード表記の履歴まで一致する。

読み取り規約（本テストが正本）:

- canonical field 行は**行頭から始まる**。先行する空白・タブがある行は field ではない
- 先頭の markdown bullet marker (`-` / `*` / `+`) は **1 個 + 空白まで**許容する
- 入れ子 bullet（`  - Field: ...`）・インデントされた行（コードブロック内の
  記入例を含む）は履歴・散文・例示として扱い、field として読まない

実データ計測（state.md / tasklist.md、2026-08-30）:
本規約で抽出結果が変わるのはごく一部で、すべて
「入れ子の per-task `Status: pass` / `Task ID: T-9`」「コードブロック内の記入例」
「散文の断片」= 誤って拾っていたケースだった。canonical な値を失う file は無かった。

同型の prefix 除去は読み手・書き手の 5 実装に散在しており（`gdd_extract_doc_field` /
`validate-steering-write.py` / `gdd_task_binding.py` / `setup-gdd-loop.sh` /
`collect-gdd-telemetry.py`）、片側だけ直すと「読み手だけ厳格」または
「書き手だけ厳格」の非対称が残る。本テストは表で 5 実装を検査する。

関連契約: 「値の無い canonical 行は現在値ではない」規則（R-1）は本テストが
扱う行頭アンカーとは別次元であり、
tests/test_state_field_value_less_line_contract.py が正本を持つ。
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT as ROOT
DETECT_STEERING_LIB = ROOT / "hooks" / "scripts" / "lib" / "detect-steering.sh"
VALIDATE_WRITE = ROOT / "hooks" / "scripts" / "validate-steering-write.py"
TASK_BINDING = ROOT / "scripts" / "gdd_task_binding.py"
LOOP_SCRIPT = ROOT / "scripts" / "setup-gdd-loop.sh"
TELEMETRY_SCRIPT = ROOT / "scripts" / "collect-gdd-telemetry.py"

BACKTICK = chr(96)

#: 5 実装が**現在も**受理する共通形。本 PR は受理形を増やさない（各実装の
#: 受理形の差は本 incident と別クラスなので触らない）。
SHARED_CANONICAL_FORMS = (
    "Next Action: done",
    "- Next Action: done",
)

#: 閉じ忘れ fence 以降は「fence 無し」として読む。閉じ忘れは実データで発生し、
#: そこから先を全部落とすと canonical field が 1 つも見えなくなる（読み手は routing
#: 材料を失い、書き手バリデータは「触った field が無い」と判断して検査を飛ばす）。
#: 救済が実装から消えたらここで落ちる。5 実装すべてに掛ける。
UNCLOSED_FENCE_CANONICAL_FORM = BACKTICK * 3 + "\n- Next Action: done"

#: backtick fence の info string に ` を含む行は fence **ではない**
#: （CommonMark。"```で囲むこと" のような散文を fence にしないため）。
#: この規約が落ちると直後の canonical field が閉じた fence に飲まれて読めなくなる。
#: 閉じ fence を後ろに置くのは、開きっぱなしだと閉じ忘れ救済で中身が残り
#: 判別力を失うため（実測: 救済のせいで規約撤去を検出できなかった）。
BACKTICK_IN_INFO_IS_NOT_A_FENCE_FORM = (
    BACKTICK * 3 + " " + BACKTICK + "x" + BACKTICK + "\n- Next Action: done\n" + BACKTICK * 3
)

#: 実装ごとの現行受理形。2026-08-30 に shipped 実装へ全形を通して実測した表で、
#: 本 PR の変更が「入れ子・インデントの除外」だけであることを固定する。
CANONICAL_FORMS_BY_IMPL = {
    "extract_doc_field": (
        UNCLOSED_FENCE_CANONICAL_FORM,
        BACKTICK_IN_INFO_IS_NOT_A_FENCE_FORM,
        "Next Action: done",
        "Next Action=done",
        "- Next Action: done",
        "- Next Action=done",
        f"- {BACKTICK}Next Action{BACKTICK}: done",
        f"- {BACKTICK}Next Action: done{BACKTICK}",
    ),
    "validate_steering_write": (
        UNCLOSED_FENCE_CANONICAL_FORM,
        BACKTICK_IN_INFO_IS_NOT_A_FENCE_FORM,
        "Next Action: done",
        "Next Action=done",
        "- Next Action: done",
        "- Next Action=done",
        "Next Action : done",
        f"- {BACKTICK}Next Action{BACKTICK}: done",
        f"- {BACKTICK}Next Action: done{BACKTICK}",
    ),
    "task_binding": (
        UNCLOSED_FENCE_CANONICAL_FORM,
        BACKTICK_IN_INFO_IS_NOT_A_FENCE_FORM,
        "Next Action: done",
        "Next Action=done",
        "- Next Action: done",
        "- Next Action=done",
    ),
    "loop_parse_field": (
        UNCLOSED_FENCE_CANONICAL_FORM,
        BACKTICK_IN_INFO_IS_NOT_A_FENCE_FORM,
        "Next Action: done",
        "Next Action=done",
        "- Next Action: done",
        "- Next Action=done",
        "* Next Action: done",
        "Next Action : done",
        f"- {BACKTICK}Next Action: done{BACKTICK}",
    ),
    "telemetry": (
        UNCLOSED_FENCE_CANONICAL_FORM,
        BACKTICK_IN_INFO_IS_NOT_A_FENCE_FORM,
        "Next Action: done",
        "- Next Action: done",
        "Next Action : done",
    ),
}

FENCE = BACKTICK * 3

#: canonical と認めてはいけない形。入れ子 bullet・インデント行・fenced code block。
#: 全 5 実装がこの表全体を拒否すること。
#: fence 形は「state.md に書式の記入例を 1 つ置くだけで field が成立する」欠陥を閉じる。
#: 読み手だけを fence 対応にすると、書き手バリデータが通した state.md を読み手が
#: 別の値で routing する非対称が残るため、5 実装を同じ表で同時に拘束する。
NON_CANONICAL_FORMS = (
    f"{FENCE}\n- Next Action: gdd-implementation-gating\n{FENCE}",
    f"{FENCE}markdown\n- Next Action: gdd-implementation-gating\n{FENCE}",
    f"{FENCE}\nNext Action: gdd-implementation-gating\n{FENCE}",
    "~~~\n- Next Action: gdd-implementation-gating\n~~~",
    f"  {FENCE}\n- Next Action: gdd-implementation-gating\n  {FENCE}",
    # TAB インデントした fence。半角スペースだけを見る fence 正規表現だと素通りし、
    # A-4（記入例が証跡になる）が復活する（merge gate の hook 実起動で確認）。
    f"\t{FENCE}\n- Next Action: gdd-implementation-gating\n\t{FENCE}",
    # **閉じた** fence のあとに閉じ忘れ fence がある形。閉じ忘れ時に本文を丸ごと
    # 返すと、それ以前の正しく閉じた記入例まで復活する。閉じ忘れの救済は
    # 「未閉鎖の開き fence 以降を残す」であって「全部を残す」ではない。
    f"{FENCE}\n- Next Action: gdd-implementation-gating\n{FENCE}\n\n{FENCE}\nleftover",
    # 開き fence の info string が canonical field 形。fence の**区切り行そのもの**を
    # 落とさないと、開き行に書いた記入例が現在値として読まれる。
    f"{FENCE}- Next Action: gdd-implementation-gating\n{FENCE}",
    # 4 連バッククォートで包んだ ``` 入りブロック。素朴なトグルは内側の ``` で
    # 反転して中身が見えてしまう（開き fence の記号種別と長さを保持すれば閉じる）。
    f"{BACKTICK * 4}\n{FENCE}\n- Next Action: gdd-implementation-gating\n{FENCE}\n{BACKTICK * 4}",
    f"  - {BACKTICK}Next Action=gdd-implementation-gating{BACKTICK}（Attempt #2 へ再入場）",
    "  - Next Action: gdd-implementation-gating",
    "    - Next Action: gdd-implementation-gating",
    "\t- Next Action: gdd-implementation-gating",
    "     Next Action: gdd-implementation-gating",
    "  Next Action: gdd-implementation-gating",
    "  Next Action : gdd-implementation-gating",
)


#: field 名は別 field の接頭辞であってはならない。`Task` を読む経路が
#: `Task Size: standard` に一致すると、値として `standard` が返る。実害として
#: `setup-gdd-loop.sh` の worktree pollution 判定が全 steering を
#: `state_task_mismatch` と誤検知し、auto-resume を無効化して GDD loop が
#: 張れなくなった（2026-08-31 実測。`Task ID` を明示した steering だけが逃れる）。
#: 5 実装すべてがこの表を拒否すること。
FIELD_NAME_PREFIX_FORMS = (
    "Task Size: standard",
    "- Task Size: standard",
    "- Task Size=standard",
    "- Task Sizing: quick",
)

#: 逆に、完全一致の field は読めること（上の拒否が過剰でないことを固定する）。
FIELD_NAME_EXACT_FORMS = (
    "Task: 20260831-example",
    "- Task: 20260831-example",
)


def _extract_doc_field(text: str, field: str, tmp_path: Path) -> str:
    """shipped の `gdd_extract_doc_field` をそのまま実行して値を取る。"""
    target = tmp_path / "doc.md"
    target.write_text(text, encoding="utf-8")
    script = (
        f'source "{DETECT_STEERING_LIB}"; '
        f'gdd_extract_doc_field "{target}" "{field}"'
    )
    proc = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    # `assert` は `python -O` で無効化され失敗を素通りさせるため、明示的に送出する
    if proc.returncode != 0:
        raise AssertionError(
            f"gdd_extract_doc_field の実行に失敗した (returncode={proc.returncode}): {proc.stderr}"
        )
    return proc.stdout.strip()


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_loop_parse_field():
    """`setup-gdd-loop.sh` の heredoc から parse_field 系の定義だけを取り出す。

    抽出方法は `test_state_field_backtick_parsing_contract.py` と同じ。
    """
    source = LOOP_SCRIPT.read_text(encoding="utf-8")
    blocks = []
    backtick = re.search(r"^BACKTICK = .*$", source, re.MULTILINE)
    assert backtick, f"BACKTICK definition not found in {LOOP_SCRIPT}"
    blocks.append(backtick.group(0))
    for name in ("normalize_line", "strip_fenced_blocks", "parse_field"):
        match = re.search(
            rf"^def {name}\(.*?(?=^def |\n^[a-zA-Z@#])", source, re.MULTILINE | re.DOTALL
        )
        assert match, f"{name} definition not found in {LOOP_SCRIPT}"
        blocks.append(match.group(0))
    namespace: dict = {}
    exec("\n".join(blocks), namespace)  # noqa: S102 - shipped source を直接検証するため
    return namespace["parse_field"]


class ExtractDocFieldAnchoringTests(unittest.TestCase):
    """読み手の正本 `gdd_extract_doc_field`（hook 群の共有経路）"""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_canonical_forms_are_read(self) -> None:
        for form in CANONICAL_FORMS_BY_IMPL["extract_doc_field"]:
            with self.subTest(form=form):
                self.assertEqual(
                    _extract_doc_field(form + "\n", "Next Action", self.tmp), "done"
                )

    def test_nested_and_indented_forms_are_not_read(self) -> None:
        for form in NON_CANONICAL_FORMS:
            with self.subTest(form=form):
                self.assertEqual(
                    _extract_doc_field(form + "\n", "Next Action", self.tmp), ""
                )

    def test_canonical_line_wins_over_earlier_history_note(self) -> None:
        """報告された block の再現。履歴メモが先頭でも canonical が返る。"""
        text = (
            "# Tasklist\n"
            f"  - {BACKTICK}Next Action=gdd-implementation-gating{BACKTICK}"
            "（T-10 impl-gate Attempt #2 へ再入場）\n"
            f"  - {BACKTICK}Next Action=gdd-systematic-debugging{BACKTICK}\n"
            "- Next Action: done\n"
        )
        self.assertEqual(_extract_doc_field(text, "Next Action", self.tmp), "done")

    def test_nested_per_task_status_does_not_shadow_document_status(self) -> None:
        """入れ子の per-task `- Status: pass` を doc-level Status として返さない。"""
        text = "## Tasks\n- T-1\n  - Status: pass\n"
        self.assertEqual(_extract_doc_field(text, "Status", self.tmp), "")

    def test_prefix_of_longer_field_is_not_read(self) -> None:
        for form in FIELD_NAME_PREFIX_FORMS:
            with self.subTest(form=form):
                self.assertEqual(_extract_doc_field(form + "\n", "Task", self.tmp), "")

    def test_exact_field_is_still_read(self) -> None:
        for form in FIELD_NAME_EXACT_FORMS:
            with self.subTest(form=form):
                self.assertEqual(
                    _extract_doc_field(form + "\n", "Task", self.tmp), "20260831-example"
                )


class ValidateSteeringWriteAnchoringTests(unittest.TestCase):
    """書き手側 `validate-steering-write.py` を読み手と同じ規約に揃える"""

    def setUp(self) -> None:
        self.mod = _load_module(VALIDATE_WRITE, "validate_steering_write_line_anchor")

    def test_canonical_forms_are_fields(self) -> None:
        for form in CANONICAL_FORMS_BY_IMPL["validate_steering_write"]:
            with self.subTest(form=form):
                self.assertTrue(self.mod.has_state_field_line(form + "\n", "Next Action"))
                self.assertTrue(self.mod.has_state_field(form + "\n", "Next Action"))

    def test_nested_and_indented_forms_are_not_fields(self) -> None:
        for form in NON_CANONICAL_FORMS:
            with self.subTest(form=form):
                self.assertFalse(self.mod.has_state_field_line(form + "\n", "Next Action"))
                self.assertFalse(self.mod.has_state_field(form + "\n", "Next Action"))
                self.assertEqual(self.mod.state_field_value(form + "\n", "Next Action"), "")

    def test_reader_and_writer_agree_on_every_form(self) -> None:
        """書き手が field と数える行は、読み手も同じ値を読めること。

        片側だけ厳格だと「書けたのに gate から見えない」（本 incident）または
        「書けないのに gate は読む」の非対称が残る。
        """
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            for form in SHARED_CANONICAL_FORMS + NON_CANONICAL_FORMS:
                with self.subTest(form=form):
                    writer_sees = self.mod.has_state_field(form + "\n", "Next Action")
                    reader_value = _extract_doc_field(form + "\n", "Next Action", tmp)
                    self.assertEqual(writer_sees, bool(reader_value), form)

    def test_prefix_of_longer_field_is_not_read(self) -> None:
        for form in FIELD_NAME_PREFIX_FORMS:
            with self.subTest(form=form):
                self.assertFalse(self.mod.has_state_field(form + "\n", "Task"))
                self.assertEqual(self.mod.state_field_value(form + "\n", "Task"), "")

    def test_exact_field_is_still_read(self) -> None:
        for form in FIELD_NAME_EXACT_FORMS:
            with self.subTest(form=form):
                self.assertTrue(self.mod.has_state_field(form + "\n", "Task"))
                self.assertEqual(
                    self.mod.state_field_value(form + "\n", "Task"), "20260831-example"
                )


class TaskBindingFieldAnchoringTests(unittest.TestCase):
    """pre-PR gate の binding 解決 `gdd_task_binding._field`"""

    def setUp(self) -> None:
        self.mod = _load_module(TASK_BINDING, "gdd_task_binding_line_anchor")

    def test_canonical_forms_are_read(self) -> None:
        for form in CANONICAL_FORMS_BY_IMPL["task_binding"]:
            with self.subTest(form=form):
                self.assertEqual(self.mod._field(form + "\n", "Next Action"), "done")

    def test_nested_and_indented_forms_are_not_read(self) -> None:
        for form in NON_CANONICAL_FORMS:
            with self.subTest(form=form):
                self.assertEqual(self.mod._field(form + "\n", "Next Action"), "")

    def test_prefix_of_longer_field_is_not_read(self) -> None:
        for form in FIELD_NAME_PREFIX_FORMS:
            with self.subTest(form=form):
                self.assertEqual(self.mod._field(form + "\n", "Task"), "")

    def test_exact_field_is_still_read(self) -> None:
        for form in FIELD_NAME_EXACT_FORMS:
            with self.subTest(form=form):
                self.assertEqual(self.mod._field(form + "\n", "Task"), "20260831-example")


class LoopParseFieldAnchoringTests(unittest.TestCase):
    """`setup-gdd-loop.sh` の terminal 判定 `parse_field`"""

    def setUp(self) -> None:
        self.parse_field = _load_loop_parse_field()

    def test_canonical_forms_are_read(self) -> None:
        for form in CANONICAL_FORMS_BY_IMPL["loop_parse_field"]:
            with self.subTest(form=form):
                self.assertEqual(self.parse_field(form + "\n", ["Next Action"]), "done")

    def test_nested_and_indented_forms_are_not_read(self) -> None:
        for form in NON_CANONICAL_FORMS:
            with self.subTest(form=form):
                self.assertEqual(self.parse_field(form + "\n", ["Next Action"]), "")

    def test_prefix_of_longer_field_is_not_read(self) -> None:
        """`Task Size: standard` を `Task` として読まない（pollution 誤検知の原因）。

        pollution 判定は `parse_field(text, ["Task ID", "Steering ID", "Task"])` を
        使うため、末尾候補 `Task` が `Task Size` に一致すると全 steering の
        `state_task_id` が `standard` になり、`state_task_mismatch` が恒真になる。
        """
        for form in FIELD_NAME_PREFIX_FORMS:
            with self.subTest(form=form):
                self.assertEqual(
                    self.parse_field(form + "\n", ["Task ID", "Steering ID", "Task"]), ""
                )

    def test_exact_field_is_still_read(self) -> None:
        for form in FIELD_NAME_EXACT_FORMS:
            with self.subTest(form=form):
                self.assertEqual(
                    self.parse_field(form + "\n", ["Task ID", "Steering ID", "Task"]),
                    "20260831-example",
                )


class TelemetryExtractFieldAnchoringTests(unittest.TestCase):
    """`collect-gdd-telemetry.py` の集計 `extract_field`"""

    def setUp(self) -> None:
        self.mod = _load_module(TELEMETRY_SCRIPT, "collect_gdd_telemetry_line_anchor")

    def test_canonical_forms_are_read(self) -> None:
        for form in CANONICAL_FORMS_BY_IMPL["telemetry"]:
            with self.subTest(form=form):
                self.assertEqual(self.mod.extract_field(form + "\n", "Next Action"), "done")

    def test_nested_and_indented_forms_are_not_read(self) -> None:
        for form in NON_CANONICAL_FORMS:
            with self.subTest(form=form):
                self.assertIsNone(self.mod.extract_field(form + "\n", "Next Action"))

    def test_prefix_of_longer_field_is_not_read(self) -> None:
        for form in FIELD_NAME_PREFIX_FORMS:
            with self.subTest(form=form):
                self.assertIsNone(self.mod.extract_field(form + "\n", "Task"))

    def test_exact_field_is_still_read(self) -> None:
        for form in FIELD_NAME_EXACT_FORMS:
            with self.subTest(form=form):
                self.assertEqual(
                    self.mod.extract_field(form + "\n", "Task"), "20260831-example"
                )


class SchemaDocReconciliationTests(unittest.TestCase):
    """`references/state-schema.json` の宣言と shipped 実装が一致すること。

    doc に規約を書いただけでは、実装が変わったときに文面だけ残って drift する。
    doc の `allowed_line_prefix` を**読み出して**実装へ通し、宣言どおりに
    読める / 読めないことを機械検査する。
    """

    def test_declared_prefixes_agree_with_the_reader(self) -> None:
        schema = json.loads((ROOT / "references" / "state-schema.json").read_text("utf-8"))
        form = schema["canonical_line_form"]
        self.assertTrue(form["indented_lines_are_not_fields"])
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            for prefix in form["allowed_line_prefix"]:
                line = f"{prefix}Next Action: done"
                with self.subTest(prefix=prefix):
                    self.assertEqual(
                        _extract_doc_field(line + "\n", "Next Action", tmp), "done", line
                    )
                    # 同じ行でも インデントすれば field ではなくなる
                    self.assertEqual(
                        _extract_doc_field("  " + line + "\n", "Next Action", tmp), "", line
                    )


if __name__ == "__main__":
    unittest.main()

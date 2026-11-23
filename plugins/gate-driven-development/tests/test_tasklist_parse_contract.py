"""`lib/tasklist_parse` の受理面と名前抽出の契約テスト（AC-4 / AC-5 / AC-6、CT-4）。

実行: `python3 -m pytest plugins/gate-driven-development/tests/test_tasklist_parse_contract.py -q`

受理面は `hooks/scripts/run-pre-tool-use-plan-reread-hook.sh` の `_task_heading_re` と
同値であることを要求する（python reader が bash reader より狭いと、bash が読める節を
python が「非標準の内容」に落として停止を塞ぐ非対称が残るため）。
negative 側の pin は「受理を広げる方向の退行」を止めるためにあり、変異注入で
判別力を実測している。**pin する文字列は変異体が受理する形でなければ空虚になる**
（実測: `Task` → `Tasks?` の変異は `### Tasks:`（名前なし）を受理しないので、
その形を pin しても退行を検出できない。名前付きの `### Tasks: 一覧` で pin する）。
"""
from __future__ import annotations
import itertools
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

# `python3 -m unittest tests.<module>` でも共有ヘルパを解決できるようにする
# （pytest は tests/ を自動で path に入れるが unittest は入れない）。
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _plugin_module_loader import PLUGIN_ROOT, load_plugin_module  # noqa: E402

_mod = load_plugin_module("hooks/scripts/lib/tasklist_parse.py")
classify_task_line = _mod.classify_task_line
task_name = _mod.task_name


class ClassifyTaskLineTests(unittest.TestCase):
    def test_colon_form_is_task(self):
        self.assertEqual(classify_task_line("### Task: T-1 | AC-01 | desc"), "task")

    def test_numbered_form_is_task(self):
        self.assertEqual(classify_task_line("### Task 1: 説明"), "task")
        self.assertEqual(classify_task_line("### Task 12: 説明"), "task")

    def test_list_item_form_is_task(self):
        self.assertEqual(classify_task_line("- T1 | AC-01 | desc"), "task")
        self.assertEqual(classify_task_line("- T-1 | AC-01 | desc"), "task")

    def test_bash_reader_forms_are_task(self):
        """bash reader（plan-reread hook）の正規表現が受理する形は python 側も受理する。

        同 hook のコメントは実データを測って「`### Task <N>:` と `- Task: <name>`
        が多数派」と記録している。python 側だけ狭いと同じ節で判定が割れる。

        ここで言う「受理」は **`_task_heading_re` 単体**の話。`## Task 3:` は正規表現には
        一致するが、hook のループは `## ` で始まる行を先に `break` するため reader 内では
        そこまで到達しない。受理面の同値は `BashReaderEquivalenceTests` が直積で担保する。
        """
        self.assertEqual(classify_task_line("- Task: T20 - PR creation"), "task")
        self.assertEqual(classify_task_line("* Task: T21 - follow-up"), "task")
        self.assertEqual(classify_task_line("#### Task: T-2 | AC-02 | desc"), "task")
        self.assertEqual(classify_task_line("## Task 3: 説明"), "task")

    def test_dash_t_helper_is_not_task(self):
        # "- T-helper" は digit で始まらないので task 扱いしない（既存の false-positive 回避）
        self.assertEqual(classify_task_line("- T-helper | not a task"), "other")

    def test_list_item_without_pipe_is_not_task(self):
        """`- T1` で始まっても `|` が無ければ task 扱いしない。

        これを外すと `- T1 の作業を完了した` のような散文が未完了タスクに計上され、
        done guard が偽の未完了を理由に停止を塞ぐ。
        """
        self.assertEqual(classify_task_line("- T1 の作業を完了した"), "other")
        self.assertEqual(classify_task_line("- T-1 は対象外"), "other")

    def test_task_lookalikes_are_not_task(self):
        """`Task` で始まるだけの見出し・フィールドを task にしない（受理を広げる退行の pin）。

        `### Task Size Distribution` は `scripts/collect-gdd-telemetry.py` に実在する
        文字列で、task と誤判定すると telemetry と done guard の両方が壊れる。
        `- Task ID:` / `- Task Size:` は steering の実データに存在するフィールド行。

        見出しレベルの**両端**を pin する。`##### Task:`（深すぎ）だけでなく
        `# Task:`（浅すぎ）も pin するのは、bash reader が `# Task: x` を不受理と
        実測しているため（`#{2,4}` → `#{1,4}` の 1 文字変異で同値性が無言で壊れる）。
        `### Task:`（名前なし）は名前群を緩める変異の pin。`+ Task:` は markdown の
        正規の bullet だが **bash reader が不受理**（実測）なので、`[-*]` → `[-*+]` の
        1 文字変異で「bash と同値」主張が無言で壊れるのを止める。
        """
        for line in (
            "### Task Size Distribution",
            "### Tasks: 一覧",
            "### Task-1: 説明",
            "- Task ID: T-0N",
            "- Task Size: standard",
            "##### Task: too deep",
            "# Task: too shallow",
            "+ Task: plus bullet",
            "### Task:",
            "### Verification",
        ):
            with self.subTest(line=line):
                self.assertEqual(classify_task_line(line), "other")

    def test_plain_heading_is_other(self):
        self.assertEqual(classify_task_line("### Verification"), "other")


class TaskNameTests(unittest.TestCase):
    """名前抽出を受理面と同じ場所に置く（呼び出し側に見出し形の再導出を残さない）。"""

    def test_name_for_each_accepted_form(self):
        cases = {
            "### Task: T-1 | AC-01 | desc": "T-1 | AC-01 | desc",
            "### Task 1: 説明": "説明",
            "### Task 12: 説明": "説明",
            "- Task: T20 - PR creation": "T20 - PR creation",
            "#### Task: T-2 | AC-02 | d": "T-2 | AC-02 | d",
            "- T1 | AC-01 | desc": "T1 | AC-01 | desc",
            "- T-1 | AC-01 | desc": "T-1 | AC-01 | desc",
        }
        for line, expected in cases.items():
            with self.subTest(line=line):
                self.assertEqual(task_name(line), expected)

    def test_numbered_heading_name_does_not_leak_prefix(self):
        """素朴な文字列置換だと `# Task 1: 説明` になる欠落形を pin する。"""
        self.assertEqual(task_name("### Task 1: 説明"), "説明")
        self.assertNotIn("Task", task_name("### Task 1: 説明"))

    def test_name_is_stripped_of_full_width_space(self):
        """全角空白は正規表現の `[ \\t]*` では落ちず `.strip()` だけが落とす。

        日本語の steering 実データで起きうる形。`.strip()` を外す退行を pin する
        （半角空白だけで pin すると呼び出し側の strip 済み契約と重なって空虚になる）。
        """
        self.assertEqual(task_name("### Task:\u3000説明"), "説明")
        self.assertEqual(task_name("- T1 | desc\u3000"), "T1 | desc")

    def test_list_item_form_requires_hyphen_bullet(self):
        """`- T<n> | ...` は `-` のみ受理する（受理面の境界を明示的に固定する）。

        見出し形が `[-*]` 両方を受理するのに対し非対称だが、これは bash reader との
        同値要求が見出し形にしか及ばないため。2026-08-22 実測で
        `~/.gdd/worktrees/**/.steering/*/tasklist.md` の `- T<n> | ...` 形はあり、
        `* T<n>` 形は **無い**。実データにない形へ受理を広げない（YAGNI）。
        """
        self.assertEqual(classify_task_line("* T1 | AC-01 | desc"), "other")
        self.assertEqual(task_name("* T1 | AC-01 | desc"), "")

    def test_non_task_returns_empty(self):
        self.assertEqual(task_name("### Verification"), "")
        self.assertEqual(task_name("- T-helper | x"), "")
        self.assertEqual(task_name("- T1 の作業を完了した"), "")

    def test_classify_and_name_never_disagree(self):
        """`classify(s) == "task"` ⟺ `task_name(s) != ""` を全 fixture 行で固定する。

        この 2 つが割れると「task として数えるが名前が消える」= 本 PR が閉じようと
        している silent failure そのものになる。実装は `classify_task_line` を
        `task_name` から導出しているので構造的に割れないが、導出をやめて分岐を
        二重化する退行をこの pin が止める。

        **判別力の要は「コロンの後が全角空白だけ」の行**（実測: 二分岐版は
        `### Task:\u3000` を `task` と分類するが `task_name()` は `""` を返す。
        `[ \\t]*` は全角空白を消費しないので `(.+)` が一致し、`.strip()` が名前を
        空にするため）。この行が無いと導出化を戻す変異が生き残る ―― 実際に
        Attempt 3 の reviewer が生存を実測した。
        """
        for line in (
            "### Task: T-1 | AC-01 | desc",
            "### Task 1: 説明",
            "### Task 12: 説明",
            "- Task: T20 - PR creation",
            "* Task: T21 - follow-up",
            "#### Task: T-2 | AC-02 | desc",
            "## Task 3: 説明",
            "- T1 | AC-01 | desc",
            "- T-1 | AC-01 | desc",
            "### Task Size Distribution",
            "### Tasks: 一覧",
            "### Task-1: 説明",
            "- Task ID: T-0N",
            "- Task Size: standard",
            "##### Task: too deep",
            "# Task: too shallow",
            "### Task:",
            "### Task:\u3000",
            "### Task 1:\u3000",
            "- T1 |\u3000",
            "+ Task: plus bullet",
            "### Verification",
            "- T-helper | x",
            "- T1 の作業を完了した",
        ):
            with self.subTest(line=line):
                self.assertEqual(
                    classify_task_line(line) == "task",
                    task_name(line) != "",
                )


# ---------------------------------------------------------------------------
# bash reader との同値を「生成的 differential」で担保する
#
# 一点 pin を指摘のたびに足す方式は 3 attempt 続けて破られた（`# Task:` / `##### Task:`
# / `+ Task:` / `[Tt]ask` / `[ \t]+Task` がいずれも 1 文字変異で通り抜けた）。
# 個別の形を列挙するのをやめ、**境界の直積を実際の bash 正規表現に通して突き合わせる**。
# 正規表現は hook ファイルから読み出すので、**生成した形の範囲で**片側だけ変えれば落ちる。
# 「どんな 1 文字変異でも落ちる」わけではない ―― 直積が振っていない次元（例: 空白 3 個以上、
# 5 桁採番）への変異は素通りする。振っている次元は下の `_boundary_product` の定義が正本。
# ---------------------------------------------------------------------------
_READER = PLUGIN_ROOT / "hooks" / "scripts" / "run-pre-tool-use-plan-reread-hook.sh"


def _bash_heading_re() -> str:
    """hook ファイルから `_task_heading_re` の値をそのまま取り出す。"""
    m = re.search(r"^_task_heading_re='([^']+)'$", _READER.read_text(encoding="utf-8"), re.MULTILINE)
    if not m:
        raise AssertionError(f"_task_heading_re not found in {_READER}")
    return m.group(1)


def _bash_classify(lines: list[str]) -> list[str]:
    """各行を bash の `[[ =~ ]]` に通して "task" / "other" を返す。

    正規表現はコマンドラインに埋め込まず環境変数で渡す（hook 本体も同じ理由で
    変数経由にしている）。入力は末尾改行を付ける ―― `read -r` は改行で終わらない
    最終行を捨てるため、付け忘れると**最後の 1 形だけ検証されない**。
    """
    script = (
        "while IFS= read -r line; do\n"
        '  if [[ "$line" =~ $GDD_TASK_HEADING_RE ]]; then echo task; else echo other; fi\n'
        "done\n"
    )
    proc = subprocess.run(
        ["bash", "-c", script],
        input="\n".join(lines) + "\n",
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "GDD_TASK_HEADING_RE": _bash_heading_re()},
    )
    out = proc.stdout.splitlines()
    # `assert` は `python -O` で消える。判定行が欠けたまま返すと以降の突き合わせが
    # 静かに短絡するため、明示的に送出する。
    if len(out) != len(lines):
        raise AssertionError(f"bash returned {len(out)} verdicts for {len(lines)} lines")
    return out


def _boundary_product() -> list[str]:
    """受理面の**空白位置 4 つすべて**を変化させた直積を返す。

    振っている次元は 4 つ: **空白の位置**（4 箇所すべて）、**空白の繰り返し数**（0/1/2 個と tab）、
    **採番の桁数**（0/1/2/3/4 桁）、**末尾の形**（無/コロン/コロン+名前/コロン+空白のみ）。

    位置しか振らなかった初版は `\\d*` -> `\\d{0,2}` / `Task[ \\t]*` -> `Task[ ]*` を、
    繰り返し数を振らなかった次版は `[ \\t]*` -> `[ \\t]?` / `\\d*` -> `\\d{0,3}` を
    それぞれ取りこぼした（いずれも実測）。**振っていない次元への変異は今も素通りする**
    ので、受理面を変えるときはこの直積の次元自体を見直すこと。
    """
    bullets = ["#", "##", "###", "####", "#####", "-", "*", "+"]
    seps = ["", " ", "  ", "\t"]
    words = ["Task", "task", "TASK", "Tasks", "Task ID"]
    nums = ["", "1", "12", "007", "1234"]
    tails = ["", ":", ": x", ":  "]
    return sorted(
        {
            b + s1 + w + s2 + n + s3 + t
            for b, s1, w, s2, n, s3, t in itertools.product(
                bullets, seps, words, seps, nums, seps, tails
            )
        }
    )


class BashReaderEquivalenceTests(unittest.TestCase):
    """見出し形の受理面が bash reader とどう一致し、どこで意図的に食い違うかを直積で固定する。

    **「完全一致」ではない**。python 側は `[ \\t]`、bash 側は `[[:space:]]` で文字クラスが
    違い、さらに python は「名前が空白のみ」の行をタスクとして扱わない。等式で書くと
    測っていない範囲まで主張することになるので、**許される食い違いの型を明示する**形にする。
    """

    def test_boundary_product_matches_bash_reader(self):
        lines = _boundary_product()
        verdicts = _bash_classify(lines)

        # hollow check: 生成集合が片側に偏ったら、differential は何も測っていないのに緑になる。
        # 生成集合の件数は固定しない。bash の受理数は reader の挙動なので、実測（2026-08-22）の値で固定する
        accepted = verdicts.count("task")
        self.assertEqual(accepted, 3000, "bash の受理数が変わった（意図した変更なら実測し直す）")
        self.assertGreater(len(lines), accepted, "bash が受理しない行が生成されていない")

        # 許される食い違いは 1 型だけ: bash が受理し python が受理しない、かつ
        # **コロンの後が空白のみ**（python は名前が空の見出しをタスクと数えない）。
        blank_name = re.compile(r"^(?:#{2,4}|[-*])[ \t]*Task[ \t]*\d*[ \t]*:[ \t]*$")
        unexpected = []
        known = 0
        for line, bash in zip(lines, verdicts):
            py = classify_task_line(line)
            if py == bash:
                continue
            if bash == "task" and py == "other" and blank_name.match(line):
                known += 1
                continue
            unexpected.append((line, bash, py))

        self.assertEqual(unexpected[:10], [], f"未知の食い違い {len(unexpected)} 件")
        # 既知の乖離が 0 になったら受理面が変わった合図。この pin ごと再実測する
        self.assertEqual(known, 1500, "「名前が空白のみ」の乖離数が変わった")

    def test_non_ascii_space_divergence_is_known_and_absent_from_real_data(self):
        """bash の `[[:space:]]` は `\\v` `\\f` `\\r` U+3000 も受理するが python の `[ \\t]` は受理しない。

        これは既知の乖離。**実データには無い**（2026-08-22 実測:
        `~/.gdd/worktrees/**/.steering/*/tasklist.md` の `Task` を含む行に、
        非 ASCII 空白で始まる見出しも名前が空の見出しも無かった）。受理面を広げるのは YAGNI なので
        **広げずに乖離を固定する**。乖離が消えたら python 側が広がった合図で、design 判断に戻す。
        """
        lines = ["###\vTask: x", "###\fTask: x", "###\rTask: x", "###\u3000Task: x"]
        self.assertEqual(_bash_classify(lines), ["task"] * 4)
        for line in lines:
            self.assertEqual(classify_task_line(line), "other")

    def test_list_item_form_is_a_deliberate_python_only_superset(self):
        """`- T<n> | ...` は python 側だけの受理形（bash reader には無い）。

        上の differential は見出し形の直積しか生成しないので、この非対称が
        「取りこぼし」ではなく意図であることを別途固定する。
        """
        lines = ["- T1 | AC-01 | desc", "- T-1 | AC-01 | desc"]
        self.assertEqual(_bash_classify(lines), ["other", "other"])
        for line in lines:
            self.assertEqual(classify_task_line(line), "task")
        self.assertEqual(classify_task_line("* T1 | AC-01 | desc"), "other")
        self.assertEqual(task_name("-T1 | AC-01 | desc"), "")


class FenceIndentTests(unittest.TestCase):
    """`strip_fenced_lines()` の境界を固定する。

    GDD の tasklist は `#### Steps` の**リスト項目の下**に fence を置くのが普通で、
    CommonMark の「開き fence は indent 0〜3」をそのまま適用すると、実データの多くが
    fence と認識されず中身が構造行として漏れる。
    実測値と導出コマンドは `.steering/<task>/design.md § 論点 2c` が正本。
    """

    def _strip(self, text):
        return _mod.strip_fenced_lines(text)

    def test_indented_fence_is_recognised(self):
        text = (
            "## Pending Tasks\n"
            "1. RED を書く\n"
            "   - Code:\n"
            "     ```python\n"
            "     - T1 | AC-01 | still open\n"
            "     ```\n"
            "- T2 | AC-02 | real\n"
        )
        lines, unclosed = self._strip(text)
        self.assertFalse(unclosed)
        self.assertNotIn("     - T1 | AC-01 | still open", lines)
        self.assertIn("- T2 | AC-02 | real", lines)

    def test_deeply_indented_fence_is_recognised(self):
        text = "## A\n" + " " * 12 + "```\n" + " " * 12 + "- T1 | x\n" + " " * 12 + "```\n- T2 | y\n"
        lines, unclosed = self._strip(text)
        self.assertFalse(unclosed)
        self.assertNotIn(" " * 12 + "- T1 | x", lines)
        self.assertIn("- T2 | y", lines)

    def test_closing_fence_must_not_carry_an_info_string(self):
        """閉じ側にも info string 判定が要る。

        ネストした ```` ```json ```` を閉じ扱いにすると、以降の行が構造として漏れる。
        実データにも該当形がある（4 連 fence の中に ```json を書く形）。
        """
        text = "## A\n````\n```json\n{}\n```\n````\n- T2 | y\n"
        lines, unclosed = self._strip(text)
        self.assertFalse(unclosed)
        self.assertEqual([ln for ln in lines if ln.startswith("- T")], ["- T2 | y"])
        self.assertNotIn("{}", lines)
        # `~~~ py` のような info 付きの閉じ候補も閉じない
        text2 = "## A\n~~~\n- T1 | x\n~~~ py\n- T2 | y\n"
        _lines2, unclosed2 = self._strip(text2)
        self.assertTrue(unclosed2, "info string 付きの行で閉じてしまっている")

    def test_opening_fence_with_backtick_in_info_is_not_a_fence(self):
        text = "## A\n```md`inline`\n- T1 | x\n"
        lines, unclosed = self._strip(text)
        self.assertFalse(unclosed)
        self.assertIn("- T1 | x", lines)

    def test_longer_closing_marker_closes_the_fence(self):
        """閉じ記号は開きより**長くてもよい**（CommonMark）。

        `>=` を `==` に狭めると、````` ```` ````` で閉じた ```` ``` ```` の fence が
        閉じず、以降が全部読み飛ばされて **恒久 block** になる。
        """
        text = "## Pending Tasks\n```\n- T1 | fenced\n````\n- T2 | real | open\n"
        lines, unclosed = self._strip(text)
        self.assertFalse(unclosed)
        self.assertIn("- T2 | real | open", lines)
        self.assertNotIn("- T1 | fenced", lines)

    def test_trailing_whitespace_on_the_closing_fence_still_closes(self):
        """閉じ fence の**末尾空白**で閉じ損ねない。

        `not info.strip()` を `not info` に狭めると、末尾に空白 1 つあるだけで
        閉じ扱いにならず恒久 block になる。末尾空白は LLM が書く markdown で
        普通に混入する形（done guard の行頭要求で踏んだのと同じ型）。
        """
        text = "## Pending Tasks\n```\n- T1 | fenced\n``` \n- T2 | real | open\n"
        lines, unclosed = self._strip(text)
        self.assertFalse(unclosed)
        self.assertIn("- T2 | real | open", lines)

    def test_unclosed_fence_is_reported(self):
        lines, unclosed = self._strip("## A\n```python\n- T1 | x\n")
        self.assertTrue(unclosed)
        self.assertNotIn("- T1 | x", lines)


class StripFencedLinesMarkedTests(unittest.TestCase):
    """`strip_fenced_lines_marked()` の 4 値 API を固定する（AC-7 secondary、T-2）。

    design.md D4 が正本。`strip_fenced_lines()` はこの API への薄いラッパへ
    置き換わる（判定ロジックは不変、戻り値の粒度だけが増える）。
    """

    def test_strip_fenced_lines_marked_returns_all_closed_fence_starts_in_a_gap(self):
        text = "\n".join([
            "## Verification", "```", "- V-01 | unit_test | pending | - | -", "```",
            "```", "- V-02 | unit_test | pending | - | -", "```", "## Next",
        ])
        kept, unclosed, fence_before, fenced_heading_lines = _mod.strip_fenced_lines_marked(text)
        self.assertFalse(unclosed)
        self.assertEqual(kept, ["## Verification", "## Next"])
        self.assertEqual(len(fence_before[1]), 2)
        self.assertEqual(fenced_heading_lines, [])

    def test_strip_fenced_lines_marked_lists_all_fenced_verification_headings(self):
        text = "\n".join([
            "#### Steps", "```", "## Verification", "```", "本文",
            "```", "## Verification", "```",
        ])
        kept, unclosed, fence_before, fenced_heading_lines = _mod.strip_fenced_lines_marked(text)
        self.assertFalse(unclosed)
        self.assertEqual(fenced_heading_lines, [2, 6])

    def test_fenced_heading_match_is_exact_not_prefix(self):
        """AC-1 (f) / design.md D4: 判定は `rstrip() == "## Verification"` の exact match。

        `startswith` にすると design § 1.5 の carve-out（`## Verification Notes` /
        `## Verification History`）を記入例 fence に 1 行含むだけで恒久 block になる。
        接頭一致する別見出しは `fenced_heading` 違反に計上しない。
        """
        text = "\n".join([
            "#### Steps", "```",
            "## Verification Notes",
            "## Verification History",
            "## VerificationX",
            "## Verification の例:",
            "```", "本文",
        ])
        _kept, unclosed, _fence_before, fenced_heading_lines = _mod.strip_fenced_lines_marked(text)
        self.assertFalse(unclosed)
        self.assertEqual(fenced_heading_lines, [])

    def test_fenced_heading_match_tolerates_trailing_whitespace_only(self):
        """`rstrip()` 後の exact match なので行末空白は許容し、行頭インデントは許容しない。"""
        text = "\n".join([
            "#### Steps", "```", "## Verification   ", "  ## Verification", "```",
        ])
        _kept, unclosed, _fence_before, fenced_heading_lines = _mod.strip_fenced_lines_marked(text)
        self.assertFalse(unclosed)
        self.assertEqual(fenced_heading_lines, [2])


if __name__ == "__main__":
    unittest.main()

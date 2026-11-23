"""done guard が tasklist.md の fenced code block をどう読むかの契約テスト（bind 済み worktree）。

fence の中の行を未完了タスクや検証行に数えないこと、fence の壊れ方ごとの扱い、
`## Verification` 節の fence を固定する。`test_stop_hook_bind_resolution_contract.py`
から分けた。fixture は `_stop_hook_test_base` の 2 worktree fixture を使う。

実行:
  python3 -m pytest plugins/gate-driven-development/tests/test_stop_hook_tasklist_fence_contract.py -q
  python3 -m unittest tests.test_stop_hook_tasklist_fence_contract
"""
from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

# `python3 -m unittest tests.<module>` でも共有ヘルパを解決できるようにする
# （pytest は tests/ を自動で path に入れるが unittest は入れない）。
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _stop_hook_test_base import (  # noqa: E402
    _bind,
    _make_two_worktree_fixture,
    _stop_done,
)


class FencedCodeBlockTests(unittest.TestCase):
    """tasklist.md の fenced code block 内の行を未完了タスクに数えない。

    実データで踏んだ: **Pending Tasks 配下のタスクの `#### Steps`** に貼った計画コード
    （fence の中の `- T1 | ... | still open` 等）が未完了タスクとして数えられ、
    実タスクを全部終えても phantom タスクが残って**恒久的に block する**。

    fixture は必ず `## Pending Tasks` / `## Current Task` 配下に fence を置く
    ―― `## Completed Tasks` 配下だと section 判定の時点で除外されるので、
    **fence 除外を外しても結果が変わらず pin が空虚になる**（実測で確認した）。
    """

    _WITH_FENCE = textwrap.dedent(
        """\
        # Tasklist
        ## Current Task
        - なし

        ## Pending Tasks

        ### Task: T-9 実装

        #### Steps

        1. RED を書く
           - Code:
             ```python
             TASKLIST = (
                 "## Current Task\\n"
                 "- T1 | AC-01 | still open\\n"
             )
             ```
           - 期待される未完了行:
             ```
             ### Task: T-99 計画コード内の文字列
             - T2 | AC-02 | これも文字列
             ```

        ## Completed Tasks
        - なし

        ## Verification
        - V-01 | unit_test | pass | npm test 通過 | -

        ## Status
        Next Action=done
        """
    )

    def _block_output(self, wtB: Path, tasklist: str) -> str:
        (wtB / ".steering" / "20260822-target" / "tasklist.md").write_text(
            tasklist, encoding="utf-8"
        )
        _bind(wtB)
        _code, out, err = _stop_done(wtB)
        self.assertIn('"decision": "block"', out, f"out={out}\nerr={err}")
        return out

    def test_task_like_lines_inside_fences_are_not_counted(self):
        """fence 内の 3 行を数えず、実タスク 1 件だけを挙げる。

        **件数まで assert する** ―― `block されたか` だけだと、fence 内の行を
        数えていても実タスクがある限り緑になる（＝何も測っていない）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = _make_two_worktree_fixture(Path(tmp))
            out = self._block_output(wtB, self._WITH_FENCE)
            self.assertIn("未完了タスクが 1 件残っています", out)
            self.assertIn("T-9 実装", out)
            for phantom in ("T-99", "T1 | AC-01 | still open", "T2 | AC-02"):
                self.assertNotIn(phantom, out, f"fence 内の行を数えている: {phantom}")

    def test_all_tasks_done_with_fenced_examples_allows_done(self):
        """fence 内に task 形の行が残っていても、実タスクが全部完了なら done を通す。

        これが実データで踏んだ形そのもの（全タスク完了後も恒久 block）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = _make_two_worktree_fixture(Path(tmp))
            all_done = self._WITH_FENCE.replace(
                "## Pending Tasks\n\n### Task: T-9 実装", "## Pending Tasks\n\n### Done: T-9 実装"
            )
            (wtB / ".steering" / "20260822-target" / "tasklist.md").write_text(
                all_done, encoding="utf-8"
            )
            _bind(wtB)
            _code, out, err = _stop_done(wtB)
            self.assertNotIn(
                "未完了タスクが", out, f"fence 内の行が未完了タスクに数えられている\nout={out}"
            )

    def test_fence_handling_does_not_hide_real_tasks(self):
        """positive control: fence の**外**の未完了タスクは従来どおり block する。

        これが無いと「fence 対応 = 全部無視」の実装でも緑になる。
        """
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = _make_two_worktree_fixture(Path(tmp))
            mixed = self._WITH_FENCE.replace(
                "## Current Task\n- なし", "## Current Task\n- T1 | AC-01 | still open"
            )
            out = self._block_output(wtB, mixed)
            self.assertIn(str(wtB / ".steering" / "20260822-target"), out)
            self.assertIn("T1 | AC-01 | still open", out)
            self.assertIn("未完了タスクが 2 件残っています", out)
            self.assertNotIn("T-99", out)


class FenceEdgeCaseTests(unittest.TestCase):
    """fence 判定の壊れ方を形ごとに固定する。

    素朴な ``` トグルで実測した壊れ方（いずれも実データに現存する形）:

    - **閉じ忘れ**（``` が奇数）: そこから先を全部読み飛ばし、**実タスクが 1 件も
      数えられず done が通る** = fail-open。guard が無言で無効になる
    - **`~~~` 形式**: トグルに引っかからず中の task 行を計上 → phantom 恒久 block
    - **4 連バッククォートで包んだ ``` 入りブロック**: 内側の ``` で反転して同上
    """

    # 維持: このクラスの全テストは Check 1（Current Task 内の fence 判定）を
    # 主張しており、Verification の内容には依存しない。canonical 全 pass は
    # allow のまま（design.md § 5「不変」）なので canonical 化のみで RED が
    # 解消する（Category A2）。
    _BASE = """# Tasklist
## Current Task
{body}

## Pending Tasks
- なし

## Completed Tasks
- なし

## Verification
| method | status | evidence | notes |
|---|---|---|---|
| method=ac:AC-01 | pass | npm test 通過 | - |

## Status
Next Action=done
"""

    def _run(self, body: str) -> tuple[str, str]:
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = _make_two_worktree_fixture(Path(tmp))
            (wtB / ".steering" / "20260822-target" / "tasklist.md").write_text(
                self._BASE.format(body=body), encoding="utf-8"
            )
            _bind(wtB)
            _code, out, err = _stop_done(wtB)
            return out, err

    def test_unclosed_fence_fails_closed(self):
        """閉じ忘れ fence は **block する**（読み飛ばして done を通さない）。

        判別力: fence を素朴なトグルに戻すと、fence 以降が全部読み飛ばされて
        `- T1 | AC-01 | still open` が数えられず allow になる。
        """
        body = "```python\nx = 1\n- T1 | AC-01 | still open"
        out, err = self._run(body)
        self.assertIn('"decision": "block"', out, f"out={out}\nerr={err}")
        self.assertIn("code fence が閉じていません", out)

    def test_tilde_fence_contents_are_not_counted(self):
        """`~~~` fence の中の task 行を数えない。"""
        body = "- なし\n\n~~~\n- T1 | AC-01 | still open\n### Task: T-99 例\n~~~"
        out, err = self._run(body)
        self.assertNotIn('"decision": "block"', out, f"out={out}\nerr={err}")

    def test_nested_backtick_fence_contents_are_not_counted(self):
        """4 連バッククォートで包んだ ``` 入りブロックの中身を数えない。"""
        body = "- なし\n\n````\n```\n- T1 | AC-01 | still open\n```\n````"
        out, err = self._run(body)
        self.assertNotIn('"decision": "block"', out, f"out={out}\nerr={err}")

    def test_real_tasks_after_a_closed_fence_are_still_counted(self):
        """positive control: 正しく閉じた fence の**後ろ**の実タスクは数える。

        これが無いと「fence を見たら以降を全部無視」の実装でも緑になる。
        """
        body = "```python\nx = 1\n```\n- T1 | AC-01 | still open"
        out, err = self._run(body)
        self.assertIn('"decision": "block"', out, f"out={out}\nerr={err}")
        self.assertIn("T1 | AC-01 | still open", out)


    def test_a_different_marker_does_not_close_a_fence(self):
        """`` ``` `` で開いた fence を `~~~` では閉じない（記号種別を見る）。

        閉じ判定から記号種別を落とすと `~~~` が閉じ扱いになり、
        その後ろの行を構造として読んでしまう。ここでは**閉じ忘れとして
        fail-closed になる**ことで区別する（block 理由の文言まで assert する
        ―― `block されたか` だけだと変異体も block するので区別できない）。
        """
        body = "- なし\n\n```python\nx = 1\n~~~\n- T1 | AC-01 | still open"
        out, err = self._run(body)
        self.assertIn('"decision": "block"', out, f"out={out}\nerr={err}")
        self.assertIn("code fence が閉じていません", out)
        self.assertNotIn("T1 | AC-01 | still open", out)

    def test_backtick_in_info_string_is_not_a_fence(self):
        """`` ```md`inline` `` のような行は fence ではない（CommonMark）。

        info string に `` ` `` を含む backtick fence は開き fence にならない。
        この判定を外すと、散文がコードブロックの開始とみなされて
        **以降の実タスクが読み飛ばされる**（fail-open）。
        """
        body = "- なし\n\n```md`inline`\n- T1 | AC-01 | still open"
        out, err = self._run(body)
        self.assertIn('"decision": "block"', out, f"out={out}\nerr={err}")
        self.assertIn("T1 | AC-01 | still open", out)
        self.assertNotIn("code fence が閉じていません", out)


class VerificationFenceTests(unittest.TestCase):
    """`## Verification` に**一部でも重なる** fence は schema 違反（AC-7）。

    旧契約は「Check 1 と Check 2 が同じ構造行を見る」対称性を守り、
    片方だけ fence を剥がすと恒久 block が再現することを防いでいた。
    D7（design.md）はこの対称性を Check 2 側でのみ破る決定をした:
    閉じた fence で `pending` を隠せる fail-open（findings F-12）の方が、
    記入例による false block より優先度が高いため。記入例・散文は
    `## Verification Notes` へ移せば fence を自由に使える（§ 1.5）。
    Check 1 側の対称性は変えていない。
    """

    def test_pending_rows_inside_a_fence_do_not_block(self):
        # 反転: D7（design.md）。旧契約は「Check 1 と Check 2 が同じ構造行を見る」
        # 対称性を守るため、閉じた fence の中身を不可視にして allow していた。
        # だがこの対称性そのものが findings F-12 の fail-open（閉じた fence で
        # pending 行を隠せる）を生んでいた。AC-7 は Check 2 側でだけこの対称性を
        # 破り、「節に一部でも重なる fence」を schema 違反にする
        # （design.md § 1.7 / D4 / D7）。したがって本来 block してはいけない
        # という主張はもう成立せず、逆に **block するのが正しい**。
        # 代替導線: 記入例は `## Verification Notes` へ移せば fence を自由に使える
        # （§ 1.5）。Check 1 側の対称性は変えていない。
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = _make_two_worktree_fixture(Path(tmp))
            tasklist = textwrap.dedent(
                """\
                # Tasklist
                ## Current Task
                - なし

                ## Pending Tasks
                - なし

                ## Completed Tasks
                - T1 | AC-01 | done

                ## Verification
                | method | status | evidence | notes |
                |---|---|---|---|
                | method=ac:AC-01 | pass | npm test 通過 | - |

                書き方の例:

                ```
                - V-99 | unit_test | pending | 未実施 | -
                - V-98 | e2e | fail | 落ちた | -
                ```

                ## Status
                Next Action=done
                """
            )
            (wtB / ".steering" / "20260822-target" / "tasklist.md").write_text(
                tasklist, encoding="utf-8"
            )
            _bind(wtB)
            _code, out, err = _stop_done(wtB)
            self.assertIn('"decision": "block"', out, f"out={out}\nerr={err}")
            self.assertIn("fenced code block が重なっています", out, f"out={out}\nerr={err}")

    def test_list_indented_fence_in_verification_does_not_block(self):
        """`#### Steps` と同じ書式（リスト項目の下）の fence も **block する**（D7 反転）。

        旧テスト名・旧docstring「block しない」は AC-7 以前の対称性契約を
        記述したもので、いまは D7 によりこの 1 点で対称性を破っている。
        reviewer が実測した false block（`^ {0,3}` のインデント制限だと
        この fence が認識されず恒久 block する）は、fence 検出そのものの
        バグであって Check 2 の schema 違反化とは無関係。fence が節に重なる
        以上、fence 検出さえ正しく効けば **節から fence を出すまで block し続ける
        のが仕様**（記入例は Notes へ移す）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = _make_two_worktree_fixture(Path(tmp))
            tasklist = textwrap.dedent(
                """\
                # Tasklist
                ## Current Task
                - なし

                ## Pending Tasks
                - なし

                ## Completed Tasks
                - T1 | AC-01 | done

                ## Verification
                | method | status | evidence | notes |
                |---|---|---|---|
                | method=ac:AC-01 | pass | npm test 通過 | - |

                1. 参考:
                   - Code:
                     ```
                     - V-99 | unit_test | fail | 例示 | -
                     ```

                ## Status
                Next Action=done
                """
            )
            (wtB / ".steering" / "20260822-target" / "tasklist.md").write_text(
                tasklist, encoding="utf-8"
            )
            _bind(wtB)
            _code, out, err = _stop_done(wtB)
            self.assertIn('"decision": "block"', out, f"out={out}\nerr={err}")
            self.assertIn("fenced code block が重なっています", out, f"out={out}\nerr={err}")

    def test_indented_verification_rows_are_not_counted_but_are_still_detected(self):
        """インデント行は新文法では**列挙外 = schema 違反**（design.md § 5「インデント行」）。

        旧実装は「未完了の検出は無条件」（旧 ADR 不変条件 1）のため、
        インデント行でも pending/fail セルを持てば検出だけは効いていた
        （計上＝data 行として数えるかどうかとは別軸）。閉じた文法には
        「検出はするが計上しない」という中間状態が無く、列挙（blank /
        `- なし` / header / separator / data_row）に一致しない行はすべて
        `line` 違反になる。
        """
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = _make_two_worktree_fixture(Path(tmp))
            # (a) fence 外のインデント記入例（pending）は **block する**（fail-closed）
            ok = textwrap.dedent(
                """\
                # Tasklist
                ## Current Task
                - なし

                ## Pending Tasks
                - なし

                ## Completed Tasks
                - T1 | AC-01 | done

                ## Verification
                - V-01 | unit_test | pass | npm test 通過 | -

                - 記入例:
                  - V-XX | manual | pending | 記入例 | -

                ## Status
                Next Action=done
                """
            )
            (wtB / ".steering" / "20260822-target" / "tasklist.md").write_text(
                ok, encoding="utf-8"
            )
            _bind(wtB)
            _code, out, err = _stop_done(wtB)
            self.assertIn('"decision": "block"', out, f"out={out}\nerr={err}")
            self.assertIn("V-XX", out)

            # 反転: reason 文字列（design.md § 5「インデント行 | 受理（表は計上）|
            # violation | done→block」に相当する reason 変化）。旧実装は
            # インデントされた list 行を「計上しない」経路に落とし、他に data 行が
            # 無ければ 0 件として「検証行がありません」を出していた。新文法には
            # 「計上しないが黙って無視する」という経路が無く、列挙外の行は
            # 即 `line` 違反になるため、reason は「schema 違反行が N 件あります」
            # に変わる。decision は block のまま（fail-closed という結論は不変）。
            #     `- 記入例:` は行頭なのでそれ自体が data 行に数えられる。
            #     「インデント行しか無い」状態を作るには例示ごとインデントする。
            bad = ok.replace(
                "- V-01 | unit_test | pass | npm test 通過 | -\n\n- 記入例:\n"
                "  - V-XX | manual | pending | 記入例 | -\n",
                "  - V-01 | unit_test | pass | npm test 通過 | -\n",
            )
            self.assertNotIn("\n- V-", bad, "fixture が意図どおり置換されていない")
            (wtB / ".steering" / "20260822-target" / "tasklist.md").write_text(
                bad, encoding="utf-8"
            )
            _code, out, err = _stop_done(wtB)
            self.assertIn('"decision": "block"', out, f"out={out}\nerr={err}")
            self.assertIn("schema 違反行", out, f"out={out}\nerr={err}")

    def test_closed_fence_immediately_before_verification_notes_blocks(self):
        """追加（design.md § 6 fence 契約 2 / D4 右端 inclusive の判別力）。

        閉じ fence の直後に**空行なしで** `## Verification Notes` が来る形。
        D4 の判定式 `range(h+1, e+1)` の右端 `e` を含めないと、この形は
        「節終了直後」に落ちて section_fence として検出できない
        （findings と同型の fail-open。security R1 H-1 が PoC で実測）。
        空行入りの fixture だけでは exclusive 実装でも緑になるため、
        空行なしの形を明示的に固定する。
        """
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = _make_two_worktree_fixture(Path(tmp))
            tasklist = textwrap.dedent(
                """\
                # Tasklist
                ## Current Task
                - なし

                ## Pending Tasks
                - なし

                ## Completed Tasks
                - T1 | AC-01 | done

                ## Verification
                | method | status | evidence | notes |
                |---|---|---|---|
                | method=ac:AC-01 | pass | ok | - |

                ```
                - V-99 | unit_test | pending | 未実施 | -
                ```
                ## Verification Notes
                記入例はここに置く

                ## Status
                Next Action=done
                """
            )
            (wtB / ".steering" / "20260822-target" / "tasklist.md").write_text(
                tasklist, encoding="utf-8"
            )
            _bind(wtB)
            _code, out, err = _stop_done(wtB)
            self.assertIn('"decision": "block"', out, f"out={out}\nerr={err}")
            self.assertIn("fenced code block が重なっています", out, f"out={out}\nerr={err}")

    def test_fence_swallowing_the_heading_blocks_even_with_a_clean_section_left(self):
        """追加（design.md § 6 fence 契約 3 / `fenced_heading_lines` の判別力）。

        fence が `## Verification` 見出し行そのものを飲み、別の（今度は
        canonical で clean な）`## Verification` 節が残る形。`fence_before`
        だけを見る実装だと、飲まれた領域は残存節の走査範囲より手前に落ちて
        検出できず、`verification_section_found` も残存節で真になるため
        ALLOW に倒れる（security R1 H-2 が PoC で実測）。この違反は
        位置非依存で計上されるため、他に clean な節があっても block が
        維持されることを固定する。
        """
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = _make_two_worktree_fixture(Path(tmp))
            tasklist = textwrap.dedent(
                """\
                # Tasklist
                ## Current Task
                - なし

                ## Pending Tasks
                - なし

                ## Completed Tasks
                - T1 | AC-01 | done

                記入例:
                ```
                ## Verification
                - V-01 | unit_test | pending | 未実施 | -
                ```

                ## Verification
                | method | status | evidence | notes |
                |---|---|---|---|
                | method=ac:AC-01 | pass | ok | - |

                ## Status
                Next Action=done
                """
            )
            (wtB / ".steering" / "20260822-target" / "tasklist.md").write_text(
                tasklist, encoding="utf-8"
            )
            _bind(wtB)
            _code, out, err = _stop_done(wtB)
            self.assertIn('"decision": "block"', out, f"out={out}\nerr={err}")
            self.assertIn("見出しがあります", out, f"out={out}\nerr={err}")
            self.assertIn("Notes へ移しても解除されません", out, f"out={out}\nerr={err}")

    def test_fenced_heading_outside_any_verification_section_still_blocks(self):
        """追加（design.md § 6 fence 契約 4 / 位置非依存の判別力）。

        節外（`## Steps` 相当）にある fence の記入例が `## Verification`
        見出しを含む形。`fenced_heading` 違反は文書全域が対象であり、
        節境界の内外を問わないことを固定する。
        """
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = _make_two_worktree_fixture(Path(tmp))
            tasklist = textwrap.dedent(
                """\
                # Tasklist
                ## Current Task
                - なし

                ## Pending Tasks
                - なし

                ## Completed Tasks
                - T1 | AC-01 | done

                ## Verification
                | method | status | evidence | notes |
                |---|---|---|---|
                | method=ac:AC-01 | pass | ok | - |

                ## Steps
                記入例:
                ```
                ## Verification
                - V-99 | unit_test | pending | 未実施 | -
                ```

                ## Status
                Next Action=done
                """
            )
            (wtB / ".steering" / "20260822-target" / "tasklist.md").write_text(
                tasklist, encoding="utf-8"
            )
            _bind(wtB)
            _code, out, err = _stop_done(wtB)
            self.assertIn('"decision": "block"', out, f"out={out}\nerr={err}")
            self.assertIn("見出しがあります", out, f"out={out}\nerr={err}")

    def test_two_fenced_headings_report_both_line_numbers(self):
        """追加（design.md § 6 fence 契約 5）。

        見出し入り記入例 fence が **2 つ**ある形。1 件ずつ提示すると
        「直した → まだ block」を繰り返し、回復手順が効かないように見える
        ため、reason は該当行を全件（両方）列挙する（design.md D4）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = _make_two_worktree_fixture(Path(tmp))
            tasklist = textwrap.dedent(
                """\
                # Tasklist
                ## Current Task
                - なし

                ## Pending Tasks
                - なし

                ## Completed Tasks
                - T1 | AC-01 | done

                ## Verification
                | method | status | evidence | notes |
                |---|---|---|---|
                | method=ac:AC-01 | pass | ok | - |

                ## Steps
                記入例1:
                ```
                ## Verification
                - V-99 | unit_test | pending | 未実施 | -
                ```

                記入例2:
                ```
                ## Verification
                - V-98 | unit_test | fail | 落ちた | -
                ```

                ## Status
                Next Action=done
                """
            )
            (wtB / ".steering" / "20260822-target" / "tasklist.md").write_text(
                tasklist, encoding="utf-8"
            )
            _bind(wtB)
            _code, out, err = _stop_done(wtB)
            self.assertIn('"decision": "block"', out, f"out={out}\nerr={err}")
            self.assertIn("2 件", out, f"out={out}\nerr={err}")
            # 件数だけでは「1 件目しか列挙しない」退行（`行 {starts}` → `行 {starts[:1]}`）を
            # 素通りさせる（件数表示は 2 件のまま残るため）。行番号リストそのものを pin する。
            # メッセージは人間可読の**原文行番号（1 始まり）**で出す（design.md:200 / :498。
            # impl-gate R7 advisory A20 / T-6 carry-in）。`strip_fenced_lines_marked()` の
            # `fenced_heading_lines` 自体は 0 始まり index のままでよい（判定ロジックは不変）が、
            # `gdd_stop_hook.py` の message 層（`_fenced_heading_message()`）が提示直前に
            # +1 して人間可読の行番号へ変換する必要がある。
            heading_lines = [
                i
                for i, line in enumerate(tasklist.splitlines(), start=1)
                if line.strip() == "## Verification"
            ]
            # 1 本目は実データの節、2〜3 本目が fence 内の記入例。fixture が壊れたら先に落とす。
            self.assertEqual(
                len(heading_lines), 3, f"fixture 前提が壊れている: {heading_lines}"
            )
            fenced_starts = heading_lines[1:]
            self.assertIn(
                f"行 {fenced_starts}", out, f"両方の行番号が出ていない\nout={out}\nerr={err}"
            )

    def test_section_fence_message_reports_one_indexed_start_line(self):
        """A23 + impl-gate R7 advisory A20（T-6 carry-in）。

        `section_fence` の block メッセージも `fenced_heading` と同様、
        `strip_fenced_lines_marked()` の**原文 index（0 始まり）**をそのまま
        `開始行 {section_fence_starts}` として出しており、人間可読の行番号
        （エディタ表示・1 始まり）と 1 ずれる。`section_fence` 側にはこれまで
        行番号 pin テストが無かった（impl-gate R7 A23）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = _make_two_worktree_fixture(Path(tmp))
            tasklist = textwrap.dedent(
                """\
                # Tasklist
                ## Current Task
                - なし

                ## Pending Tasks
                - なし

                ## Completed Tasks
                - T1 | AC-01 | done

                ## Verification
                | method | status | evidence | notes |
                |---|---|---|---|
                | method=ac:AC-01 | pass | npm test 通過 | - |

                書き方の例:

                ```
                - V-99 | unit_test | pending | 未実施 | -
                - V-98 | e2e | fail | 落ちた | -
                ```

                ## Status
                Next Action=done
                """
            )
            (wtB / ".steering" / "20260822-target" / "tasklist.md").write_text(
                tasklist, encoding="utf-8"
            )
            _bind(wtB)
            _code, out, err = _stop_done(wtB)
            self.assertIn('"decision": "block"', out, f"out={out}\nerr={err}")
            # fence の開始行（```` ``` ````）を人間可読の 1 始まり行番号で特定する。
            fence_open_line = next(
                i
                for i, line in enumerate(tasklist.splitlines(), start=1)
                if line.strip() == "```"
            )
            self.assertIn(
                f"開始行 [{fence_open_line}]",
                out,
                f"section_fence の開始行が 1 始まりで出ていない\nout={out}\nerr={err}",
            )

    def test_fences_before_and_after_the_section_without_overlap_do_not_block(self):
        """追加（design.md § 6 fence 契約 6 / negative control）。

        節の前・次の `## ` より後にある fence（見出しを含まない）は
        無関係なので block しない。section_fence / fenced_heading の判定が
        誤って文書全体に効いていないことを確認する。
        """
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = _make_two_worktree_fixture(Path(tmp))
            tasklist = textwrap.dedent(
                """\
                # Tasklist
                ## Current Task
                - なし

                ## Pending Tasks
                - なし

                ## Completed Tasks
                - T1 | AC-01 | done

                記入例（節の外側）:
                ```
                - V-00 | unit_test | pending | 未実施 | -
                ```

                ## Verification
                | method | status | evidence | notes |
                |---|---|---|---|
                | method=ac:AC-01 | pass | ok | - |

                ## Status
                Next Action=done

                ```
                - V-01 | unit_test | pending | 節の後ろの記入例 | -
                ```
                """
            )
            (wtB / ".steering" / "20260822-target" / "tasklist.md").write_text(
                tasklist, encoding="utf-8"
            )
            _bind(wtB)
            _code, out, err = _stop_done(wtB)
            self.assertNotIn('"decision": "block"', out, f"out={out}\nerr={err}")

    def test_pending_rows_outside_a_fence_still_block(self):
        """positive control: fence の外の pending 行は従来どおり block する。"""
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = _make_two_worktree_fixture(Path(tmp))
            tasklist = textwrap.dedent(
                """\
                # Tasklist
                ## Current Task
                - なし

                ## Pending Tasks
                - なし

                ## Completed Tasks
                - T1 | AC-01 | done

                ## Verification
                - V-01 | unit_test | pending | 未実施 | -

                ## Status
                Next Action=done
                """
            )
            (wtB / ".steering" / "20260822-target" / "tasklist.md").write_text(
                tasklist, encoding="utf-8"
            )
            _bind(wtB)
            _code, out, err = _stop_done(wtB)
            self.assertIn('"decision": "block"', out, f"out={out}\nerr={err}")
            self.assertIn("V-01", out)


if __name__ == "__main__":
    unittest.main()

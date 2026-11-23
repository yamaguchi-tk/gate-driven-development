"""done guard の Check 3（`Route In Progress`）が `state.md` の正準形を読み、散文を拾わないことの契約。

実行:
  python3 -m pytest plugins/gate-driven-development/tests/test_stop_hook_route_in_progress_canonical_form_contract.py -q
  python3 -m unittest tests.test_stop_hook_route_in_progress_canonical_form_contract

`test_stop_hook_done_guard_regression_contract.py` から分けた。確かめる本体は
`hooks/scripts/gdd_stop_hook.py`（入口）・`hooks/scripts/lib/done_guard.py`（Check 3 の判定）・
`hooks/scripts/lib/tasklist_parse.py`（`Route In Progress` 行の読み取り）。
bind スコープ（2 worktree fixture）での Check 3 は、元のファイルの
`BoundRouteInProgressCheckTests` が測る。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

# `python3 -m unittest tests.<module>` でも共有ヘルパを解決できるようにする
# （pytest は tests/ を自動で path に入れるが unittest は入れない）= 共通規約 13。
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _stop_hook_test_base import (  # noqa: E402
    _CLEAN_TASKLIST,
    _DONE_OUTPUT,
    _make_transcript_jsonl,
    _run_hook,
    _write_state_file,
)


class RouteInProgressCanonicalFormTests(unittest.TestCase):
    """Check 3 は `state.md` の **正準形**を読み、**散文を拾わない**。

    completion-check（2026-08-30）の H-3。出荷実装は `"Route In Progress=" in st_line`
    ―― **等号・行内部分一致・最初の 1 行で break** だった。GDD が書く正準形は
    `- Route In Progress: none`（**コロン**）なので、

    - (a) 正準形は**素通り**する ＝ Check 3 は実運用で一度も効いていなかった
    - (b) 解説文にバッククォート付きで `Route In Progress=none` が現れると**誤 block** する

    契約テストが緑だったのは **fixture 側が非正準の等号形**を使っていたため。
    AC-3 / CT-3 の「Check 3 は従来どおり働く」は実データに対して測れていなかった。
    """

    def _run(self, state_body: str, tasklist_body: str | None = None):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            slug = "20260822-target"
            d = ws / ".steering" / slug
            d.mkdir(parents=True)
            (d / "tasklist.md").write_text(tasklist_body or _CLEAN_TASKLIST, encoding="utf-8")
            (d / "state.md").write_text(state_body, encoding="utf-8")
            _write_state_file(ws, {"active": "true", "session_id": "s", "iteration": "1"})
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(
                transcript,
                assistant_text='<gdd-stop reason="done">\n\n' + _DONE_OUTPUT,
            )
            return _run_hook(ws, transcript, session_id="s")

    def test_canonical_colon_form_is_read(self):
        """`- Route In Progress: <非 none>` で block する（正準形を読む）。"""
        _c, out, err = self._run("- Route In Progress: systematic_debugging\n")
        self.assertIn('"decision": "block"', out, f"out={out}\nerr={err}")
        self.assertIn("systematic_debugging", out)

    def test_canonical_colon_none_does_not_block(self):
        """positive control: 正準形が `none` なら block しない（空洞な assert にしない）。"""
        _c, out, _e = self._run("- Route In Progress: none\n")
        self.assertNotIn('"decision": "block"', out, f"out={out}")

    def test_prose_mentioning_the_field_does_not_block(self):
        """解説文中の `` `Route In Progress=none` `` を値として拾わない。

        本 PR 自身の `state.md` が実際にこの形で**誤 block** されていた。
        """
        body = (
            "- Route In Progress: none\n"
            "- Follow-up Classification (2026-08-25):\n"
            "  - **解消先**: `Route In Progress=none`"
            "（`gdd-requirements-amendment` の 3 番目）\n"
        )
        _c, out, _e = self._run(body)
        self.assertNotIn('"decision": "block"', out, f"out={out}")

    def test_prose_before_the_canonical_line_does_not_silence_the_check(self):
        """**行順序軸**: 行頭形の散文が正準行より **前** にあっても guard は無効化されない。

        completion-check 3 回目の M-1。アンカー化しても
        「最初に match した行で `break`」が残っており、
        `` - `Route In Progress=none` を維持する `` のような**行頭形の散文**が先にあると、
        後続の正準行に到達せず **silent fail-open** する。

        **既存 test（`test_prose_mentioning_the_field_does_not_block`）は正準行を先頭に
        置いているのでこの軸を測れていなかった** —— 4 形を pin したと言いながら、
        **単独で置いた場合しか測っていなかった**。
        """
        body = (
            "- `Route In Progress=none` を維持する（解説）\n"
            "- Route In Progress: systematic_debugging\n"
        )
        _c, out, _e = self._run(body)
        self.assertIn('"decision": "block"', out, f"out={out}")
        self.assertIn("systematic_debugging", out)

    def test_fenced_example_is_not_read_as_a_value(self):
        """**fence 軸**: `state.md` の code block 内の例を値として拾わない。

        completion-check 3 回目の M-2。**H-3 の是正が新規に作った誤 block 面**。
        旧実装はコロン形に `=` が無いため素通りしていたが、アンカー化で読むようになった結果、
        **解説用の例が恒久 block の根拠**になった。

        Check 1 / Check 2 は `strip_fenced_lines()` で fence を剥がしており、
        実装コメント自身が「**片方だけ剥がすと同じ恒久 block がもう片方で再現する**」と
        書いている。Check 3 に同じ処理が掛かっていなかった。
        """
        # **fence を正準行より後ろに置く**。実装は **last-wins**（最後に書かれた正準行を採る）
        # なので、前に置くと後続の `none` が必ず勝ち、**fence を剥がしても剥がさなくても
        # 結果が変わらない**（＝空洞な assert）。
        #
        # **当初この推論を逆向きに書いていた**（「後ろに置くと先着の none が勝つ」）——
        # first-wins を前提にした説明で、独立最終レビュー 2026-08-31 の **M-1** で是正した。
        # **「実測で確認した」と書いた記録そのものが誤っていた**。
        body = (
            "- Route In Progress: none\n"
            "```\n- Route In Progress: T-99\n```\n"
        )
        _c, out, _e = self._run(body)
        self.assertNotIn('"decision": "block"', out, f"out={out}")

    def test_pipe_tail_annotation_is_not_part_of_the_value(self):
        """`none | reason: ... | updated_by: ...` は **GDD の正準書式そのもの**。

        completion-check の指摘。**実データで block したものの中に、
        値が実質 `none` のものがあった**。block メッセージは「`Route In Progress: none` にする」と
        指示するが、**既に `none` と書いてあるので従っても解除できない**
        —— bind 限定で塞いだ「自分の worktree を直しても解除できない block」と同型。

        `run-session-start-hook.sh` は同じ種類の値に `gdd_value_head`（lib/detect-steering.sh）を通しており、
        **同一プラグイン内で同じ field の読み方が食い違っていた**。
        """
        _c, out, _e = self._run(
            "- Route In Progress: none | reason: design-gating 通過 | updated_by: gdd-design-gating\n"
        )
        self.assertNotIn('"decision": "block"', out, f"out={out}")

    def test_parenthetical_annotation_is_not_part_of_the_value(self):
        """`none（2026-08-21 / 人間による解除で…）` も実質 `none`（実データにある形）。"""
        _c, out, _e = self._run(
            "- Route In Progress: none（2026-08-21 / **人間による解除**で T-30 を approved とした）\n"
        )
        self.assertNotIn('"decision": "block"', out, f"out={out}")

    def test_the_last_canonical_line_wins(self):
        """正準行が複数あるときは **最後に書かれた値**を採る（実データにある形）。

        先頭採用だと、解除を追記した `none` が無視されて**解除不能な block** になる。
        """
        body = (
            "- Route In Progress: human_recheck_required\n"
            "- Route In Progress: none\n"
        )
        _c, out, _e = self._run(body)
        self.assertNotIn('"decision": "block"', out, f"out={out}")

    def test_a_real_route_still_blocks_with_annotation(self):
        """negative control: 注記があっても**値が非 none なら block**する（空洞にしない）。"""
        _c, out, _e = self._run(
            "- Route In Progress: implementation_fix_only | reason: T-27 の remediation 中\n"
        )
        self.assertIn('"decision": "block"', out, f"out={out}")
        self.assertIn("implementation_fix_only", out)

    def test_unclosed_fence_does_not_silence_the_check(self):
        """fence 閉じ忘れで Check 3 が**無言で skip** しない。

        completion-check 4 回目の H-2(b)。M-2 の是正が `strip_fenced_lines()` の
        第 2 戻り値 `_unclosed` を**捨てていた**。tasklist 側は同じ条件を fail-closed に
        しているのに、`state.md` 側だけ黙って読み飛ばす形になっていた。
        今の実装（`done_guard._route_in_progress_errors`）は、閉じ忘れのときは値を読まずに
        一律で block する（tasklist.md 側と同じ）。
        この test の入力は値が non-none なので、一律 block かどうかは判別しない。一律 block そのものは
        `test_done_guard_state_line_break_chars_contract.py` の
        `test_unclosed_fence_blocks_even_when_route_is_none` が測る。
        """
        body = "```\n- Route In Progress: systematic_debugging\n"  # fence を閉じない
        _c, out, _e = self._run(body)
        self.assertIn('"decision": "block"', out, f"out={out}")

    def test_none_prefixed_route_names_are_not_collapsed_to_none(self):
        """**逆方向の穴**: `none` で始まる別の enum を `none` に潰さない。

        値正規化（H-1 の是正）は「注記を落とす」方向だが、**やりすぎると
        block すべきものを通す**。`nonexistent_route` / `none_but_blocked` が
        `none` に潰れると guard が黙って無効化される。

        実装は**識別子の最長一致**（`[A-Za-z_][A-Za-z0-9_-]*`）を採るのでここは安全だが、
        「先頭 4 文字が `none` なら none」のような実装に**退行させない**ために pin する。
        """
        for val in ("nonexistent_route", "none_but_actually_blocked"):
            with self.subTest(val=val):
                _c, out, _e = self._run(f"- Route In Progress: {val}\n")
                self.assertIn('"decision": "block"', out, f"val={val} out={out}")
                self.assertIn(val, out)

    def test_decorated_none_is_not_blocked(self):
        """装飾を剥がした結果が `none` なら block しない（`**none**` / `"none"`）。"""
        for val in ("**none**", '"none"', "`none`"):
            with self.subTest(val=val):
                _c, out, _e = self._run(f"- Route In Progress: {val}\n")
                self.assertNotIn('"decision": "block"', out, f"val={val} out={out}")

    def test_none_is_matched_case_insensitively(self):
        """`None` / `NONE` も `none` として扱う（completion-check 5 回目の H5-7）。

        field 名の照合は `re.IGNORECASE` なのに値比較だけ厳密で**非対称**だった。
        解除は可能なので実害は小さいが、**本 PR の主題は誤 block の除去**なので揃える。
        """
        for val in ("None", "NONE", "NoNe"):
            with self.subTest(val=val):
                _c, out, _e = self._run(f"- Route In Progress: {val}\n")
                self.assertNotIn('"decision": "block"', out, f"val={val} out={out}")

    def test_decorated_non_none_route_still_blocks(self):
        """**装飾された非 none の route は block する**（fail-open を非 none 側へ広げない）。

        completion-check 5 回目の **H5-1**。値正規化（H-1 の是正）が
        「**enum として読めない値は行ごと skip**」という形になっており、
        `**systematic_debugging**` / `実装修正中` / `"systematic_debugging"` が
        **すべて block されなくなっていた** —— 親実装（`7a46420`）では block していた
        ＝ **判別力の後退**。

        **こちらの「逆方向の検証」は述語を外していた**: 測ったのは
        「`none` に潰れるか」だったが、実際の fail-open チャネルは
        「**値として採らず `chosen` が空になる**」という別経路だった。
        実データで、当時の `_route_value`（今の `tasklist_parse.route_value` の前身。H5-1 の是正前は、
        enum として読めない値に空を返していた）が空を返す行は無かったので、
        **実測は無情報**（この軸を一度も踏んでいない）。

        `**none**` を誤 block しないための fail-open は**装飾を剥がした結果が `none` のときだけ**に限る。
        `**systematic_debugging**` は**自分の worktree の自分のファイル**で、
        block メッセージの指示どおり書き換えれば解除できる ＝ bind 限定で塞いだ「自分では直せない block」とは別種。
        """
        for val in ("**systematic_debugging**", "実装修正中", '"systematic_debugging"'):
            with self.subTest(val=val):
                _c, out, _e = self._run(f"- Route In Progress: {val}\n")
                self.assertIn('"decision": "block"', out, f"val={val} out={out}")

    def test_legacy_equals_form_is_still_read(self):
        """後方互換: 旧記録の `Route In Progress=<非 none>` も読む。"""
        _c, out, _e = self._run("- `Route In Progress=systematic_debugging`\n")
        self.assertIn('"decision": "block"', out, f"out={out}")


if __name__ == "__main__":
    unittest.main()

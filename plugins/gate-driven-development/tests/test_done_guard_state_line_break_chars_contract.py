"""done guard（Stop hook）が LF / CR 以外の行区切り文字を含む state.md を block する契約（Issue #119 / D-28）。

`select_route_in_progress()` は `strip_fenced_blocks()` → `str.splitlines()` 経由で state.md を
読むため、行区切り文字を含む state.md は行が誤分割され、`Route In Progress` の値が空文字列に
化けて Check 3 を素通りしていた（tasklist.md 側は `test_done_guard_line_break_chars_contract.py`
で既に block している。対の片方だけが直っていた）。state.md 全文に対して
`_line_break_char_error(text, "state.md")` を Check 3 の入口で走らせ、block したら
`select_route_in_progress()` へ進まない（fail-closed）。
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks" / "scripts"))

from _plugin_module_loader import load_plugin_module  # noqa: E402
from _stop_hook_test_base import (  # noqa: E402
    _bind,
    _make_transcript_jsonl,
    _run_hook,
    _stop_done,
    _write_state_file,
    _write_steering,
)

_handoff_summary = load_plugin_module("hooks/scripts/lib/handoff_summary.py")

_SLUG = "20260911-state-line-break-chars"
_HINTS_SEPARATOR = "--- 推奨アクション ---"
# 生の不可視文字はソースに埋めない。U+2028 / U+2029 も他の 6 種と同じエスケープ表記で書く
_LINE_BREAK_CHARS = ("\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029")

_CLEAN_TASKLIST = (
    "# Tasklist\n\n"
    "## Current Task\n- なし\n\n"
    "## Pending Tasks\n- なし\n\n"
    "## Completed Tasks\n- T1 | AC-01 | done\n\n"
    "## Verification\n\n"
    "| method | status | evidence | notes |\n"
    "|---|---|---|---|\n"
    "| method=ac:AC-01 | pass | npm test 通過 | - |\n\n"
    "## Status\nNext Action=done\n"
)


def _state(body: str) -> str:
    return f"# State\n{body}\n"


def _run(state_text: str) -> tuple[int, str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp)
        _write_steering(ws, _SLUG, _CLEAN_TASKLIST, state_content=state_text)
        _bind(ws, _SLUG)
        return _stop_done(ws)


class StateLineBreakCharsBlockTests(unittest.TestCase):
    def _reason(self, state_text: str) -> str:
        code, out, err = _run(state_text)
        self.assertNotEqual(out.strip(), "", f"allow になっている: err={err}")
        payload = json.loads(out.strip())
        self.assertEqual(payload["decision"], "block", f"out={out}\nerr={err}")
        return payload["reason"]

    def test_each_char_in_state_md_blocks(self):
        for ch in _LINE_BREAK_CHARS:
            with self.subTest(char=f"U+{ord(ch):04X}"):
                row = f"- Route In Progress: none{ch}x"
                text = _state(row)
                # 原文行番号は 1 始まり。`_state()` の 1 行目は `# State`
                line_no = text.split("\n").index(row) + 1
                reason = self._reason(text)
                self.assertIn("state.md", reason)
                self.assertIn("行区切り文字", reason)
                self.assertIn(f"U+{ord(ch):04X}", reason)
                # 見えない文字なので原文行番号を示す。`_line_break_char_error()` は tasklist.md と
                # 共有だが、共有関数の退行を state.md 側のテストでも検出できるようにしておく
                self.assertIn(f"行 [{line_no}]", reason)
                self.assertNotIn(ch, reason)

    def test_route_in_progress_split_by_u2028_reproduction_blocks(self):
        # D-28 の再現入力そのもの: 値の直前に U+2028 を挟むと現行実装は allow になる
        reason = self._reason(_state("- Route In Progress: \u2028systematic_debugging"))
        self.assertIn("state.md", reason)
        self.assertIn("U+2028", reason)

    def test_char_inside_fence_still_blocks(self):
        # state.md は全文検査（fence の中も救済しない）
        reason = self._reason(_state("```\n- Route In Progress: none\u2028x\n```"))
        self.assertIn("state.md", reason)
        self.assertIn("U+2028", reason)

    def test_no_hint_crosstalk(self):
        reason = self._reason(_state("- Route In Progress: none\u2028x"))
        cause, _, hints = reason.partition(_HINTS_SEPARATOR)
        self.assertNotIn("未完了タスク", cause + hints)
        self.assertNotIn("Route In Progress=", cause + hints)
        self.assertNotIn("Verification", cause + hints)

    def test_reason_does_not_disclose_check3_bypass_result(self):
        """block 理由が Check 3 の迂回手順の開示にならないことを固定する（文言の好みではない）。

        state.md 側の block 理由が「LF に置き換えると空として読まれます」（= Check 3 の non-none
        判定を素通りさせる**結果**）まで書くと、guard の出力そのものが実働する迂回手順の開示になる
        （tasklist.md 側の同型文言は後段の「検証行がありません」で block されるため非対称）。
        正のピンは差し替えた回復手順の一部、負のピンは「空として読まれる」という開示の不在。
        """
        reason = self._reason(_state("- Route In Progress: none\u2028x"))
        self.assertIn("置き換えずに該当文字だけを削除", reason)
        self.assertNotIn("空として読", reason)


class StateLineBreakFailOpenTests(unittest.TestCase):
    """L1+ 安全策 2 の fail-open 3 ケース。"""

    def _payload(self, ws: Path) -> dict:
        code, out, err = _stop_done(ws)
        self.assertNotEqual(out.strip(), "", f"allow になっている: err={err}")
        payload = json.loads(out.strip())
        self.assertEqual(payload["decision"], "block", f"out={out}\nerr={err}")
        return payload

    def test_block_expected_input_is_not_allowed(self):
        # (1) block すべき入力が allow になる: 値の直前の U+2028 で non-none の route が空に化ける
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_steering(
                ws, _SLUG, _CLEAN_TASKLIST,
                state_content=_state("- Route In Progress: \u2028implementation_fix_only"),
            )
            _bind(ws, _SLUG)
            self.assertIn("U+2028", self._payload(ws)["reason"])

    def test_undecodable_state_md_blocks_instead_of_crashing_open(self):
        # (2) 例外で guard 全体が落ちる: UTF-8 で読めない state.md でも allow にしない
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            steering = _write_steering(ws, _SLUG, _CLEAN_TASKLIST, state_content="")
            (steering / "state.md").write_bytes(b"- Route In Progress: \xff\xfe\n")
            _bind(ws, _SLUG)
            self._payload(ws)

    def test_later_none_joined_by_line_break_char_does_not_win(self):
        # (3) 判定できないときに通る: U+2028 で 1 行に繋がった後ろの `none` が現在値に採られて通る形
        reason = self._reason_of(
            _state("- Route In Progress: systematic_debugging\u2028- Route In Progress: none")
        )
        self.assertIn("state.md", reason)
        self.assertIn("U+2028", reason)

    def _reason_of(self, state_text: str) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_steering(ws, _SLUG, _CLEAN_TASKLIST, state_content=state_text)
            _bind(ws, _SLUG)
            return self._payload(ws)["reason"]


class RouteValueUnreadableBlocksTests(unittest.TestCase):
    """独立-1 A1: `Route In Progress` のキー行があるのに値が読めないときも block する。

    8 文字の検査だけでは、その下にある「値が読めなければ route なしとして通す」既定が残る。
    行の途中の単独 CR（`read_text` の universal newlines が LF に変える）、報告された文字の
    LF への置き換え、値が次の行にある形、注記だけの行は、どれも non-none の route を抱えた
    まま done が通っていた。キーの側を壊す形（ZWSP・全角コロンなど）はキー行として認識
    されないので、ここでは閉じない（既知の限界）。
    """

    def _block_reason(self, raw: bytes) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            steering = _write_steering(ws, _SLUG, _CLEAN_TASKLIST, state_content="")
            (steering / "state.md").write_bytes(raw)
            _bind(ws, _SLUG)
            code, out, err = _stop_done(ws)
        self.assertNotEqual(out.strip(), "", f"allow になっている: err={err}")
        payload = json.loads(out.strip())
        self.assertEqual(payload["decision"], "block", f"out={out}\nerr={err}")
        return payload["reason"]

    def test_unreadable_value_shapes_block(self):
        shapes = {
            "lone_cr": b"# State\n- Route In Progress: \rsystematic_debugging\n",
            "replaced_by_lf": b"# State\n- Route In Progress: \nsystematic_debugging\n",
            "value_on_next_line": b"# State\n- Route In Progress:\n  systematic_debugging\n",
            "note_only": b"# State\n- Route In Progress: | reason: x\n",
            "legacy_equals_empty": b"# State\n- `Route In Progress=`\n",
        }
        for name, raw in shapes.items():
            with self.subTest(shape=name):
                reason = self._block_reason(raw)
                self.assertIn("Route In Progress", reason)
                self.assertIn("値を読めない", reason)

    def test_later_readable_line_still_decides(self):
        # 値の無い行の後に値のある行があれば、従来どおりその値で判定する（none → allow）
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_steering(
                ws, _SLUG, _CLEAN_TASKLIST,
                state_content=_state("- Route In Progress:\n- Route In Progress: none"),
            )
            _bind(ws, _SLUG)
            code, out, err = _stop_done(ws)
        self.assertEqual(out.strip(), "", f"block されている: out={out}\nerr={err}")

    def test_state_without_route_key_line_blocks(self):
        # 方針メモ-1（ユーザー決定）: Route In Progress は Tier 1 必須 field。正準のキー行が
        # 1 本も無い state.md は、崩れた形を見分けずに block する（既定の反転。独立-2 B3）
        reason = self._block_reason(b"# State\n- Resume From: x\n")
        self.assertIn("Route In Progress の行がありません", reason)

    def test_key_line_inside_fence_is_not_counted(self):
        # fence の中の記入例はキー行として数えない（reader と同じく fence を剥がして見る）
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_steering(
                ws, _SLUG, _CLEAN_TASKLIST,
                state_content=_state("```\n- Route In Progress:\n```\n- Route In Progress: none"),
            )
            _bind(ws, _SLUG)
            code, out, err = _stop_done(ws)
        self.assertEqual(out.strip(), "", f"block されている: out={out}\nerr={err}")


class RouteKeyLineFailOpenTests(unittest.TestCase):
    """独立-2 B1〜B3、B5: キー行の受理集合と、現在値を決める最後のキー行。

    - B1: 前にある読める行（`none`）が、後ろの読めない行を隠して done が通っていた
    - B2: write guard（`state_fields.has_state_field_line`）が field と認める形を、done guard が
      キー行と見ずに素通りしていた
    - B3: キーの側が崩れた形は、正準のキー行が無いものとして block する（崩れ方は列挙しない）
    - B5: これらの block に、tasklist.md を直せという既定の推奨アクションを付けない
    """

    def _run_raw(self, raw: bytes) -> tuple[int, str, str]:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            steering = _write_steering(ws, _SLUG, _CLEAN_TASKLIST, state_content="")
            (steering / "state.md").write_bytes(raw)
            _bind(ws, _SLUG)
            return _stop_done(ws)

    def _block_reason(self, raw: bytes) -> str:
        code, out, err = self._run_raw(raw)
        self.assertNotEqual(out.strip(), "", f"allow になっている: err={err}")
        payload = json.loads(out.strip())
        self.assertEqual(payload["decision"], "block", f"out={out}\nerr={err}")
        return payload["reason"]

    def test_readable_none_before_unreadable_last_line_blocks(self):
        shapes = {
            "value_on_next_line": b"# State\n- Route In Progress: none\n- Route In Progress:\n  implementation_fix_only\n",
            "note_only": b"# State\n- Route In Progress: none\n- Route In Progress: | reason: x\n",
            "lone_cr": b"# State\n- Route In Progress: none\n- Route In Progress: \rimplementation_fix_only\n",
            "legacy_none_first": b"# State\n- `Route In Progress=none`\n- Route In Progress:\n  implementation_fix_only\n",
        }
        for name, raw in shapes.items():
            with self.subTest(shape=name):
                self.assertIn("値を読めない", self._block_reason(raw))

    def test_write_guard_field_shapes_are_key_lines(self):
        shapes = {
            "space_before_colon": b"# State\n- Route In Progress : implementation_fix_only\n",
            "backticked_key": b"# State\n- `Route In Progress`: implementation_fix_only\n",
            "double_backticks": b"# State\n- ``Route In Progress``: implementation_fix_only\n",
        }
        for name, raw in shapes.items():
            with self.subTest(shape=name):
                reason = self._block_reason(raw)
                self.assertNotIn("Route In Progress の行がありません", reason)

    def test_broken_key_shapes_block(self):
        shapes = {
            "fullwidth_colon": "- Route In Progress\uff1aimplementation_fix_only",
            "indented": "  - Route In Progress: implementation_fix_only",
            "bold": "- **Route In Progress**: implementation_fix_only",
            "star_bullet": "* Route In Progress: implementation_fix_only",
            "zwsp_in_key": "- Route\u200b In Progress: implementation_fix_only",
            "nbsp_in_key": "- Route\u00a0In Progress: implementation_fix_only",
            "leading_bom": "\ufeff- Route In Progress: implementation_fix_only",
        }
        for name, line in shapes.items():
            with self.subTest(shape=name):
                raw = (line + "\n").encode("utf-8") if name == "leading_bom" else f"# State\n{line}\n".encode("utf-8")
                self.assertIn("Route In Progress の行がありません", self._block_reason(raw))

    def test_done_guard_key_lines_cover_write_guard_field_lines(self):
        # 受理集合の対称性: write guard が field ありと見る行は、done guard もキー行と見る
        # `state_fields.py` は同 lib の `tasklist_parse` を top-level module として読む
        # （正本: tests/test_state_field_value_less_line_contract.py の同名ブロック）
        lib_dir = str(Path(__file__).resolve().parents[1] / "hooks" / "scripts" / "lib")
        sys.path.insert(0, lib_dir)
        try:
            state_fields = load_plugin_module("hooks/scripts/lib/state_fields.py")
        finally:
            if lib_dir in sys.path:
                sys.path.remove(lib_dir)
        lines = [
            "- Route In Progress: none", "Route In Progress: none", "Route In Progress=none",
            "- `Route In Progress=none`", "- Route In Progress : none", "- `Route In Progress`: none",
            "- ``Route In Progress``: none", "- Route In Progress:", "- Route In Progress= x",
            "- route in progress: none", "  - Route In Progress: none", "* Route In Progress: none",
            "- Route In Progress\uff1anone", "- **Route In Progress**: none", "Route In Progress none",
        ]
        tasklist_parse = load_plugin_module("hooks/scripts/lib/tasklist_parse.py")
        for line in lines:
            with self.subTest(line=line):
                text = f"# State\n{line}\n"
                if state_fields.has_state_field_line(text, "Route In Progress"):
                    self.assertTrue(tasklist_parse.route_in_progress_key_lines(text))

    def test_route_block_hint_points_to_state_md_not_tasklist(self):
        for raw in (b"# State\n- Resume From: x\n", b"# State\n- Route In Progress: | reason: x\n"):
            with self.subTest(raw=raw):
                reason = self._block_reason(raw)
                _cause, _, hints = reason.partition(_HINTS_SEPARATOR)
                self.assertIn("- Route In Progress:", hints)
                self.assertNotIn("tasklist.md の全タスクを完了し", hints)


class HandoffSummaryDoesNotExpandEscapesTests(unittest.TestCase):
    """独立-2 B4: `apply_summary()` は要約中のバックスラッシュ列を置換テンプレートとして解釈しない。

    文字列の置換だと、要約に書いた 2 文字の `\\n` が state.md の本物の改行になり、同じ Stop の
    中で Check 3 の直前に `Route In Progress: none` の行を足せた。`\\f` / `\\v` は行区切り文字
    になり、hook 自身の書き込みで done が止まっていた。
    """

    def test_backslash_sequences_stay_literal(self):
        content = "# State\n- Route In Progress: implementation_fix_only\nLast Handoff Summary=old\n"
        for encoded in ("x\\nRoute In Progress: none", "a\\fb\\vc\\013d", "\\g<0>\\1"):
            with self.subTest(encoded=encoded):
                result = _handoff_summary.apply_summary(content, encoded)
                self.assertIn(f"Last Handoff Summary={encoded}\n", result)
                self.assertEqual(result.count("\n"), content.count("\n"))
                self.assertFalse(any(ch in result for ch in _LINE_BREAK_CHARS))


class MixedSeparatorAndUnclosedFenceTests(unittest.TestCase):
    """独立-3 D1・D4: 最後のキー行と reader の値が食い違う形、state.md の未閉 fence。

    - D1: コロン形の `none` の後に等号形の route を書くと、reader（コロン形優先）が `none` を
      採って done が通っていた。最後のキー行の値と reader の値のどちらかが non-none なら block
    - D4: 未閉 fence の中の記入例 `none` が現在値に採られて done が通っていた。tasklist.md と
      同じく、state.md の未閉 fence は一律に block する
    """

    _run_raw = RouteKeyLineFailOpenTests._run_raw

    _block_reason = RouteKeyLineFailOpenTests._block_reason

    def test_colon_none_then_equals_route_blocks(self):
        reason = self._block_reason(
            b"# State\n- Route In Progress: none\n- Route In Progress=implementation_fix_only\n"
        )
        self.assertIn("Route In Progress=implementation_fix_only", reason)

    def test_unclosed_fence_with_example_none_blocks(self):
        reason = self._block_reason(
            b"# State\n- Route In Progress: implementation_fix_only\n## Notes\n```text\n- Route In Progress: none\n"
        )
        self.assertIn("state.md の code fence が閉じていません", reason)

    def test_unclosed_fence_blocks_even_when_route_is_none(self):
        # 一律 block（未閉 fence の位置やキー行の有無で狭めない）
        reason = self._block_reason(b"# State\n- Route In Progress: none\n```text\nfoo\n")
        self.assertIn("state.md の code fence が閉じていません", reason)

    def test_fence_opened_by_tilde_and_closed_by_backticks_is_unclosed(self):
        # (3) 判定できないときに通る: 記号の違う閉じ fence を閉じたとみなさない
        reason = self._block_reason(
            b"# State\n- Route In Progress: implementation_fix_only\n~~~\n- Route In Progress: none\n```\n"
        )
        self.assertIn("state.md の code fence が閉じていません", reason)

    def test_state_md_with_only_fence_opener_blocks_without_crashing(self):
        # (2) 例外で guard 全体が落ちる: 本文が fence の開きだけでも block で返る
        reason = self._block_reason(b"```\n")
        self.assertIn("state.md の code fence が閉じていません", reason)

    def test_unclosed_fence_hint_points_to_state_md(self):
        reason = self._block_reason(b"# State\n- Route In Progress: none\n```text\nfoo\n")
        _cause, _, hints = reason.partition(_HINTS_SEPARATOR)
        self.assertIn("state.md の code fence", hints)
        self.assertNotIn("tasklist.md の全タスクを完了し", hints)


class HandoffSummaryKeepsLineBreakCharsForCheck3Tests(unittest.TestCase):
    """独立-3 D3: `apply_summary()` の置換は行区切り文字の手前で止まる。

    `Last Handoff Summary=.*` の `.` は U+2028 など 8 文字にも一致するため、同じ物理行にある
    行区切り文字と、その後ろの route 行まで上書きしていた。persist は Check 3 より前に走るので、
    行区切り文字の検査が効かずに done が通っていた。
    """

    def test_replacement_stops_before_each_line_break_char(self):
        for ch in _LINE_BREAK_CHARS:
            with self.subTest(char=f"U+{ord(ch):04X}"):
                content = f"# State\nLast Handoff Summary=old{ch}- Route In Progress: implementation_fix_only\n"
                result = _handoff_summary.apply_summary(content, "new")
                self.assertIn(f"Last Handoff Summary=new{ch}- Route In Progress: implementation_fix_only\n", result)

    def test_persist_then_check3_blocks_from_stop_hook_entry(self):
        # 入口から: persist → Check 3 の実際の順で通す。persist は git worktree の active steering
        # （最初の `Next Action=` が terminal でない tasklist）にだけ書くので、tasklist はコロン形にする
        tasklist = _CLEAN_TASKLIST.replace("Next Action=done", "Next Action: done")
        state = (
            "# State\n- Route In Progress: none\n"
            "Last Handoff Summary=old\u2028- Route In Progress: implementation_fix_only\n"
        )
        output = (
            "全タスク完了しました。\n\n"
            "<!-- Context Handoff: test -->\n**Handoff:** 次の要約\n\n"
            "## 👤 次にすること\nレビューを依頼してください。\n\n"
            '<gdd-stop reason="done">\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=ws, check=True)
            steering = _write_steering(ws, _SLUG, tasklist, state_content=state)
            _bind(ws, _SLUG)
            _write_state_file(ws, {"active": "true", "session_id": "test-session", "iteration": "1"})
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(transcript, assistant_text=output)
            code, out, err = _run_hook(ws, transcript, session_id="test-session")
            written = (steering / "state.md").read_text(encoding="utf-8")
        # persist が走ったこと（要約が書き換わった）を前提として確かめる
        self.assertIn("Last Handoff Summary=**Handoff:** 次の要約", written)
        self.assertNotEqual(out.strip(), "", f"allow になっている: err={err}")
        payload = json.loads(out.strip())
        self.assertEqual(payload["decision"], "block", f"out={out}\nerr={err}")
        self.assertIn("U+2028", payload["reason"])


class StateLineBreakNonRegressionTests(unittest.TestCase):
    def test_clean_state_md_none_allows(self):
        code, out, err = _run(_state("- Route In Progress: none"))
        self.assertEqual(code, 0, f"err={err}")
        self.assertEqual(out.strip(), "", f"block されている: out={out}\nerr={err}")

    def test_clean_state_md_non_none_blocks_with_original_reason(self):
        code, out, err = _run(_state("- Route In Progress: systematic_debugging"))
        payload = json.loads(out.strip())
        self.assertEqual(payload["decision"], "block")
        self.assertIn("Route In Progress=systematic_debugging", payload["reason"])

    def test_missing_state_file_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_steering(ws, _SLUG, _CLEAN_TASKLIST)  # state_content=None → state.md を作らない
            _bind(ws, _SLUG)
            code, out, err = _stop_done(ws)
        self.assertEqual(code, 0, f"err={err}")
        self.assertEqual(out.strip(), "", f"block されている: out={out}\nerr={err}")


class StateWriterDoesNotSelfContaminateTests(unittest.TestCase):
    """Stop hook 自身の state.md 書き込みが D-28 の検査対象を汚さないことを固定する。

    `lib/handoff_summary.truncate_summary()` は `str.splitlines()` → `"\\n".join()` を通すため、
    LF / CR 以外の行区切り文字 8 種は **LF に畳まれてから** `Last Handoff Summary=` として
    state.md へ書かれる。この正規化が外れると、assistant 出力に U+2028 が 1 つ混じるだけで
    Stop hook が自分で書いた state.md を D-28 の検査が恒久 block する。
    """

    def test_truncate_summary_folds_line_break_chars_to_lf(self):
        for ch in _LINE_BREAK_CHARS:
            with self.subTest(char=f"U+{ord(ch):04X}"):
                result = _handoff_summary.truncate_summary(f"前半{ch}後半")
                self.assertNotIn(ch, result)
                self.assertEqual(result, "前半\n後半")


if __name__ == "__main__":
    unittest.main()

"""bind 済み done guard のデグレ防止契約（AC-3 / CT-3 の Check 2 / Check 3）。

実行:
  python3 -m pytest plugins/gate-driven-development/tests/test_stop_hook_done_guard_regression_contract.py -q
  python3 -m unittest tests.test_stop_hook_done_guard_regression_contract

bind 限定の変更は done guard の**検査対象**を bind 済み steering に絞る変更で、
「絞りすぎて guard が効かなくなる」のが失敗型（CT-3）。`validate_done_preconditions()`
の 3 チェックのうち、

- **Check 1**（未完了タスク）は `test_stop_hook_bind_resolution_contract.py` の
  `BindScopedDoneGuardTests` にある。**移設しない**: 同ファイルの
  `test_bound_worktree_is_not_blocked_by_foreign_worktree_tasklist` と
  **同じ fixture・逆の期待値**の対照実験になっており、離すと AC-1 側の
  判別力が落ちる。
- **Check 2**（`## Verification`）と **Check 3**（`Route In Progress`）は本ファイルで pin する。

**測っている範囲**: 2 worktree fixture（wtA=他人 / wtB=bind 済み対象）に対する
`reason=done` の stop hook 出力（`decision` / `reason`）に加えて、
`TableVerificationRowClassificationTests` / `TableVerificationRowClassificationAllowPathTests`
が単一 worktree（`_run_verification()` の bind 済み fixture）で Check 2 の
**表行 status セル分類**（block 方向 / allow 方向、S-B3 の既知の見落としを含む）を測り、
`VerificationNoRowsMessageTests` が「検証行がありません」の本文と回復ヒントの文言を測る。
**測っていない範囲**: fence 除去・インデント行の扱いは
`test_stop_hook_tasklist_fence_contract.py` の `VerificationFenceTests` が測る
（本ファイルが新たに測るのは表行の**受理後の分類**であり、fence/インデントの
**受理可否**そのものではない）。単一 worktree での Check 2 / Check 3 の存在自体は
`test_stop_hook_e2e.py` が測る（本ファイルはそこに **bind スコープ**の次元を足す）。

Check 3 は `tasklist.md` とは**別に** `<steering>/state.md` を読む経路で、bind 由来の
ディレクトリを使っていることを直接測るテストが無かった。他 worktree の
`Route In Progress` で block されると、自分の worktree を直しても解除できない
―― bind 限定で塞いだ症状そのものになる。
Check 3 が `state.md` の正準形を読み、散文を拾わないことは
`test_stop_hook_route_in_progress_canonical_form_contract.py` が測る。

**Check 2 の「他 worktree の Verification 不備で block しない」は本ファイルに置かない**:
Check 1 と Check 2 は同じ `tasklist_path` から作った `structural_lines` を読むので、
Check 2 だけスコープが壊れる変異が構成できない。実測（`tasklist_path` を
bind 由来から `git worktree list` 走査に戻す変異）でも、そのテストを一意に殺す変異は
無く、既存の `test_bound_worktree_is_not_blocked_by_foreign_worktree_tasklist` が
同じ変異で落ちる。独立した述語を足さない一点 pin なので置かない。
"""
from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

# `python3 -m unittest tests.<module>` でも共有ヘルパを解決できるようにする
# （pytest は tests/ を自動で path に入れるが unittest は入れない）= 共通規約 13。
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _stop_hook_test_base import (  # noqa: E402
    _CLEAN_TASKLIST,
    _bind,
    _make_two_worktree_fixture,
    _stop_done,
    _write_steering,
)
from _plugin_module_loader import load_plugin_module  # noqa: E402

_TARGET_SLUG = "20260822-target"
_FOREIGN_SLUG = "20260101-foreign"

#: `## Verification` 節そのものが無い tasklist（Check 2 の 1 形目）。
_NO_VERIFICATION_TASKLIST = textwrap.dedent(
    """\
    # Tasklist

    ## Current Task
    - なし

    ## Pending Tasks
    - なし

    ## Completed Tasks
    - T1 | AC-01 | done

    ## Status
    Next Action=done
    """
)

_ROUTE_STATE = "# State\nRoute In Progress=systematic_debugging\n"
_CLEAN_ROUTE_STATE = "# State\nRoute In Progress=none\n"


def _steering(worktree: Path, slug: str) -> Path:
    return worktree / ".steering" / slug


def _payload(out: str) -> dict:
    """stop hook の stdout を JSON として読む（平文出力に退化したら落とす）。"""
    return json.loads(out.strip())


_VERIFICATION_FIXTURE_SLUG = "20260830-verification-fixture"


def _verification_tasklist(verification_body: str) -> str:
    """他は clean で `## Verification` 本文だけを変えた単一 steering 用 tasklist。"""
    return (
        "# Tasklist\n\n"
        "## Current Task\n- なし\n\n"
        "## Pending Tasks\n- なし\n\n"
        "## Completed Tasks\n- T1 | AC-01 | done\n\n"
        "## Verification\n"
        f"{verification_body}\n\n"
        "## Status\nNext Action=done\n"
    )


def _run_verification(verification_body: str) -> tuple[int, str, str]:
    """単一 steering の Verification 本文だけを変えて stop hook を実行する（`_stop_done` 経由）。

    `_bind()` で bind 済みにする（T-2 で追加）。bind 前は allow 経路で
    `[gdd:bind-unresolved]` の warn systemMessage が常に stdout に混ざり、
    T-2 の allow-path テスト（`out.strip() == ""` を期待する）が AC-6 とは
    無関係な理由で fail する（`BoundDoneGuardSuccessPathTests` が同じ理由で
    bind 済みにしているのと同じ事情）。block 方向（T-1 の
    `TableVerificationRowClassificationTests`）は block payload しか出さない
    経路なので bind 有無で挙動は変わらない。
    """
    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp)
        _write_steering(
            ws, _VERIFICATION_FIXTURE_SLUG, _verification_tasklist(verification_body)
        )
        _bind(ws, _VERIFICATION_FIXTURE_SLUG)
        return _stop_done(ws)


def _judge_in_process(verification_body: str) -> tuple[str, str]:
    """stop hook を起動せずに、Check 2 の判定関数で (decision, reason) を出す。

    hook の main は、clean な tasklist では Check 1・3 の理由を足さず、
    `_verification_errors` の返り値を改行でつないで reason にする（入口との一致は
    `CaseTableEntryPointTests` が表ごとに確かめる）。
    """
    reason_list = _scan_reasons(_STOP_HOOK, verification_body)[0]
    return ("block" if reason_list else "allow"), "\n".join(reason_list)


def _scan_reasons(hook, verification_body: str):
    kept, _unclosed, fence_before, fenced_heading_lines = hook.strip_fenced_lines_marked(
        _verification_tasklist(verification_body)
    )
    found, rows, violations, unfinished = hook._scan_verification(
        kept, fence_before=fence_before, fenced_heading_lines=fenced_heading_lines
    )
    return hook._verification_errors(found, rows, violations, unfinished), violations


_STOP_HOOK = load_plugin_module("hooks/scripts/gdd_stop_hook.py")


class TableVerificationRowClassificationTests(unittest.TestCase):
    """done guard Check 2: 表行の status セル分類（block 方向。AC-1, AC-2, AC-3, AC-4, AC-5）。

    表行（`|` 始まり）を「装飾・空白を除去した値が許容 status 値
    （`pending`/`pass`/`fail`/`n/a`/`unsupported`）と完全一致するセルを持つ行だけを
    data 行と認める」規則に反転させたことを、block 方向（未完了/失敗検出・検証行なしの
    fail-closed）でまず固定する。allow 方向（全 pass・N/A・unsupported・list 行の
    非対称・S-B3 残余）は `TableVerificationRowClassificationAllowPathTests`（T-2）で
    固定する。

    T-5 (AC-11): 閉じた文法（design.md § 1.1「data_row は非装飾の 4 セル完全一致」）
    への移行により、`_BLOCK_PENDING_CASES` 98 件中 90 件は decision=block を
    維持したまま reason が「未完了/失敗」→「schema 違反行」へ変わる（絶対期待値の
    判定表として reason を 3 要素目に持たせた）。1 件（`notes_only_status_word_is_detected`）
    のみ allow へ反転したため `TableVerificationRowClassificationAllowPathTests`
    の `_ALLOW_CASES` へ移した（design.md § 5 最下段「status 列以外のセルの
    pending/fail」の唯一の block→done クラス）。1 case ずつの判断根拠は各 case
    直前のコメントを参照。
    """

    _BLOCK_PENDING_CASES = [
        # 維持: ASCII 空白/タブのみの padding・大文字化・エスケープ pipe は design.md §1.1/§1.2 の ws 定義・正規化手順の範囲内で吸収され、新文法でも
        # data_row として受理される
        ("table_pending_canonical_padding",
         "| method=ac:AC-1 | pending | evidence | notes |",
         "未完了/失敗"),
        # 維持: ASCII 空白/タブのみの padding・大文字化・エスケープ pipe は design.md §1.1/§1.2 の ws 定義・正規化手順の範囲内で吸収され、新文法でも
        # data_row として受理される
        ("table_pending_two_space_padding",
         "| method=ac:AC-1 |  pending  | evidence | notes |",
         "未完了/失敗"),
        # 維持: ASCII 空白/タブのみの padding・大文字化・エスケープ pipe は design.md §1.1/§1.2 の ws 定義・正規化手順の範囲内で吸収され、新文法でも
        # data_row として受理される
        ("table_pending_no_padding",
         "|method=ac:AC-1|pending|evidence|notes|",
         "未完了/失敗"),
        # 維持: ASCII 空白/タブのみの padding・大文字化・エスケープ pipe は design.md §1.1/§1.2 の ws 定義・正規化手順の範囲内で吸収され、新文法でも
        # data_row として受理される
        ("table_pending_uppercase",
         "| method=ac:AC-1 | PENDING | evidence | notes |",
         "未完了/失敗"),
        # 反転(reason変化): 全角空白は ws ではない（design.md §1.1）ため padding が残ったまま status セルと不一致になり line violation になる
        ("table_pending_fullwidth_and_tab_padding",
         "| method=ac:AC-1 | 　pending\t | evidence | notes |",
         "schema 違反行"),
        # 反転(reason変化): バッククォート装飾は §1.2 が列挙する 5 種の正規化に含まれず除去されないため status セル完全一致に外れ line violation になる
        ("table_pending_backtick_decorated",
         "| method=ac:AC-1 | `pending` | evidence | notes |",
         "schema 違反行"),
        # 反転(reason変化): 太字(`**`)装飾は §1.2 の正規化対象外のため status セル完全一致に外れ line violation になる
        ("table_pending_bold_decorated",
         "| method=ac:AC-1 | **pending** | evidence | notes |",
         "schema 違反行"),
        # 維持: ASCII 空白/タブのみの padding・大文字化・エスケープ pipe は design.md §1.1/§1.2 の ws 定義・正規化手順の範囲内で吸収され、新文法でも
        # data_row として受理される
        ("table_pending_notes_with_escaped_pipe",
         "| method=ac:AC-1 | pending | evidence | a \\| b |",
         "未完了/失敗"),
        # 維持: ASCII 空白/タブのみの padding・大文字化・エスケープ pipe は design.md §1.1/§1.2 の ws 定義・正規化手順の範囲内で吸収され、新文法でも
        # data_row として受理される
        ("table_fail",
         "| method=ac:AC-1 | fail | evidence | notes |",
         "未完了/失敗"),
        # 反転(reason変化): list 行は §1.1 の data_row（`|` 始まり）に一致しないため line violation。table 側の pending 行は canonical
        # なので unfinished 検出は効くが、violation が 1 件でもあれば D5 判定順どおり reason は schema 違反行が優先される
        ("mixed_list_all_pass_table_pending",
         "- method=ac:AC-2 | pass | evidence | notes\n"
         "| method=ac:AC-1 | pending | evidence | notes |",
         "schema 違反行"),
        # 反転(reason変化): `ROW-ID` 列を含む header は §1.1 の 4 セル `method|status|evidence|notes` に一致しないため header
        # として認識されず、5 セル構成の全行が line violation になる
        ("row_id_header_with_pending_data_row",
         "| ROW-ID | method | status | evidence | notes |\n"
         "|---|---|---|---|---|\n"
         "| 1 | method=ac:AC-1 | pending | evidence | notes |",
         "schema 違反行"),
        # 反転(reason変化): list 行は `|` 始まりの data_row に一致しないため line violation になる（迂回不可の結論は不変。旧 R1 の回帰 pin
        # を新文法向けに反転）
        ("list_only_pending_regression_pin",
         "- method=ac:AC-1 | pending | evidence | notes",
         "schema 違反行"),
        # 反転(reason変化): 行頭が `- ` である以上、§1.1 の data_row（`|` 始まり）にも header/separator にも一致しないため
        # line violation。padding 自体は §1.2 の ws 正規化で吸収される範囲だが、正規化は data_row と判定された後の手順であり、
        # list 行はそこへ到達しない ―― つまり判定は padding の有無に依存しない（同じ body を `|` 始まりにした
        # `table_pending_two_space_padding` は 維持 + 「未完了/失敗」）
        ("list_pending_two_space_padding",
         "- method=ac:AC-1 |  pending  | evidence | notes",
         "schema 違反行"),
        # 反転(reason変化): バッククォート装飾は §1.2 が列挙する 5 種の正規化に含まれず除去されないため status セル完全一致に外れ line violation になる
        ("list_pending_backtick_decorated",
         "- method=ac:AC-1 | `pending` | evidence | notes",
         "schema 違反行"),
        # 反転(reason変化): padding を一切置かない形でも文法上の結論は同じ ―― `- ` 始まりは §1.1 の data_row（`|` 始まり）に
        # 一致しないため line violation。§1.2 の ws 正規化を持ち出すまでもなく data_row の定義で落ちる（同じ body を `|`
        # 始まりにした `table_pending_no_padding` は 維持 + 「未完了/失敗」）
        ("list_pending_no_padding",
         "- method=ac:AC-1|pending|evidence|notes",
         "schema 違反行"),
        # 反転(reason変化): ゼロ幅文字は §1.2 が列挙する 5 種の正規化に含まれず除去されないため status セル完全一致に外れる（design.md
        # §5「制御文字/zero-width」→ violation）
        ("table_pending_zero_width_with_pass_row",
         "| method=ac:AC-1 | pending​ | evidence | notes |\n"
         "| method=ac:AC-2 | pass | evidence | notes |",
         "schema 違反行"),
        # 反転(reason変化): 取り消し線(`~~`)装飾は正規化対象外のため status セル完全一致に外れる
        ("table_pending_strikethrough_with_pass_row",
         "| method=ac:AC-1 | ~~pending~~ | evidence | notes |\n"
         "| method=ac:AC-2 | pass | evidence | notes |",
         "schema 違反行"),
        # 反転(reason変化): 絵文字付加は装飾の一種であり正規化対象外のため status セル完全一致に外れる（design.md §5「装飾 status」→ violation）
        ("decorated_pending_emoji_with_pass_row_blocks",
         "| method=ac:AC-1 | pending ⏳ | evidence | notes |\n"
         "| method=ac:AC-2 | pass | evidence | notes |",
         "schema 違反行"),
        # 反転(reason変化): `未実施` は §1.1 の許容 status 値集合に無い語のため、method セルが一致しても status 不一致で line violation になる
        ("non_status_word_with_pass_row_blocks",
         "| method=ac:AC-1 | 未実施 | evidence | notes |\n"
         "| method=ac:AC-2 | pass | evidence | notes |",
         "schema 違反行"),
        # 反転(reason変化): list 行・非 schema 表のいずれも §1.1 の data_row（`|` 始まりの 4 セル）に一致しないため全行 line violation になる
        ("list_all_pass_with_non_schema_table_blocks",
         "- method=ac:AC-1 | pass | evidence | notes\n"
         "| AC | 検証方法 | 実測 |\n"
         "|---|---|---|\n"
         "| AC-1 | manual | 未実施 |",
         "schema 違反行"),
        # 反転(reason変化): status 列は列位置で固定され（§1.1 の 4 セル構成）、evidence/notes 欄にある許容値語は判定に使われない。status
        # 列自体が許容値と不一致のため line violation になる
        ("unrecognized_status_with_allowed_value_in_evidence_blocks",
         "| method | status | evidence | notes |\n"
         "|---|---|---|---|\n"
         "| method=ac:AC-1 | 未実施 | N/A | 後で |",
         "schema 違反行"),
        # 反転(reason変化): status 列は列位置で固定され（§1.1 の 4 セル構成）、evidence/notes 欄にある許容値語は判定に使われない。status
        # 列自体が許容値と不一致のため line violation になる
        ("unrecognized_status_with_allowed_value_in_notes_blocks",
         "| method=ac:AC-1 | 未実施 | evidence | pass |",
         "schema 違反行"),
        # 反転(reason変化): 新文法に「表ブロックの列束縛」という概念はなく、行ごとに独立して data_row 判定する。header 語を含む非 canonical 行は単に line
        # violation になる
        ("header_word_cell_in_non_first_row_is_not_header",
         "| method=ac:AC-1 | pass | evidence | notes |\n"
         "| status | pending | | |",
         "schema 違反行"),
        # 反転(reason変化): header 判定は §1.1 の 4 語完全一致のみで、`結果` のような語彙は header と認識されない。以降の非 canonical data 行も line
        # violation になる
        ("header_without_status_word_does_not_read_evidence_column",
         "| method | 結果 | evidence | notes |\n"
         "|---|---|---|---|\n"
         "| ac:AC-1 | 未実施 | N/A | 手動確認予定 |",
         "schema 違反行"),
        # 反転(reason変化): 新文法に列束縛の概念が無いため、この現象自体が消滅する。header/separator は依然 canonical のため無視され、間に挟まる list 注記と後続の非
        # canonical data 行が line violation になる
        ("status_column_binding_survives_interleaved_list_note",
         "| method | status | evidence | notes |\n"
         "|---|---|---|---|\n"
         "- 注: 下記参照\n"
         "| method=ac:AC-1 | 未実施 | N/A | 後で |",
         "schema 違反行"),
        # 反転(reason変化): header は §1.1 の 4 語完全一致でのみ判定され、値を持つ最初の行が header に化けることはない。非 canonical な行はそのまま line
        # violation になる
        ("header_word_cell_in_first_row_with_real_values_is_not_header",
         "| ac:AC-1 | pass | x | |\n"
         "\n"
         "| ROW | pending | 手動 |",
         "schema 違反行"),
        # 反転(reason変化): 凡例語を含む行を特別扱いする規則は新文法に無い。単に data_row の 4 セル完全一致に外れるため line violation になる
        ("pending_row_with_legend_word_in_notes_is_not_skipped",
         "| ac:AC-1 | pass | x | ok |\n"
         "| ac:AC-2 | pending | | 許容 status 参照 |",
         "schema 違反行"),
        # 反転(reason変化): list 行・非 schema 表のいずれも data_row に一致しないため line violation のまま block が維持される（迂回不可の結論は不変）
        ("non_schema_table_rewritten_as_list_still_blocks",
         "- AC | 検証方法 | 実測\n"
         "- AC-1 | manual | 未実施",
         "schema 違反行"),
        # 反転(reason変化): status セルに理由書き（`N/A（理由）`）を含む行は許容値と完全一致しないため line violation になる
        ("list_row_with_reason_in_status_cell_blocks",
         "- method=ac:AC-1 | N/A（理由） | evidence | notes",
         "schema 違反行"),
        # 反転(reason変化): 凡例語を含む行を特別扱いする規則は新文法に無い。単に data_row の 4 セル完全一致に外れるため line violation になる
        ("pending_row_with_legend_word_in_notes_cell_blocks",
         "| ac:AC-1 | pass | x | ok |\n"
         "| ac:AC-2 | 未実施 |  | 各行の形式を参照 |",
         "schema 違反行"),
        # 反転(reason変化): `*`/`+` marker の list 行は §1.1 の data_row（`|` 始まり）に一致しないため line violation
        # になる（迂回不可の結論は不変）
        ("asterisk_marker_list_row_is_checked",
         "- method=ac:AC-1 | pass | e | n\n"
         "* AC-1 | manual | 未実施",
         "schema 違反行"),
        # 反転(reason変化): `*`/`+` marker の list 行は §1.1 の data_row（`|` 始まり）に一致しないため line violation
        # になる（迂回不可の結論は不変）
        ("plus_marker_list_row_pending_is_detected",
         "- method=ac:AC-1 | pass | e | n\n"
         "+ AC-2 | manual | pending",
         "schema 違反行"),
        # 維持: 両方の行がすでに canonical 表記のため、新文法でも通常の data 行として受理される（節分割の挙動検証が主眼で文法閉包の影響を受けない）
        ("second_verification_section_is_scanned",
         "| method=ac:AC-1 | pass | e | n |\n"
         "\n"
         "## Other\n"
         "\n"
         "## Verification\n"
         "\n"
         "| method=ac:AC-2 | pending | e | n |",
         "未完了/失敗"),
        # 反転(reason変化): `method=ac:*` 行に `N/A`/`unsupported` を書く形は §1.3 の許容値制約（ac 行は pending/pass/fail
        # のみ）に反するため line violation になる（結論は不変、reason のみ変化）
        ("ac_row_with_na_status_blocks",
         "| method=ac:AC-1 | N/A | evidence | notes |",
         "schema 違反行"),
        # 反転(reason変化): `method=ac:*` 行に `N/A`/`unsupported` を書く形は §1.3 の許容値制約（ac 行は pending/pass/fail
        # のみ）に反するため line violation になる（結論は不変、reason のみ変化）
        ("ac_row_with_unsupported_status_blocks",
         "| method=ac:AC-1 | unsupported | evidence | notes |",
         "schema 違反行"),
        # 反転(reason変化): `security_evidence:` は method セルでのみ意味を持つ（§1.1）。notes 欄に書いても method セルと認識されず、行全体が
        # data_row 不一致で line violation になる
        ("security_evidence_token_in_notes_column_blocks",
         "| method=ac:AC-1 | N/A | security_evidence:none | 未検証 |",
         "schema 違反行"),
        # 反転(reason変化): 凡例語を前置しても行の形自体が data_row の 4 セル完全一致に外れるため line violation になる（迂回不可の結論は不変）
        ("legend_word_prefixed_pending_row_blocks",
         "| method=ac:AC-1 | pass | ok | - |\n"
         "| 各行の形式 AC-2 | pending | | |",
         "schema 違反行"),
        # 反転(reason変化): 番号付き list 行は `|` 始まりでないため line violation になる（迂回不可の結論は不変）
        ("ordered_list_row_is_checked",
         "| method=ac:AC-1 | pass | e | n |\n"
         "1. AC-2 | manual | pending",
         "schema 違反行"),
        # 反転(reason変化): 外側パイプを省略した行は §1.2 手順 2「`|` で始まり `|` で終わる」に反するため line violation になる（迂回不可の結論は不変）
        ("table_row_without_outer_pipes_is_checked",
         "| method=ac:AC-1 | pass | e | n |\n"
         "method=ac:AC-2 | pending | |",
         "schema 違反行"),
        # 反転(reason変化): 凡例語を前置しても行の形自体が data_row の 4 セル完全一致に外れるため line violation になる（迂回不可の結論は不変）
        ("legend_word_without_colon_does_not_hide_unverified_row",
         "| method=ac:AC-1 | pass | e | n |\n"
         "| 各行の形式 AC-2 | 未実施 | | |",
         "schema 違反行"),
        # 反転(reason変化): `status=` ラベルは §1.2 の正規化 5 種に無いため除去されず、status セルが許容値と完全一致しなくなり line violation
        # になる（design.md §5「status=ラベル形」→ violation）
        ("status_labelled_pending_is_detected",
         "- method=ac:AC-1 | status=pending | e | -",
         "schema 違反行"),
        # 反転(reason変化): `AC-1: 説明` のようなラベル付き method セルは §1.1 の 3
        # 形（`method=ac:`/`method=security_evidence:`/`method=refactor-checkpoint`）のいずれにも一致しないため line violation
        # になる
        ("labelled_ac_method_cell_list_row_is_checked",
         "- AC-1: カーソル取得 | 未実施 | 証跡なし | -",
         "schema 違反行"),
        # 反転(reason変化): `security_evidence:` は method セルでのみ意味を持つ（§1.1）。notes 欄に書いても method セルと認識されず、行全体が
        # data_row 不一致で line violation になる
        ("security_evidence_token_in_notes_still_blocks_after_marker_strip",
         "- method=ac:AC-1 | status=N/A | security_evidence:none | -",
         "schema 違反行"),
        # 反転(reason変化): header は §1.1 の 4 語完全一致でのみ判定されるため、この種の誤 header 化はそもそも起きない。行自体は data_row 不一致で line
        # violation になる
        ("status_word_first_row_with_pending_is_not_header",
         "| 状態 | pending |\n"
         "\n"
         "| method | status | evidence | notes |\n"
         "|---|---|---|---|\n"
         "| method=ac:AC-1 | pass | x | - |",
         "schema 違反行"),
        # 反転(reason変化): 凡例語を前置しても行の形自体が data_row の 4 セル完全一致に外れるため line violation になる（迂回不可の結論は不変）
        ("legend_prefixed_verification_row_is_not_skipped",
         "| method=ac:AC-1 | pass | e | n |\n"
         "- 各行の形式: method=ac:AC-2 | 未実施 | 手動 |",
         "schema 違反行"),
        # 反転(reason変化): 補助表の除外という概念が新文法に無い。全ての非 canonical 行が一律 line violation になる（検出の優先順位という論点自体が消滅）
        ("pending_fail_rows_survive_auxiliary_table_exclusion",
         "| method | status | evidence | notes |\n"
         "|---|---|---|---|\n"
         "| AC-1: a | pass | ok | |\n"
         "\n"
         "| pending | AC-2: b | 手動確認 |\n"
         "| fail | AC-3: c | NG |",
         "schema 違反行"),
        # 反転(reason変化): `V-01` のような ROW-ID セルを含む行は §1.1 の 3 形いずれの method パターンにも一致しないため line violation になる
        ("row_id_table_without_header_ac_na_blocks",
         "| V-01 | ac:AC-1 | N/A | x |",
         "schema 違反行"),
        # 反転(reason変化): `V-01` のような ROW-ID セルを含む行は §1.1 の 3 形いずれの method パターンにも一致しないため line violation になる
        ("row_id_table_without_header_ac_unsupported_blocks",
         "| V-01 | ac:AC-1 | unsupported | x |",
         "schema 違反行"),
        # 反転(reason変化): 括弧書きなどの注記付き status は許容値と完全一致しないため line violation
        # になる（旧実装の`_resolved_status`注記解決は削除済み。design.md AC-8）
        ("annotated_pending_in_status_column_blocks",
         "| method | status | evidence | notes |\n"
         "|---|---|---|---|\n"
         "| method=ac:AC-1 | pending(再実行待ち) | e | n |",
         "schema 違反行"),
        # 反転(reason変化): 括弧書きなどの注記付き status は許容値と完全一致しないため line violation
        # になる（旧実装の`_resolved_status`注記解決は削除済み。design.md AC-8）
        ("annotated_fail_in_status_column_blocks",
         "| method | status | evidence | notes |\n"
         "|---|---|---|---|\n"
         "| method=ac:AC-1 | fail: 3 件残 | e | n |",
         "schema 違反行"),
        # 反転(reason変化): 括弧書きなどの注記付き status は許容値と完全一致しないため line violation
        # になる（旧実装の`_resolved_status`注記解決は削除済み。design.md AC-8）
        ("annotated_pending_in_list_row_blocks",
         "- method=ac:AC-1 | pending（再実行待ち） | e | n",
         "schema 違反行"),
        # 反転(reason変化): 新文法の method/status は常に固定列位置（1 列目=method・2列目=status）で読むため「列順が違う表」という概念自体が消滅する。非
        # canonical な行は line violation になる
        ("method_column_not_adjacent_to_status_still_blocks_ac_na",
         "| 判定 | 検証方法 | 証跡 |\n"
         "|---|---|---|\n"
         "| pass | ac:AC-1 | 手動 |\n"
         "| N/A | ac:AC-2 | 未実施 |",
         "schema 違反行"),
        # 反転(reason変化): 外側パイプを省略した行は §1.2 手順 2「`|` で始まり `|` で終わる」に反するため line violation になる（迂回不可の結論は不変）
        ("bare_row_with_explicit_pending_is_checked",
         "| method=ac:AC-9 | pass | e | n |\n"
         "結合テスト | 手動 | 手順書 | pending",
         "schema 違反行"),
        # 反転(reason変化): list marker を剥がして 0 列目を status として読む規則は新文法に無い。`|` 始まりでない行は line violation になる
        ("list_marker_is_stripped_before_status_lookup",
         "| method=ac:AC-9 | pass | e | n |\n"
         "- pending | ac:AC-2 | log",
         "schema 違反行"),
        # 反転(reason変化): `*`/`+` marker の list 行は §1.1 の data_row（`|` 始まり）に一致しないため line violation
        # になる（迂回不可の結論は不変）
        ("plus_marker_is_stripped_before_status_lookup",
         "| method=ac:AC-9 | pass | e | n |\n"
         "+ fail | ac:AC-2 | log",
         "schema 違反行"),
        # 反転(reason変化): 括弧書きなどの注記付き status は許容値と完全一致しないため line violation
        # になる（旧実装の`_resolved_status`注記解決は削除済み。design.md AC-8）
        ("headerless_status_first_column_with_annotation_blocks",
         "| method=ac:AC-9 | pass | e | n |\n"
         "\n"
         "| pending（明日） | ac:AC-2 | log |",
         "schema 違反行"),
        # 反転(reason変化): 凡例語を前置しても行の形自体が data_row の 4 セル完全一致に外れるため line violation になる（迂回不可の結論は不変）
        ("legend_prefix_on_table_row_does_not_hide_status",
         "| method=ac:AC-9 | pass | e | n |\n"
         "| 各行の形式: 手動 | pending | log |",
         "schema 違反行"),
        # 反転(reason変化): 新文法の method/status は常に固定列位置（1 列目=method・2列目=status）で読むため「列順が違う表」という概念自体が消滅する。非
        # canonical な行は line violation になる
        ("status_column_first_still_detects_unrecognized_ac_row",
         "| status | method | evidence |\n"
         "|---|---|---|\n"
         "| pass | ac:AC-1 | 手動 |\n"
         "| 未実施 | ac:AC-2 | まだ |",
         "schema 違反行"),
        # 反転(reason変化): 識別子セルの前置語・単セル化・trailing 語のいずれも method セルの 3 形完全一致から外れるため line violation
        # になる（識別子推定という概念が新文法に無い）
        ("identifier_cell_with_prefixed_words_is_still_checked",
         "| method | status | evidence | notes |\n"
         "|---|---|---|---|\n"
         "| method=ac:AC-9 | pass | e | n |\n"
         "| 検証 対象 は ac:AC-1 | 未実施 | | |",
         "schema 違反行"),
        # 反転(reason変化): 識別子セルの前置語・単セル化・trailing 語のいずれも method セルの 3 形完全一致から外れるため line violation
        # になる（識別子推定という概念が新文法に無い）
        ("numeric_row_id_cell_is_a_verification_row",
         "| method=ac:AC-9 | pass | e | n |\n"
         "| 1 | 手動確認 | 未実施 |",
         "schema 違反行"),
        # 反転(reason変化): 2 セルの list 行は `|` 始まりの 4 セル data_row に一致しないため line violation になる
        ("two_cell_list_row_with_annotated_pending_blocks",
         "- method=ac:AC-2 | pending(明日)",
         "schema 違反行"),
        # 反転(reason変化): 日本語 header は §1.1 の 4 語（method/status/evidence/notes）完全一致でのみ header と認められる語彙に含まれないため
        # header として扱われず、後続の非 canonical data 行も line violation になる（design.md §5「日本語 header 表」→ violation）
        ("non_vocabulary_japanese_header_still_checks_rows",
         "| method=ac:AC-9 | pass | e | n |\n"
         "\n"
         "| 検証項目 | 結果 | 証跡 |\n"
         "|---|---|---|\n"
         "| ac:AC-1 | 未実施 | |",
         "schema 違反行"),
        # 反転(reason変化): 補助表は method 値域外のため line violation になる。「後続の表を巻き込む/巻き込まない」という表ブロック単位の概念自体が新文法に無い
        ("auxiliary_table_does_not_swallow_following_table",
         "| method=ac:AC-9 | pass | e | n |\n"
         "\n"
         "| # | 変異 | 実測 |\n"
         "|---|---|---|\n"
         "| MUT-A | x | y |\n"
         "| method | status |\n"
         "|---|---|\n"
         "| method=ac:AC-1 | 未実施 |",
         "schema 違反行"),
        # 反転(reason変化): header 無し表の先頭行を header として消費する規則も、evidence 列を status として誤読する経路も新文法には無い（列位置は固定）。非
        # canonical な行は line violation になる
        ("headerless_table_first_row_is_not_consumed_as_header",
         "| method=ac:AC-9 | pass | e | n |\n"
         "\n"
         "| 1 | 手動確認 | 未実施 |",
         "schema 違反行"),
        # 反転(reason変化): 識別子セルの前置語・単セル化・trailing 語のいずれも method セルの 3 形完全一致から外れるため line violation
        # になる（識別子推定という概念が新文法に無い）
        ("single_cell_table_row_with_identifier_is_checked",
         "| method=ac:AC-9 | pass | e | n |\n"
         "| ac:AC-1 は未実施 | | |",
         "schema 違反行"),
        # 反転(reason変化): 外側パイプを省略した行は §1.2 手順 2「`|` で始まり `|` で終わる」に反するため line violation になる（迂回不可の結論は不変）
        ("bare_row_without_marker_is_checked",
         "| method=ac:AC-9 | pass | e | n |\n"
         "ac:AC-1 | 手動 | 未実施",
         "schema 違反行"),
        # 反転(reason変化): 新文法の method/status は常に固定列位置（1 列目=method・2列目=status）で読むため「列順が違う表」という概念自体が消滅する。非
        # canonical な行は line violation になる
        ("status_column_third_still_detects_unrecognized_ac_row",
         "| method | evidence | status | notes |\n"
         "|---|---|---|---|\n"
         "| ac:AC-1 | y | 未実施 | - |\n"
         "| ac:AC-2 | x | pass | - |",
         "schema 違反行"),
        # 反転(reason変化): 凡例語を前置しても行の形自体が data_row の 4 セル完全一致に外れるため line violation になる（迂回不可の結論は不変）
        ("legend_row_listing_status_values_with_pipes_blocks",
         "- 許容 status: pending | pass | fail | n/a | unsupported\n"
         "\n"
         "| method | status | evidence | notes |\n"
         "|---|---|---|---|\n"
         "| method=ac:AC-1 | pass | npm test | - |",
         "schema 違反行"),
        # 反転(reason変化): 凡例語を前置しても行の形自体が data_row の 4 セル完全一致に外れるため line violation になる（迂回不可の結論は不変）
        ("legend_prefixed_list_row_with_pending_blocks",
         "| method=ac:AC-9 | pass | e | n |\n"
         "- 各行の形式: 手動確認 | pending | log",
         "schema 違反行"),
        # 反転(reason変化): header 無し表の先頭行を header として消費する規則も、evidence 列を status として誤読する経路も新文法には無い（列位置は固定）。非
        # canonical な行は line violation になる
        ("headerless_table_evidence_pass_does_not_hide_unrecognized_status",
         "| method=ac:AC-1 | 未実施 | pass | notes |",
         "schema 違反行"),
        # 反転(reason変化): header 無し表の先頭行を header として消費する規則も、evidence 列を status として誤読する経路も新文法には無い（列位置は固定）。非
        # canonical な行は line violation になる
        ("headerless_list_evidence_pass_does_not_hide_unrecognized_status",
         "- method=ac:AC-1 | 未実施 | pass | notes",
         "schema 違反行"),
        # 反転(reason変化): 列束縛の持ち越しという概念が新文法に無いため、この現象自体が起きない。非 canonical な行は line violation になる
        ("adjacent_table_rebinds_header_instead_of_carrying_columns",
         "| method | evidence | notes | status |\n"
         "|---|---|---|---|\n"
         "| ac:AC-9 | ok | - | pass |\n"
         "| method | status | evidence | notes |\n"
         "|---|---|---|---|\n"
         "| ac:AC-1 | 未実施 | 手動 | pass |",
         "schema 違反行"),
        # 反転(reason変化): 外側パイプを省略した行は §1.2 手順 2「`|` で始まり `|` で終わる」に反するため line violation になる（迂回不可の結論は不変）
        ("bare_two_cell_row_with_pending_blocks",
         "| method | status | evidence | notes |\n"
         "|---|---|---|---|\n"
         "| ac:AC-1 | pass | log | - |\n"
         "ac:AC-2 | pending",
         "schema 違反行"),
        # 反転(reason変化): 全角パイプ（｜）は §1.2 の区切り文字（半角 `|`）ではないため `|` 始まりの判定に一致せず line violation になる（design.md
        # §5「全角パイプ」→ violation）
        ("fullwidth_pipe_row_with_pending_blocks",
         "| method=ac:AC-9 | pass | e | n |\n"
         "ac:AC-1 ｜ pending ｜ log",
         "schema 違反行"),
        # 反転(reason変化): インデントされた入れ子 list 行は `|` 始まりでないため line violation になる（design.md §5「インデント行」→
        # violation。無条件検出という旧 ADR 不変条件 1 はもう適用されない）
        ("indented_nested_list_status_fail_blocks",
         "- `AC1`\n"
         "  - Method: 手動確認\n"
         "  - Status: fail\n"
         "  - Evidence: -",
         "schema 違反行"),
        # 反転(reason変化): インデントされた入れ子 list 行は `|` 始まりでないため line violation になる（design.md §5「インデント行」→
        # violation。無条件検出という旧 ADR 不変条件 1 はもう適用されない）
        ("indented_nested_list_status_pending_blocks",
         "- `AC1`\n"
         "  - method: 手動確認\n"
         "  - status: pending\n"
         "  - evidence: none",
         "schema 違反行"),
        # 反転(reason変化): `AC-01 | test | status | ...` のような ID 列形は method セルの 3 形いずれにも一致しないため line violation
        # になる
        ("id_column_list_form_pending_blocks",
         "- AC-01 | test | pending | evidence | notes",
         "schema 違反行"),
        # 反転(reason変化): 括弧書きなどの注記付き status は許容値と完全一致しないため line violation
        # になる（旧実装の`_resolved_status`注記解決は削除済み。design.md AC-8）
        ("status_first_column_annotated_pending_blocks",
         "| pending（再実行待ち） | ac:AC-1 | pass |",
         "schema 違反行"),
        # 反転(reason変化): 括弧書きなどの注記付き status は許容値と完全一致しないため line violation
        # になる（旧実装の`_resolved_status`注記解決は削除済み。design.md AC-8）
        ("annotated_pending_on_unidentified_row_blocks",
         "| method=ac:AC-1 | pass | log |\n"
         "| 手動確認 | 2026-09-01 | pending（未実施） |",
         "schema 違反行"),
        # 反転(reason変化): 括弧書きなどの注記付き status は許容値と完全一致しないため line violation
        # になる（旧実装の`_resolved_status`注記解決は削除済み。design.md AC-8）
        ("annotated_fail_on_unidentified_row_blocks",
         "| method=ac:AC-1 | pass | log |\n"
         "| 手動確認 | 2026-09-01 | fail(3 件) |",
         "schema 違反行"),
        # 反転(reason変化): 列束縛の持ち越しという概念が新文法に無いため「見出しでリセットする」規則自体が不要になった。非 canonical な行は line violation になる
        ("heading_resets_the_table_column_binding",
         "| # | evidence | status | method |\n"
         "|---|---|---|---|\n"
         "| 1 | log | pass | method=ac:AC-1 |\n"
         "### 追加\n"
         "| method=ac:AC-2 | pending（再実行待ち） | pass |",
         "schema 違反行"),
        # 反転(reason変化): header は §1.1 の 4 語完全一致のみで判定されるため疑似 header が紛れ込む余地が無い。非 canonical な行は line violation
        # になる
        ("mid_block_pseudo_header_is_not_consumed",
         "| method=ac:AC-1 | pass | log |\n"
         "| 検証 | 2026-09-01 | 状態 |\n"
         "| method=ac:AC-2 | pending（未実施） | pass |",
         "schema 違反行"),
        # 反転(reason変化): 日本語の `ステータス:`/`状態:` ラベルは §1.2 の正規化対象外のため method/status セルの完全一致に外れ line violation になる
        ("japanese_status_label_pending_blocks",
         "| method=ac:AC-9 | pass | e | n |\n"
         "- ステータス: pending | 証跡なし",
         "schema 違反行"),
        # 反転(reason変化): 日本語の `ステータス:`/`状態:` ラベルは §1.2 の正規化対象外のため method/status セルの完全一致に外れ line violation になる
        ("japanese_state_label_pending_blocks",
         "| method=ac:AC-9 | pass | e | n |\n"
         "- 状態: pending",
         "schema 違反行"),
        # 反転(reason変化): インデントされた表・行は `|` 始まりでないため line violation になる（design.md §5「インデント行」→
        # violation。表かどうかの区別自体が新文法には無い）
        ("indented_verification_table_is_scanned",
         "- AC 検証結果は下表のとおり\n"
         "  | method | status | evidence |\n"
         "  |---|---|---|\n"
         "  | ac:AC-1 | 未実施 | - |",
         "schema 違反行"),
        # 反転(reason変化): インデントされた表・行は `|` 始まりでないため line violation になる（design.md §5「インデント行」→
        # violation。表かどうかの区別自体が新文法には無い）
        ("indented_verification_table_ac_row_na_blocks",
         "- 検証:\n"
         "  | method=ac:AC-1 | N/A | 未対応 |",
         "schema 違反行"),
        # 反転(reason変化): インデントされた表・行は `|` 始まりでないため line violation になる（design.md §5「インデント行」→
        # violation。表かどうかの区別自体が新文法には無い）
        ("indented_auxiliary_table_blocks_as_a_known_tradeoff",
         "| method=ac:AC-1 | pass | e | n |\n"
         "\n"
         "    | # | シンボル | 記載 | 実測 |\n"
         "    |---|---|---|---|\n"
         "    | 2 | `_is_bot_sender` | `a` | `b` |",
         "schema 違反行"),
        # 反転(reason変化): AC-ID の前置語や ID 列形は method セルの 3 形完全一致に外れるため line violation になる（`N/A` 不許可という結論以前に
        # schema 自体で block される）
        ("prefixed_ac_id_still_rejects_na",
         "| [AC-1] | n/a | 未実施 |",
         "schema 違反行"),
        # 反転(reason変化): AC-ID の前置語や ID 列形は method セルの 3 形完全一致に外れるため line violation になる（`N/A` 不許可という結論以前に
        # schema 自体で block される）
        ("prefixed_ac_id_in_id_column_form_rejects_na",
         "| V-01 | 手動 AC-1 | N/A | x |",
         "schema 違反行"),
        # 反転(reason変化): `\|` で結合したセルは分割後のセル数が 4 に一致しないため line violation になる（design.md §5「`\|`で結合したpending」→
        # reason 変化）
        ("escaped_pipe_cannot_hide_pending",
         "| method=ac:AC-1 \\| pending | pass | log |",
         "schema 違反行"),
        # 反転(reason変化): 行全体をコードスパンで包むと `|` 始まりでなくなるため line violation になる（D3 でコードスパン内 `|` 保護も廃止済み）
        ("code_span_wrapped_row_cannot_hide_pending",
         "- `| method=ac:AC-1 | pending | log |`",
         "schema 違反行"),
        # 反転(reason変化): 識別子セルの前置語・単セル化・trailing 語のいずれも method セルの 3 形完全一致から外れるため line violation
        # になる（識別子推定という概念が新文法に無い）
        ("method_label_without_identifier_is_still_a_verification_row",
         "| method=ac:AC-1 | pass | log |\n"
         "- method=受入確認 | 未実施 | -",
         "schema 違反行"),
        # 反転(reason変化): 識別子セルの前置語・単セル化・trailing 語のいずれも method セルの 3 形完全一致から外れるため line violation
        # になる（識別子推定という概念が新文法に無い）
        ("row_id_cell_with_trailing_words_is_still_a_verification_row",
         "| ac:AC-1 | pass | log |\n"
         "| V-01 手動確認 | 未実施 | - |",
         "schema 違反行"),
        # 反転(reason変化): 識別子セルの前置語・単セル化・trailing 語のいずれも method セルの 3 形完全一致から外れるため line violation
        # になる（識別子推定という概念が新文法に無い）
        ("row_id_prefix_list_form_is_still_a_verification_row",
         "| ac:AC-1 | pass | log |\n"
         "- ROW-3 の再実行 | 未実施 | log",
         "schema 違反行"),
        # 反転(reason変化): 引用記号 `>` を伴う行は §1.2 手順 2「`|` で始まる」に反するため line violation になる（design.md §5「引用行」→
        # violation）
        ("blockquoted_table_row_is_checked",
         "| method=ac:AC-9 | pass | e | n |\n"
         "> | method=ac:AC-1 | pending | 未実施 |",
         "schema 違反行"),
        # 反転(reason変化): 引用記号 `>` を伴う行は §1.2 手順 2「`|` で始まる」に反するため line violation になる（design.md §5「引用行」→
        # violation）
        ("blockquoted_list_row_is_checked",
         "| method=ac:AC-9 | pass | e | n |\n"
         "> - method=ac:AC-1 | fail | 3 件残",
         "schema 違反行"),
        # 反転(reason変化): 引用記号 `>` を伴う行は §1.2 手順 2「`|` で始まる」に反するため line violation になる（design.md §5「引用行」→
        # violation）
        ("nested_blockquote_row_is_checked",
         "| method=ac:AC-9 | pass | e | n |\n"
         ">> | method=ac:AC-1 | pending | 未実施 |",
         "schema 違反行"),
    ]

    def test_table_and_mixed_forms_that_must_block_as_pending_or_fail(self):
        # T-5 (AC-11): 閉じた文法では data_row が非装飾の 4 セル完全一致に限られる
        # ため、この 98 → 97 件（1 件は allow へ反転して移動。
        # `_ALLOW_CASES` の `notes_only_status_word_is_detected` 参照）の
        # 大半は decision=block のまま reason だけ「未完了/失敗」→
        # 「schema 違反行」に変わる。絶対期待値の判定表として reason を
        # 3 要素目に持たせ、1 case ずつ judged した結果を pin する
        # （design.md § 6「絶対期待値の判定表」）。
        for name, body, expected_reason in self._BLOCK_PENDING_CASES:
            with self.subTest(case=name):
                decision, reason = _judge_in_process(body)
                self.assertEqual(decision, "block", f"case={name} reason={reason}")
                self.assertIn(expected_reason, reason, f"case={name}")

    def test_header_row_is_excluded_from_the_pending_count(self):
        # header 行が data 行に計上されるなら「2 件」になるはずだが、
        # 実際に data 行になるのは pending 行 1 件だけ（AC-1 の header 除外の帰結）。
        _code, out, _err = _run_verification(
            "| method | status | evidence | notes |\n"
            "| method=ac:AC-1 | pending | evidence | notes |"
        )
        payload = _payload(out)
        self.assertEqual(payload["decision"], "block")
        self.assertIn("1 件", payload["reason"])
        # 件数だけだと「header を数えたうえで pending 行を落とした」形でも 1 件になる。
        # 列挙された違反行の実物まで pin して、計上されたのが pending 行であることを固定する。
        self.assertIn("| method=ac:AC-1 | pending | evidence | notes |", payload["reason"])
        self.assertNotIn("| method | status | evidence | notes |", payload["reason"])

    def test_refactor_checkpoint_na_is_a_schema_violation(self):
        # tasklist Step 6 / design.md § 6「絶対期待値の判定表」: § 1.3 の
        # 表は `method=refactor-checkpoint` 行に使える status を
        # pending/pass/fail に限る（`n/a`/`unsupported` は不可）。
        # `_STATUS_VALUES_BY_METHOD_KIND` が単一集合（例: 5 値すべてを
        # 全 method に許す）へ退化すると、この case は誤って data 行として
        # 受理され block しなくなる ―— その退化を検出する判別力を持つ。
        _code, out, _err = _run_verification(
            "| method=refactor-checkpoint | n/a | evidence | notes |"
        )
        payload = _payload(out)
        self.assertEqual(payload["decision"], "block", f"out={out}")
        self.assertIn("schema 違反行", payload["reason"])

    def test_ac_unsupported_is_a_schema_violation(self):
        # tasklist Step 6 / design.md § 6: `method=ac:*` 行に使える status も
        # pending/pass/fail に限る（`unsupported` は security_evidence 専用）。
        # 同じ退化判別力を ac 行側でも固定する。
        _code, out, _err = _run_verification(
            "| method=ac:AC-1 | unsupported | evidence | notes |"
        )
        payload = _payload(out)
        self.assertEqual(payload["decision"], "block", f"out={out}")
        self.assertIn("schema 違反行", payload["reason"])

    _NO_ROWS_CASES = [
        # 維持: header + separator のみで data 行が無いため §1.1 の空節扱いのまま「検証行がありません」で不変
        ("canonical_header_and_separator_only",
         "| method | status | evidence | notes |\n|---|---|---|---|",
         "検証行がありません"),
        # 反転(reason変化): `ROW-ID` 列を含む header は §1.1 の 4 セル `method|status|evidence|notes` に一致しないため header
        # として認識されず、5 セル構成の全行が line violation になる
        ("row_id_header_and_separator_only",
         "| ROW-ID | method | status | evidence | notes |\n|---|---|---|---|---|",
         "schema 違反行"),
        # 反転(reason変化): header は §1.1 の 4 語完全一致でのみ認められるため、非標準語彙・列欠落の header は header として扱われず line violation
        # になる
        ("non_canonical_header_only",
         "| method | ステータス | evidence | notes |",
         "schema 違反行"),
        # 反転(reason変化): header は §1.1 の 4 語完全一致でのみ認められるため、非標準語彙・列欠落の header は header として扱われず line violation
        # になる
        ("column_dropped_header_only",
         "| method |",
         "schema 違反行"),
        # 反転(reason変化): `- なし` は §1.1 の empty_marker と完全一致する必要があり、`| なし |` という表セル形は一致しないため line violation になる
        ("nashi_cell_only",
         "| なし |",
         "schema 違反行"),
        # 反転(reason変化): 空セルのみの行は separator（`:?-+:?`）にも data_row にも一致しないため line violation になる
        ("empty_cell_only",
         "| |",
         "schema 違反行"),
        # 反転(reason変化): 2 列の separator は §1.1 の 4 セル separator に一致しないため line violation になる（design.md
        # §5「separator のみ（2列）」→ reason 変化）
        ("aligned_separator_only",
         "|:---|:---|",
         "schema 違反行"),
        # 反転(reason変化): 補助表（method 値域外）は §1.1 の data_row 3 形いずれにも一致しないため line violation になる（design.md
        # §5「補助表のみ」→ reason 変化）
        ("auxiliary_table_only",
         "| # | severity | 内容 | 対応 |\n"
         "|---|---|---|---|\n"
         "| H-1 | High | x | 対応済み |",
         "schema 違反行"),
    ]

    def test_forms_with_zero_data_rows_block_as_no_rows_without_raising(self):
        # T-5 (AC-9 / AC-11): 「data 行 0 件」の言い方は §1.1 の空節相当（header/
        # separator のみ・空節）だけが「検証行がありません」を維持する。それ以外の
        # 7 件は、旧実装が「data 行として計上しない（=0 件扱い）」に落としていた
        # 非 canonical な header/separator/cell が、新文法では単独の schema
        # 違反行として計上されるため reason が変わる（decision は block のまま）。
        for name, body, expected_reason in self._NO_ROWS_CASES:
            with self.subTest(case=name):
                decision, reason = _judge_in_process(body)
                self.assertEqual(decision, "block", f"case={name} reason={reason}")
                self.assertIn(expected_reason, reason, f"case={name}")


class TableVerificationRowClassificationAllowPathTests(unittest.TestCase):
    """done guard Check 2: 表行の status セル分類（allow 方向。AC-6）。

    false positive 防止（全 pass で block しないこと）と、fail-closed へ倒した後も
    canonical schema / 凡例でない散文 list が過剰 block されないことを pin する。
    判別不能な status セルは PR #56 の独立レビュー R1 を受けて「不可視」から
    「未検証（block）」へ反転したため、旧 known-gap の pin は block 側へ移した。

    T-5 (AC-11): 閉じた文法では data_row が非装飾の 4 セル完全一致に限られる
    ため、旧 `_ALLOW_CASES`（43 件）のうち 35 件は allow → block へ反転する
    （非 canonical な緩い受理を新文法が許さなくなったため）。1 case ずつ
    design.md § 5 を根拠に判断し、以下の 2 バケツへ仕分けた:
    - `_ALLOW_CASES`（9 件 = 元の 8 件 + block 側から反転で移ってきた
      `notes_only_status_word_is_detected` 1 件）: 引き続き allow のまま
    - `_FORMERLY_ALLOWED_NOW_BLOCKED_CASES`（35 件）: allow → block に反転。
      判断根拠は各 case の直前コメントを参照
    """

    _ALLOW_CASES = [
        # 維持: 完全な canonical 行（装飾なし）なので新文法でも data 行として受理され allow のまま
        ("table_all_pass",
         "| method=ac:AC-1 | pass | evidence | notes |"),
        # 維持: status 列は固定 2 列目のみを見るため、evidence 欄の `fail: 0` は判定に影響しない。canonical 行として受理され allow のまま
        ("headerless_table_evidence_summary_does_not_block",
         "| method=ac:AC-1 | pass | fail: 0 | - |"),
        # 維持: canonical な `method=security_evidence:` 行であり、evidence/notes 欄の AC 参照は判定対象外。data 行として受理され allow
        # のまま
        # T-9 (AC-9 第 5 形 / 2026-09-10): AC 検証行 0 件の節は block になったため canonical AC 行を 1 行足した
        # （この case が pin する性質は上記のとおりで、期待値 allow は不変）。元の入力（evidence 行のみ）が block へ
        # 反転したことは `test_verification_ac_row_required_contract.py` の `OriginalAllowFixtureNowBlocksTests` が固定する
        ("security_evidence_row_with_ac_reference_in_notes_allows",
         "| method | status | evidence | notes |\n"
         "|---|---|---|---|\n"
         "| method=security_evidence:sca | N/A | snyk 0 | AC-3 は依存追加なしのため対象外 |\n"
         "| method=ac:AC-1 | pass | evidence | notes |"),
        # 維持: canonical な `method=security_evidence:` 行であり、evidence/notes 欄の AC 参照は判定対象外。data 行として受理され allow
        # のまま
        # T-9 (AC-9 第 5 形 / 2026-09-10): AC 検証行 0 件の節は block になったため canonical AC 行を 1 行足した
        # （この case が pin する性質は上記のとおりで、期待値 allow は不変）。元の入力（evidence 行のみ）が block へ
        # 反転したことは `test_verification_ac_row_required_contract.py` の `OriginalAllowFixtureNowBlocksTests` が固定する
        ("security_evidence_row_with_ac_reference_in_evidence_allows",
         "| method | status | evidence | notes |\n"
         "|---|---|---|---|\n"
         "| method=security_evidence:sca | N/A | AC-2 に関連する依存なし | |\n"
         "| method=ac:AC-1 | pass | evidence | notes |"),
        # 維持: status 列は固定 2 列目（`pass`）のみで判定し、notes 欄の注記語は見ない。canonical 行として受理され allow のまま（design.md §5
        # 最下段「status 列以外のセルの pending/fail」→ allow は不変）
        ("annotated_pending_in_notes_with_resolved_pass_allows",
         "| method=ac:AC-1 | pass | log | pending（前回）を解消 |"),
        # 維持: status 列は固定 2 列目（`pass`）のみで判定し、notes 欄の注記語は見ない。canonical 行として受理され allow のまま（design.md §5
        # 最下段「status 列以外のセルの pending/fail」→ allow は不変）
        ("annotated_fail_zero_in_notes_allows",
         "| method=ac:AC-1 | pass | log | fail(0) |"),
        # 維持: `method=security_evidence:` prefix 付きの canonical 行であり N/A は §1.3 の許容値どおり。data 行として受理され allow のまま
        # T-9 (AC-9 第 5 形 / 2026-09-10): AC 検証行 0 件の節は block になったため canonical AC 行を 1 行足した
        # （この case が pin する性質は上記のとおりで、期待値 allow は不変）。元の入力（evidence 行のみ）が block へ
        # 反転したことは `test_verification_ac_row_required_contract.py` の
        # `AcRowRequiredBlocksTests.test_security_evidence_na_table_blocks` が固定する
        ("method_prefixed_security_evidence_na",
         "| method | status | evidence | notes |\n"
         "|---|---|---|---|\n"
         "| method=security_evidence:sca | N/A | | dependencies 変更なし |\n"
         "| method=ac:AC-1 | pass | evidence | notes |"),
        # 維持: `:---` 形の aligned separator も §1.1 の separator 定義（`:?-+:?`）に一致し、続く data 行も canonical。allow のまま
        ("canonical_header_and_aligned_separator_are_not_data_rows",
         "| method | status | evidence | notes |\n"
         "|:---|:---|:---|:---|\n"
         "| method=ac:AC-1 | pass | evidence | notes |"),
        # 反転(block→done): status 列は固定 2 列目のみを見るため、notes 欄にリテラル `pending` があっても判定に影響しない（design.md §5 最下段「status
        # 列以外のセルにリテラルの pending/fail」→ **block→done** の唯一のクラス）。旧実装は `_has_unfinished_status`
        # が全セルを列位置非依存で走査していたため notes 欄の `pending` も検出していたが、新文法は status 列だけを見るためこの 1 件だけ allow へ反転する
        ("notes_only_status_word_is_detected",
         "| method=ac:AC-1 | pass | ok | pending |"),
    ]

    def test_forms_that_must_not_block(self):
        for name, body in self._ALLOW_CASES:
            with self.subTest(case=name):
                decision, reason = _judge_in_process(body)
                self.assertEqual(decision, "allow", f"case={name} reason={reason}")

    _FORMERLY_ALLOWED_NOW_BLOCKED_CASES = [
        # T-5 (AC-11): 旧 `_ALLOW_CASES` にあった 43 件のうち 35 件は、旧実装が
        # 「非 canonical でも status 語を検出できれば通す」という緩い受理をして
        # いたために allow だった。新文法は data_row の完全一致（§1.1）以外を
        # 一律 line violation とするため、この 35 件は block へ反転する。ケース名は
        # 変えず、判断根拠を各行に残したうえでこちらのバケツへ移した。
        # 反転(done→block): list 行は data_row（`|` 始まり）に一致しないため、装飾がなくても line violation になる（design.md §5「list 行」→
        # violation）
        ("list_all_pass",
         "- method=ac:AC-1 | pass | evidence | notes"),
        # 反転(done→block): table 側の canonical 行は allow のままだが、list 行は data_row に一致せず line violation になるため全体としては
        # block へ反転する
        ("mixed_all_pass",
         "- method=ac:AC-2 | pass | evidence | notes\n"
         "| method=ac:AC-1 | pass | evidence | notes |"),
        # 反転(done→block): `security_evidence:` 単体（`method=` prefix 無し）は §1.1 の method セル 3 形いずれにも一致しないため line
        # violation になる（design.md §1.6「`method=security_evidence:` prefix 必須」）
        ("security_evidence_na",
         "| security_evidence:sca | N/A | | dependencies 変更なし |"),
        # 反転(done→block): `security_evidence:` 単体（`method=` prefix 無し）は §1.1 の method セル 3 形いずれにも一致しないため line
        # violation になる（design.md §1.6「`method=security_evidence:` prefix 必須」）
        ("security_evidence_unsupported",
         "| security_evidence:iac | unsupported | | snyk IaC 未対応 |"),
        # 反転(done→block): 散文中の `|` は行が `|` で始まらない限り data_row と誤認されないはずだが、この例の 2 行目は `**注**:`/`- 実行コマンド` で始まり
        # §1.1 の列挙（blank/`- なし`/header/separator/data_row）のどれにも一致しないため line violation になる
        ("prose_note_with_pipes_does_not_block",
         "| method | status | evidence | notes |\n"
         "|---|---|---|---|\n"
         "| ac:AC-1 | pass | ok | - |\n"
         "**注**: 検証は `grep foo | sort | uniq` の出力で確認した"),
        # 反転(done→block): `- ` で始まる list 行は §1.1 の data_row（`|` 始まり）に一致しないため、散文であっても line violation
        # になる（design.md §5「list 行」→ violation。「散文だから除外」という判定は新文法に無い）
        ("prose_list_label_with_pipes_does_not_block",
         "| ac:AC-1 | pass | ok | - |\n"
         "- 補足: 手順は A | B | C の順"),
        # 反転(done→block): `V-01` のような ROW-ID セルを含む行は §1.1 の 3 形いずれの method パターンにも一致しないため line violation になる
        ("row_id_table_without_header_all_pass",
         "| V-01 | ac:AC-1 | pass | npm test |"),
        # 反転(done→block): 日本語 header は §1.1 の 4 語（method/status/evidence/notes）完全一致でのみ header と認められる語彙に含まれないため
        # header として扱われず、後続の非 canonical data 行も line violation になる（design.md §5「日本語 header 表」→ violation）
        ("japanese_header_row_id_table_all_pass",
         "| ROW | 検証方法 | ステータス | 実測 |\n"
         "|---|---|---|---|\n"
         "| V-1 | ac:AC-1 | pass | npm test |"),
        # 反転(done→block): 2 つ目の節見出し内にある `ROW | method | status | evidence` header は §1.1 の 4 語 header
        # と一致しない（`ROW` 列が余分）ため、後続の data 行が header 未確定のまま line violation になる。列束縛のリセットという概念自体も新文法には無い
        ("consecutive_verification_sections_reset_block_state",
         "| method | status | evidence | notes |\n"
         "|---|---|---|---|\n"
         "| ac:AC-1 | pass | ok | - |\n"
         "## Verification\n"
         "| ROW | method | status | evidence |\n"
         "|---|---|---|---|\n"
         "| 1 | ac:AC-2 | pass | ok |"),
        # 反転(done→block): notes 欄に status 語（`fail: 0`/`pending: なし`）を書くこと自体は許容されるはずだが、この例の method セルが `AC-1:
        # a` というラベル形で §1.1 の 3 形いずれにも一致しないため line violation になる
        ("notes_with_annotated_status_word_does_not_block",
         "| method | status | evidence | notes |\n"
         "|---|---|---|---|\n"
         "| AC-1: a | pass | ok | fail: 0 |"),
        # 反転(done→block): notes 欄に status 語（`fail: 0`/`pending: なし`）を書くこと自体は許容されるはずだが、この例の method セルが `AC-1:
        # a` というラベル形で §1.1 の 3 形いずれにも一致しないため line violation になる
        ("notes_with_pending_summary_does_not_block",
         "| method | status | evidence | notes |\n"
         "|---|---|---|---|\n"
         "| AC-1: a | pass | ok | pending: なし |"),
        # 反転(done→block): 日本語 header は §1.1 の 4 語（method/status/evidence/notes）完全一致でのみ header と認められる語彙に含まれないため
        # header として扱われず、後続の非 canonical data 行も line violation になる（design.md §5「日本語 header 表」→ violation）
        ("japanese_only_header_resolves_status_column",
         "| 判定 | 検証方法 | 証跡 |\n"
         "|---|---|---|\n"
         "| pass | ac:AC-1 | 手動 |"),
        # 反転(done→block): `status=` ラベルは §1.2 の正規化 5 種に無いため除去されず、status セルが許容値と完全一致しなくなり line violation
        # になる（design.md §5「status=ラベル形」→ violation）
        ("status_labelled_pass_list_row",
         "- method=ac:AC-1 | status=pass | evidence=`pytest -q` | notes=-"),
        # 反転(done→block): `status=` ラベルは §1.2 の正規化 5 種に無いため除去されず、status セルが許容値と完全一致しなくなり line violation
        # になる（design.md §5「status=ラベル形」→ violation）
        ("status_labelled_pass_table_row",
         "| method=ac:AC-1 | status=pass | evidence=x | notes=- |"),
        # 反転(done→block): header 無し表の先頭行を header として消費する規則も、evidence 列を status として誤読する経路も新文法には無い（列位置は固定）。非
        # canonical な行は line violation になる
        ("headerless_list_evidence_summary_does_not_block",
         "- method=ac:AC-1 | pass | fail: 0 | -"),
        # 反転(done→block): 行全体をコードスパンで包むと `|` 始まりでなくなるため line violation になる（D3 でコードスパン内 `|` 保護も廃止済み）
        ("code_span_pipes_do_not_split_cells",
         "- AC-13: `rg \"AUTO_REVIEW_\" agent-runtime/` が 0 件 / `rg X | sort`"),
        # 反転(done→block): 補助表は method 値域外のため line violation になる。「後続の表を巻き込む/巻き込まない」という表ブロック単位の概念自体が新文法に無い
        ("auxiliary_table_prose_mentioning_ac_id_does_not_block",
         "| method=ac:AC-1 | pass | e | n |\n"
         "\n"
         "| # | 変異 | 実測 |\n"
         "|---|---|---|\n"
         "| MUT-H | spec の AC-4 行からだけ削除 | 1 failed |"),
        # 反転(done→block): 散文中の `|` は行が `|` で始まらない限り data_row と誤認されないはずだが、この例の 2 行目は `**注**:`/`- 実行コマンド` で始まり
        # §1.1 の列挙（blank/`- なし`/header/separator/data_row）のどれにも一致しないため line violation になる
        ("prose_note_with_code_span_pipes_does_not_block",
         "| ac:AC-1 | pass | ok | - |\n"
         "- 実行コマンド `cat a | grep b | wc -l` を使用"),
        # 反転(done→block): `- ` で始まる list 行は §1.1 の data_row（`|` 始まり）に一致しないため、散文であっても line violation
        # になる（design.md §5「list 行」→ violation。「散文だから除外」という判定は新文法に無い）
        ("prose_list_without_colon_does_not_block",
         "| ac:AC-1 | pass | ok | - |\n"
         "- 補足 A | B | C"),
        # 反転(done→block): header に余分な列（`#`）が付くと §1.1 の 4 語完全一致から外れ header と認識されない。後続の 5 セル data 行も 4 セル分割に失敗し
        # line violation になる
        ("header_with_extra_columns_is_still_header",
         "| # | method | status | evidence |\n"
         "|---|---|---|---|\n"
         "| 1 | ac:AC-1 | pass | ok |"),
        # 反転(done→block): header に `date` 列が付くと §1.1 の 4 語完全一致から外れ header と認識されない。後続の 5 セル data 行も line
        # violation になる
        ("header_with_trailing_date_column_is_still_header",
         "| method | status | evidence | notes | date |\n"
         "|---|---|---|---|---|\n"
         "| ac:AC-1 | pass | x | - | 9/7 |"),
        # 反転(done→block): 2 行目の `codebase-health` は method セルが §1.1 の 3 形いずれにも一致しないため line violation になる（1 行目の
        # canonical AC 行は data 行のまま）
        ("gate_record_row_with_na_allows",
         "| method | status | evidence | notes |\n"
         "|---|---|---|---|\n"
         "| method=ac:AC-1 | pass | npm test | - |\n"
         "| codebase-health | N/A | script | medium 1 件 no-action |"),
        # 反転(done→block): list 行（`- refactor-checkpoint | status: N/A | e | -`）は `|` 始まりでなく、かつ `status:`
        # ラベルも正規化対象外のため line violation になる
        ("checkpoint_row_with_na_list_allows",
         "- refactor-checkpoint | status: N/A | e | -"),
        # 反転(done→block): `- pending: 0 件` 等の list 行は `|` 始まりの data_row に一致しないため line violation になる（0
        # 件宣言という意味論を読む規則自体が新文法には無い）
        ("zero_count_summary_list_lines_do_not_block",
         "| method | status | evidence |\n"
         "|---|---|---|\n"
         "| method=ac:AC-1 | pass | a |\n"
         "\n"
         "- pending: 0 件\n"
         "- fail: 0 件"),
        # 反転(done→block): list 行（`- method=ac:AC-2 | pass | log`）は data_row に一致しないため line violation
        # になる。列束縛の非波及という概念自体が新文法には無い
        ("table_header_binding_does_not_leak_into_following_list_rows",
         "| ROW | method | status | notes |\n"
         "|---|---|---|---|\n"
         "| V-01 | ac:AC-1 | pass | log |\n"
         "- method=ac:AC-2 | pass | log"),
        # 反転(done→block): `AC-01 | test | status | ...` のような ID 列形は method セルの 3 形いずれにも一致しないため line violation
        # になる
        ("id_column_short_form_pass_allows",
         "| AC-1 | pass | log |"),
        # 反転(done→block): `V-01 | pass | log` は method セルが `|` 直後に無く 3 形いずれにも一致しないため line violation になる
        ("row_id_short_form_pass_allows",
         "| V-01 | pass | log |"),
        # 反転(done→block): status 列は固定 2 列目のみで判定するため、0 列目に status 語を置く「status 先頭列」形はどちらの行も method セルが 3 形に一致せず
        # line violation になる
        ("status_first_column_all_pass_allows",
         "| pass | ac:AC-1 | log |\n"
         "| pass | ac:AC-2 | log |"),
        # 反転(done→block): `AC-01 | test | status | ...` のような ID 列形は method セルの 3 形いずれにも一致しないため line violation
        # になる
        ("id_column_list_form_pass_allows",
         "- 許容 status: `pending`, `pass`, `fail`\n"
         "- AC-01 | test | pass | evidence | notes"),
        # 反転(done→block): インデントされた入れ子 list 行は `|` 始まりでないため line violation になる（design.md §5「インデント行」→
        # violation。無条件検出という旧 ADR 不変条件 1 はもう適用されない）
        ("indented_nested_list_status_pass_allows",
         "- `AC1`\n"
         "  - method: 手動確認\n"
         "  - status: pass\n"
         "| method=ac:AC-1 | pass | e |"),
        # 反転(done→block): `method:` のようなコロン付きラベルは §1.1 の method セル（`method=` イコール形のみ）に一致しないため line violation
        # になる（design.md §5「`method:`コロン形」→ violation）
        ("method_colon_labelled_security_evidence_na",
         "| method: security_evidence:sca | N/A | | 依存変更なし |"),
        # 反転(done→block): list 行（`- security_evidence | status: N/A | evidence: auth/authz`）は `|`
        # 始まりでなく、method セルも `method=security_evidence:` の形に一致しないため line violation になる
        ("list_security_evidence_na_allows",
         "- security_evidence | status: N/A | evidence: auth/authz"),
        # 反転(done→block): list 行は `|` 始まりの data_row に一致しないため、status セルの有無に関わらず line violation になる
        ("list_prose_without_status_cell_is_not_pending",
         "- method=ac:AC-1 | pass | evidence | pending を解消済み"),
        # 反転(done→block): `\|` で結合したセルは分割後のセル数が 4 に一致しないため line violation になる（design.md §5「`\|`で結合したpending」→
        # reason 変化）
        ("escaped_pipe_left_of_status_column_does_not_shift_cells",
         "| method | status | evidence | notes |\n"
         "|---|---|---|---|\n"
         "| method=ac:A \\| B | pass | e | n |"),
        # 反転(done→block): list 行はセル数の閾値に関わらず `|` 始まりの data_row に一致しないため line violation
        # になる（セル数閾値という概念自体が新文法には無い）
        ("prose_list_below_cell_threshold_is_not_status_checked",
         "- method=ac:AC-1 | pass | evidence | notes\n"
         "- AC-1 は目視で確認した"),
    ]

    def test_forms_that_used_to_pass_now_block(self):
        """反転(done→block): design.md §1.1/§1.2 の closure により、旧実装が
        許容していた非 canonical な allow 経路が一律 schema 違反へ倒れることを pin する。
        （AC-11 の絶対期待値判定表。`_ALLOW_CASES` から反転した 35 件はここに集約する）
        """
        for name, body in self._FORMERLY_ALLOWED_NOW_BLOCKED_CASES:
            with self.subTest(case=name):
                decision, reason = _judge_in_process(body)
                self.assertEqual(decision, "block", f"case={name} reason={reason}")
                self.assertIn("schema 違反行", reason, f"case={name}")


class LabelClassificationInvarianceTests(unittest.TestCase):
    """tasklist Step 7 / design.md § 6「ラベル分類の不変性テスト」（★ R3 / AC-8 の代替 guardrail）。

    `_labeled_violation_line()`（D5 の提示ラベル）は判定に一切使わない
    “表示専用” の分類だと ADR-8 が宣言しているが、宣言だけでは退行を検知
    できない。この分類関数の戻り値を**全行同一ラベルに固定**する mutation を
    当てても、AC-11 の各 case の decision と違反件数（`line` 種別）が
    **全件不変**であり、赤くなるのは文言 pin（`test_verification_block_message_contract.py`
    の (d) ラベル pin）だけであることを固定する。
    """

    @staticmethod
    def _all_case_bodies() -> list[tuple[str, str]]:
        bodies: list[tuple[str, str]] = []
        for name, body, _reason in TableVerificationRowClassificationTests._BLOCK_PENDING_CASES:
            bodies.append((name, body))
        for name, body, _reason in TableVerificationRowClassificationTests._NO_ROWS_CASES:
            bodies.append((name, body))
        for name, body in TableVerificationRowClassificationAllowPathTests._ALLOW_CASES:
            bodies.append((name, body))
        for name, body in (
            TableVerificationRowClassificationAllowPathTests._FORMERLY_ALLOWED_NOW_BLOCKED_CASES
        ):
            bodies.append((name, body))
        return bodies

    @staticmethod
    def _run_in_process(hook, body: str) -> tuple[str, int]:
        reason_list, violations = _scan_reasons(hook, body)
        decision = "block" if reason_list else "allow"
        line_violation_count = sum(1 for kind, _payload in violations if kind == "line")
        return decision, line_violation_count

    def test_label_classification_mutation_does_not_change_decision_or_count(self):
        hook = load_plugin_module("hooks/scripts/gdd_stop_hook.py")
        cases = self._all_case_bodies()
        # 下の比較が空で通らないようにする。件数は固定しない
        self.assertTrue(cases, "AC-11 の case が 1 件も無い")

        baseline = {name: self._run_in_process(hook, body) for name, body in cases}

        forced_label = "未完了の可能性がある検証行 — Notes へ移さず canonical 表行へ書き直す"

        def _forced_labeled_violation_line(raw: str) -> str:
            safe = hook.safe_for_output(raw)[:80]
            return f"  {safe}  [{forced_label}]"

        with mock.patch.object(
            hook, "_labeled_violation_line", side_effect=_forced_labeled_violation_line
        ):
            mutated = {name: self._run_in_process(hook, body) for name, body in cases}

        for name, _body in cases:
            with self.subTest(case=name):
                self.assertEqual(
                    baseline[name],
                    mutated[name],
                    f"case={name}: ラベル分類の mutation で (decision, line 違反件数) が変わった"
                    "（判定に使われていないはずのラベル分類が、実際には受理・件数に影響している）",
                )


class CaseTableEntryPointTests(unittest.TestCase):
    """表のケースを判定関数で回す前提（hook の入口でも同じ判定・理由になる）を、表ごとに固定する。

    表の全ケースを hook の起動で回すとケースごとに hook の起動の分だけ時間がかかるため、全ケースは
    `_judge_in_process` で見て、入口を通すのは各表の先頭の 1 ケースだけにする。
    """

    def test_first_case_of_each_table_matches_the_hook_entry_point(self):
        bodies = [
            TableVerificationRowClassificationTests._BLOCK_PENDING_CASES[0][1],
            TableVerificationRowClassificationTests._NO_ROWS_CASES[0][1],
            TableVerificationRowClassificationAllowPathTests._ALLOW_CASES[0][1],
            TableVerificationRowClassificationAllowPathTests._FORMERLY_ALLOWED_NOW_BLOCKED_CASES[0][1],
        ]
        for body in bodies:
            with self.subTest(body=body):
                decision, reason = _judge_in_process(body)
                code, out, err = _run_verification(body)
                if decision == "allow":
                    self.assertEqual(out.strip(), "", f"out={out} err={err}")
                    self.assertEqual(code, 0, f"out={out} err={err}")
                else:
                    payload = _payload(out)
                    self.assertEqual(payload["decision"], "block", f"out={out} err={err}")
                    self.assertIn(reason, payload["reason"])


class VerificationNoRowsMessageTests(unittest.TestCase):
    """ADR-7: 「検証行がありません」の本文とヒントが、非 schema 表の存在を示すこと。

    guard 自身の回復ヒントが旧文言のままだと、非 schema 表を直さずに list の pass 行を
    1 行足すだけで ALLOW に転じる経路（S-B3 の受容経路）へ実装者を誘導してしまう
    （Round 3 security review Medium-3）。本文とヒントに status セルの説明を追記しても、
    他ファイルが部分一致で依存している「検証行がありません」が残ることも併せて pin する。
    """

    def test_no_rows_message_mentions_status_cell_and_rewrite_hint(self):
        # 反転: design.md § 5「日本語 header 表 … → header は列名 4 語のみ →
        # violation」/ AC-9 が正本。旧 fixture の `| method | ステータス |
        # evidence | notes |` は、旧実装の緩い header 語彙判定では「header の
        # み（0 データ行）」に落ちていたが、新文法の `header` は §1.1 の 4 語
        # （method/status/evidence/notes）の ASCII 完全一致でのみ認識される。
        # `ステータス`（日本語）は語彙に含まれないため、この行は header にも
        # data_row にも一致せず単なる列挙外の行 = schema 違反行になる
        # （AC-9 の「検証行ゼロ系」ではなく「列挙外の行」側）。
        # 本テストの本来の目的（ADR-7 / Round 3 security review Medium-3:
        # 「検証行がありません」メッセージが status セル説明と書き直しヒントを
        # 含むこと）を維持するため、fixture を canonical ASCII header 1 行
        # （データ行 0 件の正真の「header のみ」）に差し替える。
        # あわせて「書き直して」→「書き直しが唯一の回復手順です」という
        # T-4 承認済みの文言変更に assert を追従させる。
        _code, out, err = _run_verification(
            "| method | status | evidence | notes |"
        )
        payload = _payload(out)
        self.assertEqual(payload["decision"], "block", f"out={out}\nerr={err}")
        self.assertIn("検証行がありません", payload["reason"])
        self.assertIn("status セル", payload["reason"])
        self.assertIn("pending", payload["reason"])
        # PR #65 review（2026-09-11）で反転: header のみの節は AC 検証行 0 件で、解除条件は
        # `method=ac:` 行の追加。「書き直しが唯一の回復手順」は解除条件と矛盾するため出さない
        # （schema 違反のときだけ出す）。代わりに AC 行の追加案内を pin する
        self.assertNotIn("唯一の回復手順", payload["reason"])
        self.assertIn("AC 検証行なし → `method=ac:", payload["reason"])

    def test_japanese_header_is_a_schema_violation_not_zero_rows(self):
        # 反転: 上のテストから切り出した「非 ASCII header は schema 違反行に
        # なる」側の主張（design.md § 5「日本語 header 表」/ AC-9）。
        _code, out, err = _run_verification(
            "| method | ステータス | evidence | notes |"
        )
        payload = _payload(out)
        self.assertEqual(payload["decision"], "block", f"out={out}\nerr={err}")
        self.assertIn("schema 違反行", payload["reason"])
        self.assertNotIn("検証行がありません", payload["reason"])


class BoundVerificationCheckTests(unittest.TestCase):
    """CT-3 / Check 2: bind 済み steering の Verification 不備は従来どおり block する。"""

    def test_bound_steering_without_verification_section_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = _make_two_worktree_fixture(Path(tmp))
            (_steering(wtB, _TARGET_SLUG) / "tasklist.md").write_text(
                _NO_VERIFICATION_TASKLIST, encoding="utf-8"
            )
            _bind(wtB)
            _code, out, err = _stop_done(wtB)
            payload = _payload(out)
            self.assertEqual(payload["decision"], "block", f"out={out}\nerr={err}")
            # **理由**まで固定する。Check 1（未完了タスク）で block していると
            # 「Check 2 が生きている」ことを一切測らないまま緑になる。
            self.assertIn("Verification セクションが存在しません", payload["reason"])
            self.assertNotIn("未完了タスク", payload["reason"])
            # **どの steering を見て block したか**（AC-1 との交差）
            self.assertIn(str(_steering(wtB, _TARGET_SLUG)), payload["reason"])
            self.assertNotIn(_FOREIGN_SLUG, out + err)


class BoundRouteInProgressCheckTests(unittest.TestCase):
    """CT-3 / Check 3: `Route In Progress != none` は従来どおり block する。"""

    def test_bound_steering_route_in_progress_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = _make_two_worktree_fixture(Path(tmp))
            (_steering(wtB, _TARGET_SLUG) / "state.md").write_text(
                _ROUTE_STATE, encoding="utf-8"
            )
            _bind(wtB)
            _code, out, err = _stop_done(wtB)
            payload = _payload(out)
            self.assertEqual(payload["decision"], "block", f"out={out}\nerr={err}")
            # 値まで出す（「何か残っている」ではなく「どの route が残っているか」）。
            self.assertIn(
                "Route In Progress=systematic_debugging", payload["reason"]
            )
            self.assertNotIn(_FOREIGN_SLUG, out + err)

    def test_route_in_progress_none_allows_done(self):
        """negative control: state.md がある**だけ**では block しない。

        これが無いと、上のテストは「state.md の存在で block する」実装でも緑になる。
        `_CLEAN_ROUTE_STATE`（＝ `state.md` を置く clean な形）を書くのは本ファイルで
        **このテストだけ**で、success path は `state.md` を置かない形にしてある。
        setup を分ける理由は `BoundDoneGuardSuccessPathTests` の docstring が正本。
        """
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = _make_two_worktree_fixture(Path(tmp))
            (_steering(wtB, _TARGET_SLUG) / "state.md").write_text(
                _CLEAN_ROUTE_STATE, encoding="utf-8"
            )
            _bind(wtB)
            code, out, err = _stop_done(wtB)
            # clean な `state.md` が**ある**状態でも「stdout 空 かつ exit 0」の連言まで
            # 固定する。block 文字列の非包含だけだと「`state.md` があるときだけ非 block の
            # 余計な stdout を出す」変異をどのテストも殺せない（impl-gate T-7 Attempt 2 の
            # advisory A-7）。非包含はこの連言に含まれる（空文字列に部分文字列は存在しない）
            # ため、増分 0 の pin として置かない。setup が success path と異なる
            # （あちらは `state.md` を置かない）ので構造的支配も生じない。
            # 実測は `.steering/<task>/tasklist.md` § Current Task § T-8 § A-7 の処置。
            self.assertEqual(out.strip(), "", f"out={out}\nerr={err}")
            self.assertEqual(code, 0, f"out={out}\nerr={err}")

    def test_foreign_worktree_route_in_progress_does_not_block(self):
        """他 worktree の `Route In Progress` 残存は block 理由にならない（AC-1 × Check 3）。

        Check 3 は tasklist とは別に `<steering>/state.md` を読む。その steering が
        bind 由来でないと、**自分の worktree を直しても解除できない block** が残る。
        wtA の tasklist は clean にして、wtA 側の欠陥を Route In Progress だけに絞る。
        """
        with tempfile.TemporaryDirectory() as tmp:
            wtA, wtB = _make_two_worktree_fixture(Path(tmp))
            (_steering(wtA, _FOREIGN_SLUG) / "tasklist.md").write_text(
                _CLEAN_TASKLIST, encoding="utf-8"
            )
            (_steering(wtA, _FOREIGN_SLUG) / "state.md").write_text(
                _ROUTE_STATE, encoding="utf-8"
            )
            _bind(wtB)
            _code, out, err = _stop_done(wtB)
            self.assertNotIn('"decision": "block"', out, f"out={out}\nerr={err}")
            self.assertNotIn("systematic_debugging", out + err)
            self.assertNotIn(_FOREIGN_SLUG, out + err)


class BoundDoneGuardSuccessPathTests(unittest.TestCase):
    """success path: 3 チェックすべて満たす bind 済み steering は done を通す。"""

    def test_clean_bound_steering_allows_done(self):
        """`state.md` を**置かない** clean な bind 済み steering（Check 3 は no-op）。

        `_CLEAN_ROUTE_STATE` を**ここでは書かない**のは意図的。書くと本テストの
        setup が `test_route_in_progress_none_allows_done` と同一になり、A-7 の
        assert 強化で両者の assert 集合も一致したため、**互いに支配し合う重複**に
        なる ―― 片方だけを殺す変異が原理的に存在しなくなる。setup を分けることで
        両方が load-bearing になる（実測は `.steering/<task>/tasklist.md`
        § Current Task § T-8 § A-7 の処置 の判別力マトリクスが正本）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = _make_two_worktree_fixture(Path(tmp))
            _bind(wtB)
            code, out, err = _stop_done(wtB)
            # 実測: bind 済みで 3 チェックすべて通ると stdout は**空**（exit 0）。
            # `gdd:bind-unresolved` の warn は unbound 経路だけのもので、ここに
            # 混ざると AC-2 の warn が「常時出る雑音」に退化する。
            self.assertEqual(out.strip(), "", f"out={out}\nerr={err}")
            self.assertEqual(code, 0, f"out={out}\nerr={err}")


if __name__ == "__main__":
    unittest.main()

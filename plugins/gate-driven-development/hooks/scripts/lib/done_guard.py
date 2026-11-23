"""tasklist.md の構造行を走査する done guard のヘルパー群と、state.md を読む Check 3。

`gdd_stop_hook.py` から切り出した。理由は挙動ではなく健全性で、hook 本体が
行数上限 1500 を超え、**1 行触るだけで pre-PR の Codebase Health Gate が
`gh pr create` を止める**状態だったため。挙動は変えていない。

`実装漏れ防止` / `hook-enforced` を含む block reason の組み立ては
`tests/checks/hooks.sh` の契約リテラルなので hook 本体に残してある。
"""
from __future__ import annotations

import re
from pathlib import Path

from lib.regular_file import read_regular_text
from lib.task_binding_resolve import safe_for_output
from lib.tasklist_parse import (
    NON_NEWLINE_LINE_BREAKS,
    ROUTE_IN_PROGRESS_PATTERN,
    _scan_fences,
    classify_task_line,
    route_in_progress_key_lines,
    route_value,
    select_route_in_progress,
    task_name,
)

# 正本: references/self-contained-contract.md の
# <!-- verification-grammar:begin --> 文法ブロック（design.md § 1.1 と同一テキスト）。
# method 種別ごとに status の許容集合が異なる（AC-1 (e)）
_AC_STATUS_VALUES = {"pending", "pass", "fail"}
_EVIDENCE_STATUS_VALUES = {"pending", "pass", "fail", "n/a", "unsupported"}
_STATUS_VALUES_BY_METHOD_KIND = {
    "ac": _AC_STATUS_VALUES,
    "security_evidence": _EVIDENCE_STATUS_VALUES,
    "refactor-checkpoint": _AC_STATUS_VALUES,
}
# 未完了を表す status 値（method 種別に依らず共通）。data 行の unfinished 計上に使う
_UNFINISHED_STATUS_VALUES = {"pending", "fail"}
# 文法ブロックの `ws`。**半角空白とタブだけ**（design.md § 1.2 手順 1 / セルレベル）。
# Python 既定の `str.strip()` は Unicode 空白全体（U+3000 全角空白 / U+00A0 NBSP /
# U+2028 …）を落とすため使わない。§ 5 は全角空白 padding を violation と定めており、
# 既定の `strip()` を使うと削除した `_CELL_TRIM_CHARS`（全角空白を含んでいた）の挙動が
# **別名で復活**して AC-8 第 2 条項に反する。
_WS = " \t"
# `- なし` は完全一致リテラル（design.md § 1.1 empty_marker / D2）。
_EMPTY_MARKER = "- なし"
# AC_ID / method セルの正本は文法ブロック（design.md § 1.1）。ここでの正規表現は
# 従属定義（§ 7 Ownership Matrix）。
# `\d` ではなく `[0-9]`: 文法ブロックの `DIGIT` は ASCII 数字であり、`\d` は Unicode の
# 十進数字（全角 `１` など）まで拾う。`str.strip()` / `str.lower()` と同型の
# 「Python 既定が正本より広い」面なので、ここでも ASCII に閉じる。
# 末尾は `$` ではなく `\Z`: `$` は末尾の改行 1 個を許すため、`method=ac:AC-1\n` が
# 完全一致として通る（`_SEPARATOR_CELL` は既に `\Z`）。
_AC_ID_CORE = r"AC-[A-Za-z]?[0-9]+(?:-(?:[0-9]+|[a-z]))?[a-z]?"
_METHOD_AC_RE = re.compile(r"^method=ac:(" + _AC_ID_CORE + r")\Z")
_METHOD_EVIDENCE_RE = re.compile(r"^method=security_evidence:([a-z][a-z0-9-]*)\Z")
_METHOD_REFACTOR_RE = re.compile(r"^method=refactor-checkpoint\Z")
_HEADER_CELLS = ("method", "status", "evidence", "notes")
_SEPARATOR_CELL = re.compile(r":?-+:?\Z")
# セル区切りの `|`。`\|` はエスケープなので区切りにしない（design.md § 1.2 手順 3）
_ESCAPED_PIPE = re.compile(r"(?<!\\)\|")
# method セル 3 形と、その method 種別が使う status 許容集合。data 行の判定は
# この 3 form を順に試すだけ（design.md § 1.1 の ac_row / evidence_row / refactor_row）
_METHOD_KIND_PATTERNS = (
    ("ac", _METHOD_AC_RE),
    ("security_evidence", _METHOD_EVIDENCE_RE),
    ("refactor-checkpoint", _METHOD_REFACTOR_RE),
)


# `str.splitlines()` は LF / CR 以外に次の文字でも行を分ける。閉じた文法の改行は LF / CR / CRLF
# だけ（`ws` にも改行にもしない）なので、これらを含む tasklist / state.md は行・節の境界を正しく数えられない。
# 行の途中の `U+2028## X` で `## Verification` 節が切れ、後ろの fail 行が節の外に出て done が
# 通っていた（独立レビュー R23 #1）。block 理由には文字そのものではなく U+XXXX 表記だけを載せる
_NON_NEWLINE_LINE_BREAKS = NON_NEWLINE_LINE_BREAKS
# 検査対象ファイル名 → 見出しの後ろに置く「なぜ止まるか」。tasklist.md の文言は一般化の前とバイト等価。
# state.md の文は被害だけを書く。「LF に置き換えると空として読まれる」のように結果まで書くと、
# block 理由そのものが Check 3 の non-none 判定を素通りさせる手順の開示になる（Issue #119 / D-28）
_LINE_BREAK_WHY_TEXT = {
    "tasklist.md": (
        "行の解析がこの文字で分割され、節の範囲や検証行を正しく数えられないため done を許可しません。"
        "該当文字を削除してください。"
        "通常の改行（LF）に置き換えると、後ろの行が別の節に移って検証行が `## Verification` の外に出ることがあります。"
    ),
    "state.md": (
        "行の解析がこの文字で分割され、remediation route の完了判定ができないため done を許可しません。"
        "該当文字を削除してください。"
        "通常の改行（LF）に置き換えると値が別行へ移り、`Route In Progress` の記録が壊れます。"
        "置き換えずに該当文字だけを削除し、1 行に戻してください。"
    ),
}


def _line_break_headline(filename: str) -> str:
    """block 理由の先頭に置く見出し。回復ヒント（`lib/done_block_message.py`）が行頭一致で見る。"""
    return f"{filename} に LF / CR 以外の行区切り文字"


_LINE_BREAK_HEADLINES = tuple(_line_break_headline(name) for name in _LINE_BREAK_WHY_TEXT)
_LINE_BREAK_HEADLINE_TASKLIST = _line_break_headline("tasklist.md")


def _line_break_char_error(text: str, filename: str) -> str:
    """LF / CR 以外の行区切り文字を含む `filename`（tasklist.md / state.md）の block 理由。含まなければ空文字列。

    見えない文字なので原文行番号（1 始まり・先頭 5 件）を示す。`read_text` の時点で CR / CRLF は
    LF になっているので `split("\\n")` で数える。LF への置き換えは勧めない: `U+2028## X` を LF に
    すると本物の見出しになり、後ろの fail 行が節の外に出て done が通る（impl-gate R21 M-1）
    """
    found = sorted({ch for ch in text if ch in _NON_NEWLINE_LINE_BREAKS})
    if not found:
        return ""
    labels = " / ".join(f"U+{ord(ch):04X}" for ch in found)
    line_numbers = [
        i for i, line in enumerate(text.split("\n"), start=1)
        if any(ch in _NON_NEWLINE_LINE_BREAKS for ch in line)
    ]
    more = f" ほか {len(line_numbers) - 5} 行" if len(line_numbers) > 5 else ""
    return (
        f"{_line_break_headline(filename)}（{labels}）が含まれています（行 {line_numbers[:5]}{more}）。"
        f"{_LINE_BREAK_WHY_TEXT[filename]}"
    )


# Check 3 が「行が無い」「最後の行を読めない」で止めるときの見出し。回復ヒント
# （`lib/done_block_message.py`）が行頭一致で見る
_ROUTE_MISSING_HEADLINE = "state.md に Route In Progress の行がありません"
_ROUTE_UNREADABLE_HEADLINE = "state.md の Route In Progress の最後の行から値を読めない"
_ROUTE_LINE_HEADLINES = (_ROUTE_MISSING_HEADLINE, _ROUTE_UNREADABLE_HEADLINE)
_STATE_FENCE_UNCLOSED_HEADLINE = "state.md の code fence が閉じていません"


def _route_in_progress_errors(tasklist_path: Path) -> list[str]:
    """Check 3: done 時点で Route In Progress が残っていないか。

    terminal 状態で non-none の Route In Progress は remediation 未完を意味する。
    state.md に LF / CR 以外の行区切り文字があれば、その理由だけを返して
    `select_route_in_progress()` へ進まない。行が誤分割されて値が空に化け、
    non-none の route を抱えたまま done が通っていた（fail-closed。Issue #119 / D-28）

    未閉の code fence があれば block する（独立-3 D4）。キー行（write guard の受理集合を含む）が
    1 本も無ければ block する（Tier 1 必須 field。崩れた書き方を見分けずに畳む）。最後のキー行が現在の行で、その値を読めなければ block する。
    前にある読める行が後ろの読めない行を隠して done が通っていた（独立-2 B1〜B3）
    """
    state_file = tasklist_path.parent / "state.md"
    try:
        state_text = read_regular_text(state_file)
    except OSError:  # FIFO・ディレクトリ・symlink のループを「無い」と読むと Check 3 を飛ばして done が通る
        return [f"state.md を通常のファイルとして読めないため done を許可しません: {safe_for_output(str(state_file))}"]
    if state_text is None:
        return []
    line_break_error = _line_break_char_error(state_text, "state.md")
    if line_break_error:
        return [line_break_error]
    if _scan_fences(state_text)[2] >= 0:
        # tasklist.md と同じく一律 block。閉じ忘れの後ろは記入例と現在値を区別できず、
        # 記入例の `none` が採られて done が通っていた（独立-3 D4）
        return [
            f"{_STATE_FENCE_UNCLOSED_HEADLINE}（``` / ~~~ の対応が取れていない）。"
            "記入例と現在の Route In Progress を区別できないため done を許可しません。"
        ]
    key_lines = route_in_progress_key_lines(state_text)
    if not key_lines:
        return [
            f"{_ROUTE_MISSING_HEADLINE}（必須 field）。"
            "remediation route の完了判定ができないため done を許可しません。"
        ]
    last = ROUTE_IN_PROGRESS_PATTERN.match(key_lines[-1])
    last_value = route_value(last.group(2)) if last else ""
    if not last_value:
        # 値が次の行にある・注記だけ・単独 CR・形が違う（` : x` など）。前の行の値で判定しない
        return [
            f"{_ROUTE_UNREADABLE_HEADLINE}ため、"
            "remediation route の完了判定ができず done を許可しません。"
        ]
    # 最後のキー行の値と reader の値の両方が none のときだけ通す。reader はコロン形を優先するので、
    # `: none` の後に `=<route>` を書くと reader だけが none を返す（独立-3 D1。reader は変えない）
    for value in (last_value, select_route_in_progress(state_text)):
        chosen = safe_for_output(value)
        # 値も **case-insensitive** に見る（H5-7）。field 名の照合は `re.IGNORECASE` なのに
        # 値比較だけ厳密で非対称だった ―― `None` / `NONE` が block していた。
        if chosen and chosen.lower() != "none":
            return [
                f"Route In Progress={chosen} が残っています。"
                "remediation route が完了していない可能性があります。"
                "Route In Progress=none にしてから done してください。"
            ]
    return []


def _scan_remaining_tasks(structural_lines: list[str]) -> tuple[list[str], list[str]]:
    """Check 1: Current Task / Pending Tasks に残っている行を集める。

    `(remaining, unexpected_content)` を返す。
    """
    section = ""
    remaining: list[str] = []
    unexpected_content: list[str] = []
    in_task_body = False
    for line in structural_lines:
        stripped = line.strip()
        if line.startswith("## Current Task"):
            section, in_task_body = "current", False
        elif line.startswith("## Pending Tasks"):
            section, in_task_body = "pending", False
        elif line.startswith("## Completed Tasks"):
            section, in_task_body = "completed", False
        elif line.startswith("## "):
            section, in_task_body = "", False
        elif section in ("current", "pending"):
            # "- なし" is the canonical empty marker — skip it
            if not stripped or stripped == "- なし":
                continue
            # **タスク行は行頭ぴったり**。インデントされた行は散文の例示か
            # indented code block で、tasklist の構造ではない。
            # 実測値と導出コマンドは `.steering/<task>/design.md § 論点 2c` が正本。
            #
            # 見るのは **先頭の空白だけ**。`line != stripped` にすると `strip()` が
            # 末尾も落とすので「末尾に空白があるだけの task 行」まで捨ててしまい、
            # しかも `unexpected_content` に計上される前に continue するため
            # **警告も出ない silent fail-open** になる（実測で確認した退行）。
            # 導出: tests/test_stop_hook_bind_resolution_contract.py の
            # IndentedLineTests が両方向を pin する。
            if line.lstrip() != line:
                continue
            # 受理面は lib/tasklist_parse に集約する（`### Task:` だけでなく
            # `### Task N:` / `- Task:` / `- T-N |` も受理する。正準形しか読まない
            # 実装は実データの多数派の節を丸ごと取りこぼしていた）。
            if classify_task_line(stripped) == "task":
                remaining.append(f"  [{section}] {stripped[:80]}")
                in_task_body = True
            elif in_task_body:
                # task heading の本文は、その heading で既に計上済み
                continue
            elif stripped.startswith("- ") or stripped.startswith("### "):
                # 既知パターンに一致しない構造行。散文の本文は無視する
                unexpected_content.append(f"  [{section}] {stripped[:80]}")
    return remaining, unexpected_content


def _ascii_lower(value: str) -> str:
    """ASCII の大文字だけを小文字化する（Unicode 依存の畳み込みを持ち込まない）。

    正本: design.md § 1.2。`str.lower()` は Unicode 全体の大文字小文字対応表を
    使って畳み込む（例: Kelvin sign U+212A → "k"、独 "ß" → "ss" 相当の畳み込み系）ため、
    status / header セルの**完全一致**判定には使わない。
    """
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in value)


def _split_unescaped_pipes(rstripped: str) -> list[str] | None:
    """`|` 区切りの行をちょうど 4 セルへ分解する（design.md § 1.2 手順 2 / 3）。

    引数は **行末の `ws` だけを落とした文字列**（行頭空白は残っている）。行頭空白を
    落とさないことが判定の一部で、インデント行は `startswith("|")` を満たさずここで
    violation になる（design.md § 1.2 手順 1）。同様に外側パイプが無い行・全角パイプ行・
    引用行・list 行も一律 `None`（= violation）。コードスパン内の `|` も未エスケープなら
    区切りとして数える（D3）。
    """
    if not rstripped.startswith("|"):
        return None
    # 末尾の `|` は **未エスケープ**であること。`\|` は cell の中身であって区切りでは
    # ないので（`_ESCAPED_PIPE` と同じ判定）、`endswith("|")` だけだと
    # `| … | -\|` が 4 セルの data 行として通る fail-open になる。
    if len(rstripped) < 2 or rstripped[-1] != "|" or rstripped[-2] == "\\":
        return None
    cells = _ESCAPED_PIPE.split(rstripped[1:-1])
    if len(cells) != 4:
        return None
    return [c.strip(_WS) for c in cells]


def _classify_verification_line(line: str) -> tuple[str, object]:
    """`## Verification` 節の 1 行を閉じた文法で分類する（design.md § 1.1 / § 1.2）。

    戻り値は `(kind, payload)`。

    - `"blank"` / `"empty_marker"` / `"header"` / `"separator"`: payload は `None`
    - `"data"`: payload は `(method_kind, status)`。`method_kind` は
      `"ac"` / `"security_evidence"` / `"refactor-checkpoint"` のいずれか
    - `"violation"`: payload は違反行の実物（block メッセージ表示用に前後空白を
      除いた文字列。**この `strip()` は表示整形であって受理判定には一切使わない**。
      受理側の空白除去は `_WS` に閉じている）

    正規化はここに列挙した 5 種だけで、他の除去・推定は行わない（design.md § 1.2）。
    """
    rstripped = line.rstrip(_WS)
    if rstripped == "":
        return "blank", None
    # 完全一致。`rstripped` は既に行末の `ws` を落としてあるので、ここで `lstrip()` /
    # `strip()` を挟むと行頭インデントと Unicode 空白 padding（`- なし　`）まで
    # 受理してしまう（design.md § 1.2 手順 1 / § 1.1 empty_marker）。
    if rstripped == _EMPTY_MARKER:
        return "empty_marker", None
    cells = _split_unescaped_pipes(rstripped)
    if cells is None:
        return "violation", rstripped.strip()
    lowered = tuple(_ascii_lower(c) for c in cells)
    if lowered == _HEADER_CELLS:
        return "header", None
    if all(_SEPARATOR_CELL.match(c) for c in cells):
        return "separator", None
    method_cell = cells[0]
    status_norm = _ascii_lower(cells[1])
    for method_kind, pattern in _METHOD_KIND_PATTERNS:
        if pattern.match(method_cell) and status_norm in _STATUS_VALUES_BY_METHOD_KIND[method_kind]:
            return "data", (method_kind, status_norm)
    return "violation", rstripped.strip()


def _scan_verification(
    structural_lines: list[str],
    *,
    fence_before: list[list[int]] | None = None,
    fenced_heading_lines: list[int] | None = None,
) -> tuple[bool, list[str], list[tuple[str, object]], list[str]]:
    """Check 2: `## Verification` 節を閉じた文法で走査する（design.md § 4）。

    `(verification_section_found, verification_data_rows, violations, unfinished)`
    を返す。`verification_data_rows` は AC 検証行（`method=ac:`）だけを数える
    （AC-9 第 5 形。`unfinished` は method 種別に依らない）。`violations` は `(kind, payload)` の list で、`kind` は
    `"line"`（列挙外の行）/ `"section_fence"`（節に重なる fence の開始行番号）/
    `"fenced_heading"`（fence 内の `## Verification` 見出し行番号）のいずれか。

    `fence_before` / `fenced_heading_lines` は keyword-only + 既定値 `None`。
    `None` は「fence 情報なし = fence 違反 0」として扱う（単体テストが fence 引数
    無しで呼べるようにするため）。**production の呼び出し元（`gdd_stop_hook.py`）は
    両方を必ず渡すこと** — 既定値のまま production へ渡ると fence 違反が
    常に 0 件になる fail-open の面になる（design.md § 4）。
    """
    fence_before = fence_before or []
    fenced_heading_lines = fenced_heading_lines or []
    verification_section_found = False
    verification_data_rows: list[str] = []
    violations: list[tuple[str, object]] = []
    unfinished: list[str] = []
    # (h, e): h は見出し `## Verification` の kept index、e は次の `## ` 行の
    # kept index（無ければ len(structural_lines)）。design.md § 4 の定義そのもの
    section_bounds: list[tuple[int, int]] = []
    in_verification = False
    h = -1
    for index, line in enumerate(structural_lines):
        if line.rstrip() == "## Verification":
            if in_verification:
                section_bounds.append((h, index))
            in_verification = True
            verification_section_found = True
            h = index
            continue
        if in_verification and line.startswith("## "):
            section_bounds.append((h, index))
            in_verification = False
            continue
        if not in_verification:
            continue
        kind, payload = _classify_verification_line(line)
        if kind in ("blank", "empty_marker", "header", "separator"):
            continue
        if kind == "data":
            # AC-9 第 5 形: `security_evidence` / `refactor-checkpoint` 行は AC の検証の
            # 代わりにならないので `verification_data_rows` に数えない。`unfinished` は
            # method 種別に依らず数える（pending な evidence 行も block する）
            if payload[0] == "ac":
                verification_data_rows.append(line.strip())
            if payload[1] in _UNFINISHED_STATUS_VALUES:
                unfinished.append(line.strip())
            continue
        violations.append(("line", payload))
    if in_verification:
        section_bounds.append((h, len(structural_lines)))

    # 節に重なる fence（AC-7 / D4）。判定式は design.md § D4「右端 inclusive」:
    # range(h + 1, e + 1) の要素ごとに fence_before[i] を見る（fence 単位で 1 件）
    seen_fence_starts: set[int] = set()
    for h_index, e_index in section_bounds:
        for i in range(h_index + 1, e_index + 1):
            if i < len(fence_before):
                for start in fence_before[i]:
                    if start not in seen_fence_starts:
                        seen_fence_starts.add(start)
                        violations.append(("section_fence", start))
    # fence 内の `## Verification` 見出し（位置非依存。D4）
    for heading_line in fenced_heading_lines:
        violations.append(("fenced_heading", heading_line))

    return verification_section_found, verification_data_rows, violations, unfinished


def _tally_task_sections(structural_lines: list[str]) -> tuple[int, int, int, str]:
    """`(completed, pending, current, current_task_name)` を数える。"""
    counts = {"completed": 0, "pending": 0, "current": 0}
    cur_task_name = ""
    sect = ""
    for tl_line in structural_lines:
        if tl_line.startswith("## Completed Tasks"):
            sect = "completed"
        elif tl_line.startswith("## Pending Tasks"):
            sect = "pending"
        elif tl_line.startswith("## Current Task"):
            sect = "current"
        elif tl_line.startswith("## "):
            sect = ""
        elif sect:
            tl_stripped = tl_line.strip()
            if tl_stripped == "- なし":
                continue
            # done guard と同じく行頭要求（進捗表示と guard の件数を揃える）。
            # 末尾空白で落とさないよう **先頭の空白だけ**を見る（guard 側と同じ理由）。
            if tl_line.lstrip() != tl_line:
                continue
            # **名前もここで導出しない**。分類だけ共有して名前を作り直すと、
            # 見出し形をもう一度定義したことになる（実測: 素朴な
            # `replace("### Task:", "")` は `### Task 1: 説明` を `# Task 1: 説明` にする）。
            name = task_name(tl_stripped)
            if name:
                counts[sect] += 1
                if sect == "current" and not cur_task_name:
                    cur_task_name = name
    return counts["completed"], counts["pending"], counts["current"], cur_task_name

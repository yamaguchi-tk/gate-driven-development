"""Shared acceptance surface for tasklist.md task-heading detection.

Pure functions — no git / registry dependency. To be used by `gdd_stop_hook.py`
(done guard, progress counter, progress text) and `scripts/collect-gdd-telemetry.py`
so the task-heading forms are never silently dropped in one caller while accepted
in another (the silent-failure family the done guard once had).

**Why one module**: the defect this closes is not "the regex was wrong" but
"two readers disagreed about what a task heading looks like". Keeping the
acceptance surface in one place is the fix; duplicating the regex back into a
caller re-opens it. For the same reason the module also owns **name extraction**
— a caller that re-derives the name has re-derived the heading form.

**Why classify is derived from task_name**: holding the same two branches in two
functions lets them disagree — "counted as a task but the name vanished", which is
the very silent failure this module exists to close. Deriving one from the other
makes that split structurally impossible. **測った差**: 分岐を二重に持つ版は
`### Task:\u3000`（コロンの後が全角空白だけ）を `"task"` と分類するが `task_name()`
は `""` を返す（`[ \t]*` は全角空白を消費しないので `(.+)` が一致し、`.strip()` が
名前を空にする）。導出版は両方とも「タスクでない」に揃う。この 1 行が判別力の要で、
契約テストの不変条件 fixture に入っている。

**受理面の出所**: `hooks/scripts/run-pre-tool-use-plan-reread-hook.sh` の
`_task_heading_re`（同ファイル 50 行）と、**`[ \t]` の範囲かつ名前が空でない行について同値**。
bash 側は `[[:space:]]` なので `\v` `\f` `\r` U+3000 も受理し、また名前が空白のみの行も
受理するが、python 側はどちらも受理しない。実データの tasklist に該当は無かった
（2026-08-22 実測。非 ASCII 空白で始まる見出しも名前が空の見出しも無い）ので広げない。乖離は契約テストが明示的に固定している。python 側だけ狭いと、bash reader が
読める節を python reader が「非標準の内容」に落として停止を塞ぐ非対称が残る。
**測った入力集合**: 2026-08-22 に `~/.gdd/worktrees/**/.steering/*/tasklist.md`
の `## Current Task` 節を走査した実測 — `### Task <N>: <name>` が最も多く、
`- Task: <name>` が続き、正準形 `### Task: <name>` は少数派で、
狭い受理面はその節を丸ごと取りこぼす。
"""
from __future__ import annotations

from collections import Counter
import re

#: 見出し形のタスク行。`##`〜`####` と箇条書き（`-` / `*`）を入口として受理し、
#: `Task` の後の採番は任意。末尾の `:` の後ろを名前として捕捉する（1 文字以上を要求）。
#: 見出しレベルの下限が `##` なのは bash reader と同値にするため（`# Task: x` は
#: bash 側も不受理であることを実測済み）。`- Task ID:` / `- Task Size:` /
#: `### Task Size Distribution` / `### Tasks: 一覧` / `### Task-1:` はいずれも不一致。
_TASK_HEADING_RE = re.compile(r"^(?:#{2,4}|[-*])[ \t]*Task[ \t]*\d*[ \t]*:[ \t]*(.+)$")
#: `- T1 | ...` / `- T-1 | ...`。`- T` の直後に数字を要求するのは
#: `- T-helper` のような非タスク行を task 扱いしないため。`|` を併せて要求するのは
#: `- T1 の作業を完了した` のような散文を未完了タスクに計上しないため。
_TASK_LIST_ITEM_RE = re.compile(r"^- (T-?\d.*)$")


def task_name(stripped_line: str) -> str:
    """Return the task name for a task line, or "" when the line is not a task.

    受理面と名前抽出を同じ場所に置く。分離すると「分類は共有だが名前抽出は各自」
    という形になり、採番付き見出しで名前が欠ける（実測: 素朴な
    `replace("### Task:", "")` は `### Task 1: 説明` を `# Task 1: 説明` にする）。
    """
    heading = _TASK_HEADING_RE.match(stripped_line)
    if heading:
        return heading.group(1).strip()
    item = _TASK_LIST_ITEM_RE.match(stripped_line)
    if item and "|" in stripped_line:
        return item.group(1).strip()
    return ""


def classify_task_line(stripped_line: str) -> str:
    """Return "task" if stripped_line is a task heading/list-item, else "other".

    Accepts: "### Task: ...", "### Task 1: ...", "### Task 12: ...",
    "- Task: ...", "#### Task: ...", "- T1 | ...", "- T-1 | ...".
    **`task_name()` から導出する**ので、分類と名前抽出が食い違うことはない
    （不変条件 `classify(s) == "task" ⟺ task_name(s) != ""` を契約テストが固定する）。
    """
    return "task" if task_name(stripped_line) else "other"


#: fenced code block の開始/終了候補。`` ` `` または `~` を 3 つ以上。
#: **インデントは制限しない**。CommonMark の「開き fence はインデント 0〜3」は
#: *ブロックの起点からの* 相対で、リスト項目の中では項目のインデント分ずれる。
#: GDD の tasklist は `#### Steps` の**リスト項目の下**に fence を置くのが普通で、
#: `^ {0,3}` だと実データの多くが見えない。実測値と導出コマンドは
#: `.steering/<task>/design.md § 論点 2c` が正本（数値をここに書き写さない）。
#: 境界は `tests/test_tasklist_parse_contract.py::FenceIndentTests` が pin する。
#: インデントに **TAB を含める**。集約前の 5 実装はいずれもタブを見ており
#: （awk は `[[:space:]]*`、Python 3 実装は `[ \t]*`）、半角スペースだけに
#: 狭めると `\t```` ` で包んだ記入例が fence として認識されず、A-4（記入例が
#: 証跡になる）が復活する。境界は canonical field 契約テストが 5 実装同時に pin する。
_FENCE_RE = re.compile(r"^[ \t]*(?P<marker>`{3,}|~{3,})(?P<info>.*)$")


def strip_fenced_lines(text: str) -> tuple[list[str], bool]:
    """Return (lines outside fenced code blocks, fence_unclosed).

    tasklist.md の `#### Steps` に貼られた計画コードは **tasklist の構造ではない**。
    除外しないと、fence 内の `- T1 | AC-01 | still open` のような行が未完了タスクとして
    数えられ、実タスクを全部終えても phantom が残って恒久的に block する（実データで発生）。

    素朴な `startswith("```")` トグルでは足りない。実測した壊れ方:

    - **閉じ忘れ**（`` ``` `` の数が奇数）: そこから先を全部読み飛ばすので、
      **実タスクが 1 件も数えられず done が通る** = fail-open。実 tasklist にも該当があった
    - **`~~~` 形式**: トグルに引っかからず、中の task 行を計上して phantom block
    - **4 連バッククォートで包んだ ``` 入りブロック**: 内側の ``` でトグルが反転して同様

    そこで開き fence の**記号の種類と長さ**を保持し、**同種・同長以上かつ後ろが空白だけ**の
    行でのみ閉じる。閉じ忘れは呼び出し側が **fail-closed に倒せる**よう第 2 戻り値で返す
    （黙って読み飛ばすと guard が無言で無効化される）。
    """
    kept, unclosed, _fence_before, _fenced_heading_lines = strip_fenced_lines_marked(text)
    return kept, unclosed


def strip_fenced_lines_marked(
    text: str,
) -> tuple[list[str], bool, list[list[int]], list[int]]:
    """(kept, unclosed, fence_before, fenced_heading_lines)。design.md D4 が正本。

    fence_before[i]: kept[i-1]/kept[i] の間で落とされた閉じた fence の開始 index（昇順）。
    len(fence_before) == len(kept) + 1。fenced_heading_lines: 落とされた行のうち
    `line.rstrip() == "## Verification"` を満たす見出し行の原文 index（昇順）。
    """
    lines, closed, open_at, closed_spans = _scan_fences(text)
    cut = len(lines) if open_at < 0 else open_at
    kept, kept_source_index = [], []
    for i, line in enumerate(lines):
        if i >= cut or i in closed:
            continue
        kept.append(line)
        kept_source_index.append(i)

    fence_before: list[list[int]] = [[] for _ in range(len(kept) + 1)]
    for start, end in closed_spans:
        if start >= cut:
            continue
        gap = 0
        while gap < len(kept_source_index) and kept_source_index[gap] < start:
            gap += 1
        fence_before[gap].append(start)
    for bucket in fence_before:
        bucket.sort()

    # 判定は `line.rstrip() == "## Verification"` の **exact match**（design.md D4 /
    # AC-1 (f)）。`startswith` にすると design § 1.5 の carve-out（`## Verification
    # Notes` / `## Verification History`）まで拾い、記入例 fence が `## Verification
    # Notes` を 1 行含むだけで回復手順の無い恒久 block になる。Check 2 が節見出しを
    # exact match で走査する（`## Verification Notes` を飲み込まない）以上、fence 内
    # の見出しも同じ判定でなければ「fence の外なら別節、中なら Verification 節」と
    # いう非対称が生まれる。
    fenced_heading_lines = sorted(
        i for start, end in closed_spans if start < cut
        for i in range(start, min(end, cut - 1) + 1)
        if lines[i].rstrip() == "## Verification"
    )
    return kept, open_at >= 0, fence_before, fenced_heading_lines


def _scan_fences(text: str) -> tuple[list[str], set[int], int, list[tuple[int, int]]]:
    """走査を 1 本化する。返すのは (全行, **閉じた** fence の内側の行 index, 未閉鎖の開き fence の index, 閉じた fence ごとの (開始, 終了) index)。

    閉じた fence と未閉鎖の開き fence を呼び出し側が区別できないと、閉じ忘れの救済
    （下記 `strip_fenced_blocks`）が「それ以前の正しく閉じた記入例」まで復活させる。
    未閉鎖が無いときの index は -1。`closed_spans` は `closed` set からの contiguity
    復元では区別できない「閉じ fence の直後に次の開き fence が来る」形を復元するために
    足す（design.md D4）。判定ロジックは不変で、戻り値だけが増える。
    """
    lines = text.splitlines()
    closed: set[int] = set()
    closed_spans: list[tuple[int, int]] = []
    fence_marker = ""
    open_at = -1
    for i, line in enumerate(lines):
        match = _FENCE_RE.match(line)
        if fence_marker:
            # 閉じ判定: 同じ記号・同じ長さ以上・情報文字列なし
            if (
                match
                and match.group("marker")[0] == fence_marker[0]
                and len(match.group("marker")) >= len(fence_marker)
                and not match.group("info").strip()
            ):
                closed.update(range(open_at, i + 1))
                closed_spans.append((open_at, i))
                fence_marker = ""
                open_at = -1
            continue
        if match:
            info = match.group("info")
            # backtick fence の info string に ` を含む形は fence ではない
            # （CommonMark: "```で囲むこと" のような散文を fence にしない）
            if match.group("marker")[0] == "`" and "`" in info:
                continue
            fence_marker = match.group("marker")
            open_at = i
    return lines, closed, open_at, closed_spans


def strip_fenced_blocks(text: str) -> str:
    """canonical field 読み取り向けのラッパ。fence 内の行を落とした本文を返す。

    `state.md` / `tasklist.md` の fenced code block は「書式の記入例」であって現在値
    ではない。fence を追跡しないと、記入例を 1 つ置くだけで field が成立する
    （merge gate の `Merge Approval` が実測でこの形で通っていた）。

    **閉じ忘れ時は、未閉鎖の開き fence 以降だけを残す**。閉じ忘れは実データで発生し
    （`strip_fenced_lines` の docstring が実測件数を持つ）、そこから先を全部落とすと
    canonical field が 1 つも見えなくなる。読み手は routing 材料を失い、書き手
    バリデータは「触った field が無い」と判断して検査自体を飛ばす（fail-open）。
    落とすより残す側に倒し、A-4（記入例が証跡になる）の閉じ忘れ時の残存は許容する。

    ただし救済は**未閉鎖の fence に限る**。本文を丸ごと返すと、それ以前の
    正しく閉じた記入例まで復活し、閉じ忘れ 1 つで A-4 が全面的に開く
    （`detect-steering.sh` の awk はこの形を既に閉じており、揃えないと
    「書き手は通すのに読み手には見えない」非対称が残る）。
    """
    lines, closed, _open_at, _closed_spans = _scan_fences(text)
    return "\n".join(line for i, line in enumerate(lines) if i not in closed)


#: `state.md` の `Route In Progress` 行。`- Route In Progress: x` / `` - `Route In Progress=x` `` の両形。
#: **行頭アンカー**が本質 —— 解説文中の言及を値として拾わないため（H-3）。
def route_value(raw: str) -> str:
    """`Route In Progress` の値部分から **enum トークンだけ**を取り出す。

    正準書式は `none | reason: ... | updated_by: ...` で、**注記が値に続く**
    （`run-session-start-hook.sh` は同じ値に `gdd_value_head`（lib/detect-steering.sh）を通している）。
    実データでは `none（2026-08-21 / 人間による解除で…）` の形もある。

    注記を値の一部として扱うと **`none` と書いてあるのに block** する
    ―― block メッセージの指示（`none にする`）に従っても解除できない形になり、
    bind 限定で塞いだ欠陥と同型になる（completion-check で見つかった。
    **実データで block したものの中に、この誤 block が含まれていた**）。
    """
    body = raw.split("|")[0].strip().strip("`").strip("*").strip('"').strip("'").strip()
    head = re.match(r"[A-Za-z_][A-Za-z0-9_-]*", body)
    # 識別子で始まらない値（`実装修正中` 等）も**そのまま返して block 側に残す**
    # （completion-check 5 回目の H5-1）。「読めなければ行ごと skip」にすると
    # `**systematic_debugging**` / `実装修正中` が**すべて通り**、親実装より判別力が落ちる。
    # `none` の解除判定は呼び出し側の `chosen.lower() != "none"` が行う。
    return head.group(0) if head else body


#: 行頭アンカーは `tests/test_canonical_field_line_anchoring_contract.py` の規約
#: （行頭から始まり、markdown bullet marker は `- ` 1 個まで）に揃える。旧
#: `^[-*]?\s*` は空白を個数無制限で食うため、`    Route In Progress: none`
#: （インデントした記入例・散文）と `-Route In Progress: ...`（bullet 直後に空白なし）
#: を canonical field として受理していた。done guard Check 3 が読む経路なので、
#: 記入例の `none` を現在値に採ると未完了 route を抱えたまま done が成立する
#: （fail-open）。同時に、awk の `gdd_extract_doc_field` が拒否する形をここだけが
#: 受理する非対称でもあった（2026-09-03 実測で 3 形）。
ROUTE_IN_PROGRESS_PATTERN = re.compile(
    r'^(?:-[ \t]+)?`?Route In Progress(?P<sep>[=:])\s*(.+?)(`.*)?$', re.IGNORECASE
)

#: `str.splitlines()` が LF / CR 以外に行を分ける 8 文字。done guard の検査と、hook 自身の
#: `Last Handoff Summary=` の置換範囲（`lib/handoff_summary.py`）が同じ集合を使う（独立-3 D3）
NON_NEWLINE_LINE_BREAKS = frozenset("\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029")

def state_field_pattern(field: str) -> str:
    """state.md の field 行を拾う canonical パターン。

    `Field: v` / `Field=v` / `- Field: v` を受理し、行頭にアンカーする。
    存在判定 (has_state_field) と値取得 (state_field_value) の唯一の読み取り規約。
    呼び出し側は本パターンを適用する前に対象テキストの backtick を全除去する
    （`_strip_backticks_for_field_match()`）ため、field 名や bullet 周りに
    backtick を挟む形は考慮不要（PR #31 独立レビュー Finding F-2: 二重
    backtick・field 名内 backtick・bullet 前置 backtick は旧パターンの
    単一任意 backtick 許容を外れ、field 行が未検出のまま値だけ書き換えられた。
    読み取り側 `gdd_extract_doc_field()`（`hooks/scripts/lib/detect-steering.sh`）
    は行全体から backtick を `gsub` で全除去してから解釈するため、書込み側も
    この正規化を先に揃える）。

    空白は `\\s` ではなく `[ \\t]` で受ける。`\\s` は改行も食うため、値のない
    `Resume From:` の値として次行の内容を拾ってしまう。
    """
    return rf"^(?:-[ \t]+)?{re.escape(field)}[ \t]*[:=]"


def route_in_progress_key_lines(state_text: str) -> list[str]:
    """fence を剥がした `state.md` の `Route In Progress` のキー行を、書かれた順に返す（値の有無は問わない）。

    write guard（`state_fields.has_state_field_line`）と同じく backtick を全除去してから
    `state_field_pattern()` を当てる。reader（`ROUTE_IN_PROGRESS_PATTERN`）に合わせて大文字小文字は
    無視するので、受理集合は write guard より大文字小文字の分だけ広い（block 側に倒れる）。done guard Check 3 はこの最後の 1 本を現在の行として読む（独立-2 B1・B2）。
    """
    pattern = re.compile(state_field_pattern("Route In Progress"), re.IGNORECASE)
    return [
        line for line in strip_fenced_blocks(state_text).splitlines()
        if pattern.match(line.replace("`", ""))
    ]


def select_route_in_progress(state_text: str) -> str:
    """`state.md` 全文から `Route In Progress` の**現在値**を選ぶ。

    **done guard と telemetry collector の受理面をここ 1 箇所に集約する**
    （completion-check 6 回目の M6-1。従来は collector が `extract_field` の
    先頭一致をそのまま集計キーにしており、`none（注記）` が 1 件ごとに別バケットになり、
    かつ**正準行が 2 本ある場合に hook と判定が食い違って**いた）。

    規則:

    - **fence を剥がす**。閉じ忘れのときは未閉鎖の開き fence 以降を生の行で読む（黙って skip しない）
    - **行頭アンカー**で読む（解説文中の言及を値として拾わない）
    - **正準形（コロン）を優先**し、無ければ旧等号形へフォールバック
    - 同形が複数あれば**最後に書かれた行**を採る（解除の追記が無視されないように）

    **shell 側もこの関数へ委譲する**（`detect-steering.sh` の
    `gdd_extract_route_in_progress`）。上の規則を awk へ書き写すと、規約が 2 実装に
    散って片方だけ直す形の退行が戻る —— 2026-09-03 実測では、汎用 reader
    `gdd_extract_doc_field`（最初の一致）との差が 7 形に達していた。正本テストは
    `tests/test_route_in_progress_reader_contract.py`。
    """
    # 救済範囲は `strip_fenced_blocks` と同じ（閉じた fence は落とし、未閉鎖の
    # 開き fence 以降だけ残す）。閉じ忘れ時に本文を丸ごと読むと、それ以前の
    # 正しく閉じた記入例まで現在値に化ける。ここは done guard Check 3 と
    # telemetry が読む経路なので、記入例の `none` を拾うと未完了 route を
    # 抱えたまま done が成立する（fail-open）。awk 側の reader とも値が割れる。
    lines = strip_fenced_blocks(state_text).splitlines()
    canonical = ""
    legacy = ""
    for line in lines:
        match = ROUTE_IN_PROGRESS_PATTERN.match(line)
        if not match:
            continue
        value = route_value(match.group(2))
        if not value:
            continue
        if match.group("sep") == ":":
            canonical = value
        else:
            legacy = value
    return canonical or legacy


#: `state.md` の `Resume From` 行。`- Resume From: x` / `` - `Resume From=x` `` の両形。
# canonical field 行の接頭辞は **markdown bullet `-` + 空白 1 個以上**だけ。
# 旧 `^[-*]?\s*` は `*` bullet と任意のインデントを受理していたため、入れ子 bullet の
# 履歴メモ（`  - `Resume From=...`（Attempt #2）`）が現在値として返っていた。
# 他 5 実装のアンカーに揃える（正本: tests/test_canonical_field_line_anchoring_contract.py）。
RESUME_FROM_PATTERN = re.compile(
    r'^(?:-[ \t]+)?`?Resume From[=:][ \t]*(.+?)(`.*)?$', re.IGNORECASE
)


def resume_from_value(body: str) -> str:
    """`state.md` 本文（fence 剥がし済み）から `Resume From` の現在値を返す。

    区切り文字の後ろが trim + backtick 除去後に空の行は現在値ではない。その行は
    飛ばし、次の一致行を見る（最初の**値付き**一致）。値付き行が 1 本も無ければ `""`。
    正本: tests/test_state_field_value_less_line_contract.py。
    """
    for sf_line in body.splitlines():
        rf_match = RESUME_FROM_PATTERN.match(sf_line)
        if not rf_match:
            continue
        candidate = rf_match.group(1).strip().strip("`").strip()
        if candidate:
            return candidate
    return ""


#: `Reviewed by:` 行。行頭の空白・箇条書きの記号（`-` `*` `+`）・`**` の装飾を許す
#: （実データの書式: `- Reviewed by:` / `Reviewed by:` / `**Reviewed by**:` /
#: `- **Reviewed by: …**`）。backtick は除いてから当てる。
_REVIEWED_BY_RE = re.compile(r"^[ \t]*(?:[-*+][ \t]+)?(?:\*\*)?Reviewed by(?:\*\*)?[ \t]*:")
#: impl-gating が review を外した完了タスクの `Reviewed by:` の値（正本: references/task-breakdown-steps.md
#: § Judgment Change）。同じタスクに `no` の宣言があるときだけ受け付ける
SKIPPED_REVIEWED_BY = "none (Judgment Change: no)"
#: review を外すと宣言する欄の行。受けるのはこの 1 形だけ（装飾・末尾の文・別の値は宣言に数えない）
_JUDGMENT_NO_RE = re.compile(r"[ \t]*- Judgment Change: no[ \t]*")
#: 宣言の欄に見える行（大小文字・装飾・行の中の位置を問わない）。`Reviewed by:` の行を除き、この行がちょうど 1 本で
#: `_JUDGMENT_NO_RE` の形のときだけ宣言に数える（受け付ける形を閉じ、ほかの書き方はすべて review を回す側）
_JUDGMENT_WORD_RE = re.compile(r"judge?ment\W*change", re.IGNORECASE)
#: 差し戻しの印。impl-gating は changes_requested のたびに Current Task の task に足し、approved で消す
_GATE_ROUNDS_RE = re.compile(r"gate\W*rounds", re.IGNORECASE)
#: テンプレートで 1 本だけの欄（gdd-task-breakdown の Plan Execution Fields）。1 つの block に 2 本あれば、
#: 見出しの崩れた task が前の task の block に混ざった印
_SINGLE_FIELD_RE = re.compile(r"- (Covers AC|Depends on|Execution Status|Complexity|Judgment Change):")
#: task の Files の宣言（gdd-task-breakdown の Files block）。1 行の形 `- Files: a, b` か、見出し（`#### Files` か値の無い
#: `- Files:`）の下に `- Create|Modify|Test|Delete: <パス>, …` を並べる形（インデント可）。パスは glob・空白・語を
#: 含まないものだけで、前に動詞、後ろに括弧の注記を置いてよい。注記の中は読まない（宣言を広げる側に読まない）
_FILES_RE = re.compile(r"(?:- Files:|#### Files)[ \t]*(.*)")
_FILES_ITEM_RE = re.compile(r"([ \t]*)- (?:Create|Modify|Test|Delete):[ \t]*(.+)")
_PATH_PART = r"(?:(?:Create|Modify|Test|Delete)[ \t]+)?`?([A-Za-z0-9_.\-/]+)`?[ \t]*(?:（[^）]*）|\([^)]*\))?"
_PATHS_RE = re.compile(rf"{_PATH_PART}(?:[ \t]*,[ \t]*{_PATH_PART})*")
_NO_PATHS_RE = re.compile(r"(?:なし|none)[ \t]*(?:（[^）]*）|\([^)]*\))?", re.IGNORECASE)
#: review を外してよい Task Size（completion-check を通るもの）。Express は impl-gating が唯一の review なので外さない。
#: Express から昇格した steering は、昇格の元の High が直ったかを宣言からは判定できないので外さない
#: Execution Plan の見出し（段・前後の語を問わない）と、外してよい節の見出し・Mode の行（許可リスト）
_PLAN_HEADING_RE = re.compile(r"#+\s.*execution\s*plan", re.I)
_PLAN_SECTION_RE = re.compile(r"## Execution Plan\b")
_PLAN_MODE_RE = re.compile(r"\bmode\b|^\W*(sequential|parallel)\W*$", re.I)
_PLAN_GATE_BATCH_RE = re.compile(r"gate\W*batch\W*\d", re.I)
_SEQUENTIAL_MODE_LINES = frozenset({"- Mode: sequential", "Mode: sequential", "- sequential"})


def _sequential_plan(lines: list[str]) -> bool:
    """Execution Plan が無いか、逐次と読めるか（並列の batch の最後の 1 task を外さないため）。

    外してよいのは、見出しが 0 本か、`## Execution Plan` ちょうど 1 本の節で、Mode の行（subagent-driven-implementation
    が並列か逐次かを決める欄）がちょうど 1 本あり、それが `_SEQUENTIAL_MODE_LINES` のどれかで、番号つきの
    Gate Batch の行が無いときだけ。読めない形は外さない側に倒す。
    """
    headings = [i for i, line in enumerate(lines) if _PLAN_HEADING_RE.match(line)]
    if not headings:
        return True
    if len(headings) > 1 or not _PLAN_SECTION_RE.match(lines[headings[0]]):
        return False
    words = []
    for line in lines[headings[0] + 1:]:
        if line.startswith(("# ", "## ")):
            break
        if _PLAN_GATE_BATCH_RE.search(line):
            return False
        if _PLAN_MODE_RE.search(line):
            words.append(line.strip())
    return len(words) == 1 and words[0] in _SEQUENTIAL_MODE_LINES


_SKIPPABLE_TASK_SIZES = frozenset({"standard", "quick (standard)"})


def judgment_change_no(block: list[str]) -> bool:
    """タスクのブロックの行（fence の外）が review を外すと宣言しているか。

    `Reviewed by:` の行を除き、`_JUDGMENT_WORD_RE` に当たる行がちょうど 1 本で、それが `_JUDGMENT_NO_RE` の形のときだけ真。
    値の違う行・別の書き方の行・2 本目の行が混ざれば偽（review を回す側）。gate の固定行（`impl_gate_review`）と完了の受理
    （`completed_tasks_reviewed_by`）が同じこの述語を使う。
    """
    lines = [
        line.rstrip("\n") for line in block
        if _JUDGMENT_WORD_RE.search(line) and not _REVIEWED_BY_RE.match(line.replace("`", ""))
    ]
    return len(lines) == 1 and bool(_JUDGMENT_NO_RE.fullmatch(lines[0]))


def _paths(value: str) -> frozenset[str] | None:
    value = value.strip()
    if _NO_PATHS_RE.fullmatch(value):
        return frozenset()
    if not _PATHS_RE.fullmatch(value):
        return None
    paths = set()
    for match in re.finditer(_PATH_PART, value):
        path = match.group(1)
        path = path[2:] if path.startswith("./") else path
        if not path or path.endswith("/"):
            return None
        paths.add(path)
    return frozenset(paths)


def declared_files(block: list[str]) -> frozenset[str] | None:
    """タスクのブロックの Files の宣言のパスの集合。宣言がちょうど 1 つで、読める形のときだけ返す（ほかは None）。"""
    heads = [i for i, line in enumerate(block) if _FILES_RE.fullmatch(line.rstrip())]
    if len(heads) != 1:
        return None
    value = _FILES_RE.fullmatch(block[heads[0]].rstrip()).group(1)
    if value:
        return _paths(value)
    paths: set[str] = set()
    indent: str | None = None
    for line in block[heads[0] + 1:]:
        line = line.rstrip()
        if not line.strip():
            if indent is None:
                continue
            break
        item = _FILES_ITEM_RE.fullmatch(line)
        if indent and not line.startswith(indent):
            break  # インデントした項目の後の、次の欄
        if not line.lstrip().startswith("- "):
            break
        found = _paths(item.group(2)) if item else None
        if found is None:
            return None
        indent = item.group(1)
        paths |= found
    return frozenset(paths) if indent is not None else None


def completed_tasks_reviewed_by(text: str) -> tuple[list[tuple[str, str]], bool]:
    """`## Completed Tasks` のタスクごとに、`Reviewed by:` 行の状態を返す。

    返り値は ([(タスク名, 状態)], fence が閉じていないか)。状態は `ok`、`missing`（行が無い）、
    `no-implementation-reviewer`（行に `gdd-implementation-reviewer` が無い）、`skipped`（impl-gating が review を
    外した。`- Judgment Change: no` の宣言と、値が `SKIPPED_REVIEWED_BY` ちょうどの行の両方がある）。タスクごとに返すのは、
    既に 1 タスク欠けている tasklist で別のタスクの行を落としたときも、移す前と後の差で見えるようにするため。
    completion-check Step 2a の検算（`scripts/check-gate-ledger.sh`）と、steering write guard の `reviewed_by_regressions` が使う。

    節の見出しは done guard と同じ前方一致（`## Completed Tasks（3 件）` も節）。タスクのブロックは、
    行頭から始まるタスク行（`task_name`。インデントした行は done guard と同じく構造として読まない）から、
    次のタスク行か `## ` の見出しまで。fence の中の行は数えない。reviewer の judgment（approved など）は自由文なので見ない。
    """
    lines, unclosed = strip_fenced_lines(text)
    tasks: list[tuple[str, str]] = []
    in_section = False
    current: str | None = None
    reviewed: list[str] = []
    body: list[str] = []

    def close() -> None:
        if current is None:
            return
        if not reviewed:
            tasks.append((current, "missing"))
        elif any("gdd-implementation-reviewer" in line for line in reviewed):
            tasks.append((current, "ok"))
        elif judgment_change_no(body) and any(
            line[_REVIEWED_BY_RE.match(line).end():].strip() == SKIPPED_REVIEWED_BY for line in reviewed
        ):
            tasks.append((current, "skipped"))
        else:
            tasks.append((current, "no-implementation-reviewer"))

    for line in lines:
        if line.startswith("## "):
            close()
            current, reviewed, body = None, [], []
            in_section = line.startswith("## Completed Tasks")
            continue
        if not in_section:
            continue
        name = task_name(line.rstrip()) if line[:1] not in (" ", "\t") else ""
        if name:
            close()
            current, reviewed, body = name, [], []
            continue
        body.append(line)
        plain = line.replace("`", "")
        if current is not None and _REVIEWED_BY_RE.match(plain):
            reviewed.append(plain)
    close()
    return tasks, unclosed


def reviewed_by_rows(text: str) -> list[tuple[str, str]]:
    """completion-check Step 2a の検算の行（`(状態, 詳細)`）。状態は ok / missing / invalid。

    述語は `completed_tasks_reviewed_by`。`scripts/check-gate-ledger.sh` の reviewed-by 行と
    `scripts/check-completion-mechanical.py` が同じ行を出すために共有する。完了タスクが 0 件なら
    missing（Step 2a を通る Task Size で、節を丸ごと移した・見出しの形が崩れた）。
    """
    tasks, unclosed = completed_tasks_reviewed_by(text)
    rows: list[tuple[str, str]] = []
    if not tasks and not unclosed:
        rows.append(("missing", "## Completed Tasks に完了タスクが無い（丸ごと worklog.md へ移した・見出しの形が崩れたなら、そのまま戻す）"))
    if unclosed:
        rows.append(("invalid", "tasklist.md の fence が閉じていない（閉じるまで完了タスクを数えられない）"))
    recovery = (
        "（completion-check Step 2a のとおり gdd-implementation-gating で再 gate する。"
        "worklog.md へ移しただけなら、その行をそのまま戻す）"
    )
    for name, status in tasks:
        name = " ".join(name.split())
        if status == "ok":
            rows.append(("ok", f"{name}: Reviewed by（gdd-implementation-reviewer）がある"))
        elif status == "skipped":
            rows.append(("ok", f"{name}: impl-gating の review を外した（Judgment Change: no）"))
        elif status == "missing":
            rows.append(("missing", f"{name}: Reviewed by 行が無い{recovery}"))
        else:
            rows.append(("invalid", f"{name}: Reviewed by に gdd-implementation-reviewer が無い{recovery}"))
    return rows


def impl_gate_review(
    text: str, task_size: str, changed: frozenset[str] | None, completed_at_start: int | None
) -> tuple[bool, str]:
    """impl-gating が review（Step 2〜10）を外してよいか。返り値は (外すか, 外す task 名か review を回す理由)。

    `changed` は gate 単位の差分（前の gate 単位を終えたときの起点からの変更ファイル。取れなければ None）。外すのは、
    それが `no` の task の Files の宣言（`declared_files`）に収まり、宣言が空でなければ宣言したファイルが差分に
    出ているときだけ。崩れた task の変更は宣言の外に出る（`scripts/impl-gate-context.py` が git から取って渡す）。
    `completed_at_start` は gate 単位の始まりの Completed Tasks の数（state.md の `Impl Gate Completed`。読めなければ
    None）。今の数（`completed_tasks_reviewed_by`）と違えば、並列の batch の途中か task を移したので外さない。

    外すのは、Task Size が `_SKIPPABLE_TASK_SIZES` のどれかで、`## Current Task`（done guard と同じ前方一致）が
    受け付ける形だけでできているときだけ。Execution Plan は `_sequential_plan`、task は 1 つだけ（Gate Batch・並列の batch は外さない。起点と
    State Machine Impact block の単位が gate 単位と合わないため）。受け付ける形は、最初の task の見出しより
    前は空行だけ、どの task も `judgment_change_no` で、テンプレートで 1 本だけの欄が重ならない、
    `Gate Rounds` の行が無い（差し戻し後の再 gate ではない）。fence が閉じていない、task として読めない `### ` 見出しがある、
    例外が起きた、のどれでも review を回す。`scripts/impl-gate-context.py` が固定行で出す。
    """
    try:
        if task_size not in _SKIPPABLE_TASK_SIZES:
            return False, f"Task Size={task_size or '（読めない）'}"
        lines, unclosed = strip_fenced_lines(text)
        if unclosed:
            return False, "fence が閉じていない"
        if not _sequential_plan(lines):
            return False, "Execution Plan が逐次と読めない（並列の batch か読めない形）"
        blocks: list[tuple[str, list[str]]] = []
        in_current = False
        for line in lines:
            if line.startswith("## "):
                in_current = line.startswith("## Current Task")
                continue
            if not in_current:
                continue
            if _GATE_ROUNDS_RE.search(line):
                return False, "Current Task に Gate Rounds がある（差し戻し後の再 gate）"
            name = task_name(line.rstrip()) if line[:1] not in (" ", "\t") else ""
            if name:
                blocks.append((" ".join(name.split()), []))
            elif line.startswith("### "):
                return False, f"Current Task に task として読めない見出しがある（{line.strip()}）"
            elif blocks:
                blocks[-1][1].append(line)
            elif line.strip():
                return False, f"Current Task の最初の task より前に行がある（{line.strip()}）"
        if not blocks:
            return False, "Current Task に task が無い"
        if len(blocks) > 1:
            return False, "Current Task に task が 2 つ以上ある（Gate Batch・並列の batch）"
        declared = [name for name, block in blocks if not judgment_change_no(block)]
        if declared:
            return False, f"Judgment Change: no ではない task がある（{', '.join(declared)}）"
        mixed = [name for name, block in blocks
                 if max(Counter(m.group(1) for line in block if (m := _SINGLE_FIELD_RE.match(line))).values(), default=0) > 1]
        if mixed:
            return False, f"1 本だけの欄が重なる task がある（見出しの崩れた task が混ざった。{', '.join(mixed)}）"
        if changed is None:
            return False, "gate 単位の差分を取れない"
        if completed_at_start is None:
            return False, "state.md の Impl Gate Completed が無いか読めない"
        done = len(completed_tasks_reviewed_by(text)[0])
        if done != completed_at_start:
            return False, f"Completed Tasks の数（{done}）が gate 単位の始まり（{completed_at_start}）と違う（並列の batch の途中か、task を移した）"
        name, block = blocks[0]
        files = declared_files(block)
        if files is None:
            return False, f"Files の宣言が無いか読めない（{name}）"
        outside = sorted(set(changed) - files)
        if outside:
            return False, f"Files の宣言の外の変更がある（{', '.join(outside[:3])}）"
        if files and not files & changed:
            return False, "Files に宣言したファイルが gate 単位の差分に無い"
        return True, name
    except Exception as exc:  # noqa: BLE001 — 判定できないときは review を回す
        return False, f"判定できない（{type(exc).__name__}）"


def open_task_names(text: str) -> Counter[str]:
    """`## Current Task` と `## Pending Tasks`（done guard と同じ前方一致）の、行頭から始まるタスク行の名前の件数。"""
    lines, _unclosed = strip_fenced_lines(text)
    names: Counter[str] = Counter()
    in_open = False
    for line in lines:
        if line.startswith("## "):
            in_open = line.startswith(("## Current Task", "## Pending Tasks"))
        elif in_open and line[:1] not in (" ", "\t") and (name := task_name(line.rstrip())):
            names[name] += 1
    return names


#: `_without_unclosed_fences` が読み直す回数の上限。1 回ごとに全体を読み直すので、上限が無いと閉じていない fence の
#: 数の 2 乗で時間が延び、hook の timeout（PreToolUse は timeout で通る）に届く。実データの tasklist.md はあっても 1 本
_MAX_UNCLOSED_FENCES = 10


def _without_unclosed_fences(text: str) -> str:
    """閉じた fence は落とし、閉じていない開き fence の行だけを除いて先を構造として読む（`strip_fenced_blocks` の救済と同じ向き）。

    閉じていない fence が `_MAX_UNCLOSED_FENCES` を超えたら `ValueError`（判定できない。呼び出し側が止める）。
    """
    for _ in range(_MAX_UNCLOSED_FENCES + 1):
        lines, closed, open_at, _spans = _scan_fences(text)
        if open_at < 0:
            return text
        text = "\n".join(line for i, line in enumerate(lines) if i not in closed and i != open_at)
    raise ValueError(f"more than {_MAX_UNCLOSED_FENCES} unclosed fences")


def _regressions(before: str, after: str) -> list[tuple[str, str]]:
    before_tasks, _ = completed_tasks_reviewed_by(before)
    after_tasks, _ = completed_tasks_reviewed_by(after)
    # 外した記録（skipped）も、通った記録と同じく落とす書き込みを止める
    passed = ("ok", "skipped")
    ok_before = Counter(name for name, status in before_tasks if status in passed)
    ok_after = Counter(name for name, status in after_tasks if status in passed)
    not_ok_before = Counter(name for name, status in before_tasks if status not in passed)
    not_ok_after = Counter(name for name, status in after_tasks if status not in passed)
    reasons = {name: status for name, status in reversed(after_tasks) if status not in passed}
    reopened = open_task_names(after)
    found = []
    for name, count in ok_before.items():
        lost = count - ok_after[name]
        degraded = min(max(lost, 0), max(not_ok_after[name] - not_ok_before[name], 0))
        if degraded:
            found.append((name, reasons[name]))
        elif lost > reopened[name]:
            found.append((name, "removed"))
    return found


def reviewed_by_regressions(before: str, after: str) -> list[tuple[str, str]]:
    """書き込みの前に `Reviewed by` が ok（skipped を含む）だった完了タスクのうち、後で ok でなくなったもの。

    返り値は [(タスク名, 理由)]。理由は `completed_tasks_reviewed_by` の状態か、`removed`（Completed にも
    Current・Pending にも無い。消した・要約で見出しが崩れた・節の見出しを変えた・別の節へ移した）。
    `task_name` は番号を落とすので、同名のタスクは件数で比べる。書き込みの前から ok でなかったタスクは見ない。
    Completed に残ったまま ok でなくなった分は、そのまま返す（同じ書き込みで同名の ok でない完了タスクを消すと、
    その分は打ち消される）。Completed から消えた分は、書き込みの後に Current か Pending にある同名のタスク
    （再オープン。done guard が残りのタスクとして数える）の件数だけ差し引く。先に Pending へ足して次の書き込みで
    Completed から消す 2 回の形も通すため、前からあったものも数える（同名の別タスクが前から Current・Pending に
    あると、Completed から消す書き込みは通る。限界）。閉じていない fence の先を前と後の両方で構造として読む比較と、
    fence を追う読み方（done guard・検算と同じ）の比較の両方で見る（閉じていない fence を足して完了タスクを隠す形も止める）。
    steering write guard が書き込みの時点で止めるのに使う。
    """
    found = _regressions(_without_unclosed_fences(before), _without_unclosed_fences(after))
    seen = {name for name, _ in found}
    return found + [item for item in _regressions(before, after) if item[0] not in seen]

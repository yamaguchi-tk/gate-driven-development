"""リスクの段の読み手と、`risk-low:` の human check の承認を止める steering の書き込みの検査。

記録の書式の正本は `agents/gdd-request-code-crosscheck.md` § リスクの段（`.steering/<task>/request-crosscheck.md`）。
`低` と読むのは固定行の 1 形だけで、無い・読めない・崩れた記録は全部 `高` にする（`低` は human check を待たない根拠になる）。
依頼の原文（hook が作った `request.md`。形は `hooks/scripts/lib/request_capture.py`）が無い steering も `高` にする。
検査は `validate-steering-write.py` が呼ぶ。
"""
from __future__ import annotations

import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

try:
    from .patch_scoping import patch_text_of
    from .regular_file import lstat_or_none, read_regular_bytes
    from .state_write_projection import edit_misses_old_string, project_written_text
    from .steering_paths import is_state_md_path
except ImportError:  # hook とテストは top-level の module として読む
    _DIR = str(Path(__file__).resolve().parent)
    sys.path.insert(0, _DIR)
    try:
        from patch_scoping import patch_text_of
        from regular_file import lstat_or_none, read_regular_bytes
        from state_write_projection import edit_misses_old_string, project_written_text
        from steering_paths import is_state_md_path
    finally:
        sys.path.remove(_DIR)

RECORD = "request-crosscheck.md"
HEADING = "### リスクの段"
LOW_LINE = "リスクの段: 低"
# request_capture.py の BEGIN と同じ印（hook の import は重いので、ここに写す）
CAPTURE_BEGIN = b"<!-- gdd-request-capture:begin -->"

# `risk-low` の表記の揺れ（大文字・`_`・空白・`:`・U+2010 など。NFKC で全角も）も同じ承認として見る（広い側）
_RISK_LOW = re.compile(r"risk[^a-z0-9]{0,3}low")
# 見出しの深さ・字下げ・末尾の `#` を問わず、リスクの段の見出しとして数える行
_ANY_HEADING = re.compile(r"^#{1,6}\s*リスクの段\s*#*$")
# 行頭が `リスクの段` で、その後に `:` か `：` が来る行（後の段が上げた記録も含む）
_ANY_TIER_LINE = re.compile(r"^リスクの段\s*[:：]")

REASON = (
    "risk_low_approval",
    "state.md に `risk-low`（human check を待たない承認の evidence。表記の揺れを含む）を書いていますが、"
    f"`{RECORD}` のリスクの段が `低` と読めません（記録が無い・読めない・`高`・`判定できない`・形が崩れている・"
    "節や `リスクの段:` の行が 2 つある）か、依頼の原文がありません（`request.md` が無いか、hook の節で始まらない。写していない旨・runner や main が書いたもの・"
    "Codex・Cursor の steering を含む）。リスクの段が低でない steering は human check で本人の承認を待ちます。"
    "本人の承認なら evidence を `human:<自走上限の値>` にし、そうでなければ承認を書かずに human check を表示して"
    "ください。state.md の地の文で `risk-low` に触れているだけなら、その語を書かないでください",
)
UNPROJECTABLE_REASON = (
    "risk_low_approval",
    f"`{RECORD}` のリスクの段が `低` と読めない steering の state.md への Edit / MultiEdit で、`old_string` が書き込み前の"
    "テキストにそのまま見つからないか、空の `new_string` で改行ごと消える形です。書き込み後に `risk-low` の行が現れるかを"
    "確かめられないので止めます。state.md を Read し直し、`old_string` を今の内容のとおりに書くか、行ごと差し替えてください",
)


def _has_original_request(steering_dir: Path) -> bool:
    """依頼の原文があるか。例外は出さない（読めなければ無いとみなす）。

    原文は、hook が作った `request.md`（通常のファイルで、hook の節〔BEGIN〕で始まる）だけ。写していない旨・runner や
    main が書いたもの・無いものは原文ではない。state.md の欄では決めない（runner が書き漏らせ、後から消せる）。
    """
    path = steering_dir / "request.md"
    try:
        # read_regular_bytes は symlink の先を読む。hook は symlink の request.md を作らないので、原文に数えない
        request = None if path.is_symlink() else read_regular_bytes(path)
    except (OSError, ValueError):
        return False
    return request is not None and request.startswith(CAPTURE_BEGIN)


def read_risk_tier(steering_dir: Path) -> str:
    """`steering_dir` の `request-crosscheck.md` のリスクの段を `低` か `高` で返す。例外は出さない。

    `低` は次をすべて満たすときだけ。行は `\\n` だけで割り、各行の両端の空白を除いて見る。
    - 通常のファイルで、BOM の無い UTF-8 として読める（FIFO で止まらないよう `read_regular_bytes` で読む）
    - リスクの段の見出し（`#` の数・末尾の `#` を問わない）がちょうど 1 行で、それが `### リスクの段`
    - その後の最初の空でない行が `リスクの段: 低` で、`リスクの段:`・`リスクの段：` で始まる行がほかに無い
    - `判定できない` の語が無い
    - 依頼の原文がある（`_has_original_request`）
    """
    if not _has_original_request(Path(steering_dir)):
        return "高"
    try:
        data = read_regular_bytes(Path(steering_dir) / RECORD)
        if data is None or data.startswith(b"\xef\xbb\xbf"):
            return "高"
        text = data.decode("utf-8")
    except (OSError, ValueError):
        return "高"
    lines = [line.strip() for line in text.split("\n")]
    headings = [i for i, line in enumerate(lines) if _ANY_HEADING.match(line)]
    if len(headings) != 1 or lines[headings[0]] != HEADING or "判定できない" in text:
        return "高"
    if sum(1 for line in lines if _ANY_TIER_LINE.match(line)) != 1:
        return "高"
    first = next((line for line in lines[headings[0] + 1:] if line), "")
    return "低" if first == LOW_LINE else "高"


def _mentions_risk_low(text: str) -> bool:
    """`risk-low` の揺れを含むか（NFKC の後、バッククォートと `*` を除き、casefold して見る）。"""
    plain = unicodedata.normalize("NFKC", text).replace("`", "").replace("*", "").casefold()
    return bool(_RISK_LOW.search(plain))


def _risk_low_lines(text: str) -> Counter[str]:
    """`risk-low` の揺れを含む行の多重集合。

    改行は `Path.read_text()` と同じく `\r\n`・`\r` を `\n` にそろえてから割る。書き込み前（生の bytes）と
    書き込み後（Edit は `read_text` で読んだ全文、Write は `content` そのまま）で改行の扱いが違うので、
    そろえないと CRLF の state.md の既にある行を新しい行に数える。
    """
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return Counter(line for line in lines if _mentions_risk_low(line))


def _adds_risk_low_line(tool_name: str, tool_input: object, path: str) -> bool:
    """書き込み後の state.md に、書き込み前に無かった `risk-low` の行が現れるか。

    呼び出し側が `edit_misses_old_string` の Edit を先に止めるので、Edit / MultiEdit の素の置換はツールの結果と一致する。
    """
    after = project_written_text(tool_name, tool_input, path)
    if after is None:  # ApplyPatch と、宛先の違う Write は追加分の検査が受ける
        return False
    try:  # FIFO などで止まらないよう `read_regular_bytes` で読む
        data = read_regular_bytes(Path(path))
        before = "" if data is None else data.decode("utf-8", errors="replace")
    except (OSError, ValueError):
        before = ""
    return bool(_risk_low_lines(after) - _risk_low_lines(before))


def _misses_on_existing_state(tool_name: str, tool_input: object, path: str) -> bool:
    """既にある state.md への Edit / MultiEdit を、そのまま当てられないか（無いファイルは対象外）。

    通常のファイルでないもの（FIFO など）は `edit_misses_old_string` が読むと止まるので、読まずに当てられないとみなす。
    あるかを確かめられない（親に権限が無いなど）ものも、当てられないとみなす。
    """
    if tool_name not in ("Edit", "MultiEdit"):
        return False
    try:
        if lstat_or_none(Path(path)) is None:
            return False
    except ValueError:  # 符号化できないパス（lone surrogate など）には何も無い。`os.path.lexists` と同じ
        return False
    except OSError:
        return True
    try:
        if read_regular_bytes(Path(path)) is None:
            return True
    except (OSError, ValueError):
        return True
    return edit_misses_old_string(tool_name, tool_input, path)


def _patch_plus_lines(tool_name: str, tool_input: object) -> str:
    """ApplyPatch の生の patch の `+` で始まる行（`+++ ` も含む。`extract_added_lines` は飛ばす）。"""
    patch = patch_text_of(tool_name, tool_input) or ""
    return "\n".join(line[1:] for line in patch.split("\n") if line.startswith("+"))


def collect_risk_low_approval_violations(
    target_paths: list[str], chunks: list[str], tool_name: str = "", tool_input: object = None
) -> list[tuple[str, str]]:
    """触れた state.md の steering のリスクの段がどれも `低` でなければ、次のどれかで止める。

    - 追加分のどこか（ApplyPatch は生の `+` 行も）に `risk-low` の揺れがある。欄名・status・どのファイルの追加行かは
      問わない（広い側。ApplyPatch の行をファイルに割り当てた結果に頼らない）
    - 追加分をつないだもの（`risk` と `-low` を別の edit の `new_string` に分けた形）に `risk-low` の揺れがある
    - 既にある state.md への Edit / MultiEdit を、そのまま当てられない（`edit_misses_old_string`。ツールが引用符を
      正規化して当てる形と、空の `new_string` で改行ごと消す形は、書き込み後の全文を確かめられない）
    - Write / Edit / MultiEdit の書き込み後の state.md に、書き込み前に無かった `risk-low` の行が現れる
      （値だけを置換する Edit〔PR #31 Finding C〕と、`risk` と `-low` を別の Edit に分けた形）

    ApplyPatch の move で流れ込む移動元の中身は読まない。state.md を移動先にする patch は、`Origin Session` の検査
    （`origin_session_guard._moves_onto_state_md`）が移動元を読まずに止める。
    """
    states = [path for path in target_paths if is_state_md_path(path)]
    if not states or all(read_risk_tier(Path(path).parent) == "低" for path in states):
        return []
    added = [*chunks, "".join(chunks), _patch_plus_lines(tool_name, tool_input)]
    if any(_mentions_risk_low(chunk) for chunk in added):
        return [REASON]
    if any(_misses_on_existing_state(tool_name, tool_input, path) for path in states):
        return [UNPROJECTABLE_REASON]
    return [REASON] if any(_adds_risk_low_line(tool_name, tool_input, path) for path in states) else []

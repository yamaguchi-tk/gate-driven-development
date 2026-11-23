#!/usr/bin/env python3
"""Lint Approved Direction glob patterns in state.md.

Approved Direction の自走範囲 / 戻し条件に書かれた glob pattern が以下のルール
を満たしているか機械的に検査する（正本の見出しの形〔`## Approved Direction`〕では
`含むディレクトリ / モジュール glob:` の欄だけを読み〔glob の形でない語があれば欄を読まない〕、colon の形〔`Approved Direction:`〕は節の語のうち glob の形のものだけを拾い、`自走範囲` 以外の行の `/` の無い語は既知の拡張子のときだけ拾う）:

1. 単一ファイル固定 glob の禁止（`src/foo.ts` のような pattern を拒否）
   - rename / split で silent に過剰発動するため
2. 全域 glob × security-sensitive path の交差検出
   - `**/*.ts` のような全域 glob が auth / secret / webhook / payload 系 path
     と交差する場合、`design_detail_only` 範囲を超える可能性を警告
3. 自走上限と `Human Check Status` の `human:` evidence が、自走のマージに入らない形（WARN のみ）
   - `references/post-merge-qa.md` § 入口の読み方と手順 2 は、両者を完全一致で比べる。
     注記を付けた値、表の外の `マージ…` の値、両者の不一致、承認前でない status の `human:` で始まらない
     evidence では、自走のマージに入れない（判定は hooks/scripts/lib/autonomy_value.py）。警告するのは、自走上限か
     `human:` の evidence の値が自走のマージを指しうる値（`マージ` を含み、`PR マージ後検証 / 再学習まで` で始まらない）か、
     注記を付けた `PR マージ後検証 / 再学習まで` のときだけで、`human:` で始まらない evidence は自走上限が前者のときだけ見る

正本: `references/rollback-patterns.md` § Approved Direction glob 粒度 guard

Exit code:
  0: lint pass（WARN を含む。自走範囲を検査したことに数える glob が無いときも 0 で、--quiet でなければ INFO を出す）
  1: lint fail（単一ファイル固定 glob 検出）
  2: usage error（state.md も --pattern も無い、または state.md が無い）

Usage:
  lint-approved-direction.py <path/to/state.md>
  lint-approved-direction.py --pattern '<glob pattern>' [--pattern ...]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

# Security-sensitive path patterns (fallback if reviewer-selection.md is not
# parseable; aligned with gdd-security-reviewer trigger conditions).
SECURITY_SENSITIVE_PATTERNS = (
    r"(?i)\bauth(?:n|z)?\b",
    r"(?i)\bsecret",
    r"(?i)\btoken",
    r"(?i)\bwebhook",
    r"(?i)\bpayload",
    r"(?i)\bcredential",
    r"(?i)\bpii\b",
    r"(?i)\bsigna?ture",
    r"(?i)\bsensitive",
)

# 自走上限と human: の evidence の読み方は、steering の書き込み hook と共有する（hooks/scripts/lib/autonomy_value.py）。
# top-level module として読む（`from lib.X` にすると scripts/lib と衝突する。scripts/gdd_task_binding.py と同じ）。
_LIB_DIR = str(Path(__file__).resolve().parents[1] / "hooks" / "scripts" / "lib")
sys.path.insert(0, _LIB_DIR)
try:
    from autonomy_value import MERGE_AUTONOMY_LIMITS, autonomy_value_notes  # noqa: E402,F401
finally:
    if _LIB_DIR in sys.path:
        sys.path.remove(_LIB_DIR)
# 正本の書式（見出しの節）で glob を書く欄（references/requirements-template.md § Approved Direction テンプレート）
GLOB_FIELD_LABEL = "含むディレクトリ / モジュール glob"
# ATX の見出し（`#123` のような見出しでない行は含まない）
HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})(?:\s+(.*?))?\s*$")
GLOB_FIELD_RE = re.compile(r"^(\s*)[-*]?\s*" + re.escape(GLOB_FIELD_LABEL) + r"\s*[:：]\s*(.*?)\s*$")
CONTINUATION_RE = re.compile(r"^(\s*)[-*]\s+(.*?)\s*$")
# 続きの行の欄名（`明示的に除外する範囲:` など。`/`・`.` を含む語〔`src/foo.ts:42`〕は欄名にしない）
CONTINUATION_LABEL_RE = re.compile(r"^[\-\*]?\s*[^\s:：=/.][^:：=/.]*?\s*[:：=]")
# 自走範囲の検査に数える語の文字（パスと glob の記号と、末尾の `:行番号` だけ。`!`・括弧などの記号、先頭の `-`、全角の文字を含まない）
SCOPE_WORD_RE = re.compile(r"^[A-Za-z0-9_.*?\[\]{}/][A-Za-z0-9_.*?\[\]{}/-]*(?::[\d\-]+)?$")
# 語の区切り（見出しの形の split_tokens と colon の形で同じにする）
TOKEN_SEP_RE = re.compile(r"[,、，;|／・\s]+")

# Glob meta characters
GLOB_META = "*?[]{"
# colon の形の `自走範囲` 以外の行で、`/` の無い語を単一ファイルとみなす拡張子（`戻し条件` などの自由文の
# host:port・ホスト名を拾わない。この拡張子で終わる自由文の語〔`Node.js`・`requirements.md`〕は拾う）
COLON_SLASHLESS_FILE_RE = re.compile(r"\.(?:ts|js|py|tf|md)(?::[\d\-]+)?$")


def is_single_file_pattern(pattern: str) -> bool:
    """Return True if pattern points to a single fixed file (no glob meta).

    Examples:
      'src/foo.ts'           -> True   (no glob meta, has file extension)
      'src/foo'              -> False  (no extension, could be a directory)
      'src/foo/**'           -> False  (has glob meta)
      'src/**/*.ts'          -> False  (has glob meta)
      'src/foo.ts:42'        -> True   (file + line, treat as single file)
    """
    # Strip line/range suffixes like ':42' or ':10-20'
    cleaned = re.sub(r":[\d\-]+$", "", pattern).strip()
    if not cleaned:
        return False
    # If any glob meta character exists, it's not single-file-fixed
    if any(c in cleaned for c in GLOB_META):
        return False
    # If it ends with '/', it's a directory reference (not single-file)
    if cleaned.endswith("/"):
        return False
    # If the last segment has a '.', treat as file (heuristic)
    last_segment = cleaned.split("/")[-1]
    return "." in last_segment and not last_segment.startswith(".")


def is_global_glob(pattern: str) -> bool:
    """Return True for patterns like '**/*' or '**/*.ext' that match very broadly.

    Examples:
      '**/*'        -> True
      '**/*.ts'     -> True
      '**/*.{ts,js}' -> True
      'src/**'      -> False  (scoped under src/)
      'src/**/*.ts' -> False  (scoped under src/)
    """
    cleaned = pattern.strip()
    return cleaned.startswith("**/") or cleaned == "**"


def intersects_security_sensitive(pattern: str) -> list[str]:
    """Return list of matched security-sensitive markers in the pattern."""
    matches = []
    for sec_pat in SECURITY_SENSITIVE_PATTERNS:
        if re.search(sec_pat, pattern):
            matches.append(sec_pat)
    return matches


def lint_pattern(pattern: str) -> tuple[int, list[str]]:
    """Lint a single pattern. Returns (severity, messages).

    severity:
      0: pass
      1: warning (global glob × security-sensitive, recommended escalation)
      2: error (single-file fixed)
    """
    messages = []
    severity = 0

    if is_single_file_pattern(pattern):
        messages.append(
            f"ERROR: single-file-fixed glob '{pattern}': "
            "rename/split で silent に過剰発動します。最低限ディレクトリ単位 "
            "（例: 'src/foo/**'）にしてください"
        )
        severity = max(severity, 2)

    if is_global_glob(pattern):
        sec_matches = intersects_security_sensitive(pattern)
        if sec_matches:
            messages.append(
                f"WARN: global glob '{pattern}' × security-sensitive marker "
                f"{sec_matches}: design_detail_only の自走範囲を超える可能性。"
                "human_recheck_required への昇格を検討してください"
            )
            severity = max(severity, 1)
        else:
            messages.append(
                f"INFO: global glob '{pattern}': scope が広いため、"
                "security-sensitive な変更時は human_recheck_required を検討してください"
            )

    return severity, messages


def split_tokens(value: str) -> list[str]:
    tokens = (t.strip("`'\"") for t in TOKEN_SEP_RE.split(value))
    return [t for t in tokens if t]


def is_glob_shape(token: str) -> bool:
    """glob として検査する語か。

    glob meta を含む語は `/` を含むときだけ（`[TBD]`・`**未定**` は外す）、meta の無い語は、
    英字で始まる拡張子つきの単一ファイルのときだけ（`etc.`・`v1.2`・`S-1/S-2` は外す）受理する。
    """
    if any(c in token for c in GLOB_META):
        return "/" in token
    return is_single_file_pattern(token) and re.search(r"\.[A-Za-z]\w*(?::[\d\-]+)?$", token) is not None


def is_scope_word(token: str) -> bool:
    """自走範囲を検査したことに数える語か（glob の形で、パスと glob の記号だけでできている）。"""
    return is_glob_shape(token) and SCOPE_WORD_RE.match(token) is not None


def is_heading_glob_word(token: str) -> bool:
    """見出しの形の glob の欄で読む語か（glob の形で、`!`・`-` の否定・除外で始まらない）。

    `app/(auth)/**`・`packages/@org/**`・`docs/設計/**` のような記号・全角の文字を含むパスも読む。
    """
    return is_glob_shape(token) and not token.startswith(("!", "-"))


def read_heading_glob_words(text: str) -> list[str] | None:
    """正本の書式（`## Approved Direction` の見出しの節）から、`含むディレクトリ / モジュール glob:` の欄の語を取り出す。

    見出しの節が無ければ None を返す。欄の値と、欄の行より深く字下げした続きの箇条を読む。自由文の欄（`自走範囲` の値、
    `承認後の到達点`、`事前スキャン対象 glob` など）は読まない。値が `<` で始まるもの（テンプレートの
    記入例のまま）は読まない。節は、同じ階層以上の次の見出しで終わる。
    """
    tokens: list[str] = []
    found = False
    block_level = 0
    field_indent: int | None = None
    for line in text.splitlines():
        heading = HEADING_RE.match(line)
        if heading:
            level, title = len(heading.group(1)), heading.group(2) or ""
            if title.startswith("Approved Direction"):
                found, block_level, field_indent = True, level, None
                continue
            if block_level and level <= block_level:
                block_level, field_indent = 0, None
            continue
        if not block_level:
            continue
        field = GLOB_FIELD_RE.match(line)
        if field:
            field_indent = len(field.group(1))
            if not field.group(2).startswith("<"):
                tokens.extend(split_tokens(field.group(2)))
            continue
        item = CONTINUATION_RE.match(line)
        if field_indent is not None and item and len(item.group(1)) > field_indent:
            tokens.extend(split_tokens(item.group(2)))
        elif line.strip():
            field_indent = None
    return tokens if found else None


def extract_patterns_from_state_md(state_path: Path) -> list[str]:
    """Extract glob patterns from Approved Direction block of state.md.

    見出しの形（正本）は read_heading_glob_words で読む。以下は colon の形の読み方。

    Approved Direction block format (loosely):

      Approved Direction:
        自走範囲: src/foo/**, tests/foo/**
        戻し条件: when ...

    Patterns are the words in the block that have a glob shape (is_glob_shape);
    other words are skipped one by one. Outside the `自走範囲` line, words without '/'
    count only when they end with a known extension (COLON_SLASHLESS_FILE_RE), since
    those lines are free text. A block ends at a heading or the next top-level field;
    a bulleted block also ends at a sibling bullet with such a field.
    """
    if not state_path.is_file():
        return []
    return read_state_patterns(state_path.read_text(encoding="utf-8", errors="replace"))[0]


def read_state_patterns(text: str) -> tuple[list[str], list[str]]:
    """(lint する pattern, 自走範囲を検査したことに数える pattern) を返す。

    colon の形では、`戻し条件` の行・`自走範囲外:` の行・括弧の注記・欄名つきの続きの行
    （`明示的に除外する範囲:` など。glob の欄を除く）とその下の箇条・自走範囲の検査に数えない語
    （is_scope_word が偽の語。自由文・`except`・`!` の否定など）を含む行の glob も lint するが、自走範囲の検査には数えない。
    """
    words = read_heading_glob_words(text)
    if words is not None:
        # glob の形でない語（`S-1/S-2`、`**` の無い `src/notify`、自由文、`!src/legacy/**` の否定）が 1 つでもあれば欄を読まない
        checked = words if all(is_heading_glob_word(w) for w in words) else []
        return checked, checked
    patterns: list[str] = []
    scope_patterns: list[str] = []
    in_block = False
    bullet_indent: int | None = None
    scope_indent: int | None = None
    label_indent: int | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        indent = len(line) - len(line.lstrip())
        if re.match(r"^[\-\*]?\s*Approved Direction\s*[:=]", stripped):
            in_block = True
            bullet_indent = indent if stripped[0] in "-*" else None
            scope_indent = None
            label_indent = None
            continue
        if in_block:
            # Block ends at a heading or the next top-level field (for a bulleted block, also a sibling bullet
            # whose field is one like `Route In Progress:`)
            field = re.sub(r"^[\-\*]\s*", "", stripped)
            other_field = re.match(r"^[A-Z][A-Za-z ]+\s*[:=]", field) and not field.startswith(
                ("自走範囲", "戻し条件", "scope", "boundary", "範囲", "条件")
            )
            sibling = bullet_indent is not None and stripped[0] in "-*" and indent <= bullet_indent
            if HEADING_RE.match(line) or (other_field and (sibling or field == stripped)):
                in_block = False
                continue
            # `自走範囲:` の行と、それより深く字下げした続きの行（`含むディレクトリ / モジュール glob:` を含む）
            if scope_indent is not None and indent <= scope_indent:
                scope_indent = None
            # 欄名には注記（`自走範囲（S-1）:`。括弧の中身は問わない）と `=` を許す。`自走範囲外:`・`自走範囲の補足:` は別の欄
            scope_label = re.match(r"^[\-\*]?\s*自走範囲\s*(?:[（(]([^）)]*)[）)]\s*)?[:：=]", stripped)
            if scope_label:
                scope_indent = indent
            scope_line = scope_indent is not None
            # 欄名つきの続きの行（`明示的に除外する範囲:` など。glob の欄を除く）より深い箇条は、その欄の中身
            if label_indent is not None and (not scope_line or indent <= label_indent):
                label_indent = None
            glob_field = GLOB_FIELD_RE.match(line)
            labeled = scope_line and not scope_label and not glob_field and CONTINUATION_LABEL_RE.match(stripped)
            nested = label_indent is not None
            if labeled and not nested:
                label_indent = indent
            # 自走範囲の検査に数えるのは、`自走範囲` の行の値と、欄名の無い続きの行・glob の欄の行のうち、
            # 語がすべてパスと glob の形のもの（`リポジトリ全体、src/legacy/** は除く` の除外の glob は数えない）
            if glob_field:
                value = glob_field.group(2)
            elif scope_label:
                value = stripped[scope_label.end():]
            else:
                value = re.sub(r"^[\-\*]\s+", "", stripped)
            value_words = split_tokens(value)
            counts_as_scope = (
                scope_line
                and not labeled
                and not nested
                and all(is_scope_word(w) for w in value_words)
            )
            # `自走範囲` の行は、欄名の `自走範囲` 自体は語にせず、欄名の後ろの値を区切る（欄名と値の間に空白が
            # 無くても値を読む）。ほかの行は行全体を区切る。括弧の注記からは単一ファイルだけを拾う（除外の注記の
            # ディレクトリ glob・全域 glob を、検査した自走範囲に数えない）
            if scope_label and scope_label.group(1):
                for token in TOKEN_SEP_RE.split(scope_label.group(1)):
                    token = token.strip("`'\"")
                    if is_glob_shape(token) and is_single_file_pattern(token):
                        patterns.append(token)
            for token in TOKEN_SEP_RE.split(stripped[scope_label.end():] if scope_label else stripped):
                token = token.strip("`'\"")
                if not token or token in ("自走範囲:", "戻し条件:", "-"):
                    continue
                # 語ごとに、glob の形（is_glob_shape）のものだけを pattern にする
                if is_glob_shape(token) and (scope_line or "/" in token or COLON_SLASHLESS_FILE_RE.search(token)):
                    patterns.append(token)
                    if counts_as_scope:
                        scope_patterns.append(token)
    return patterns, scope_patterns


def lint_human_evidence(text: str) -> list[str]:
    """自走上限と `human:<値>` の evidence が、自走のマージに入らない形なら WARN を返す。"""
    return autonomy_value_notes(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "state_md",
        nargs="?",
        help="Path to state.md to lint (extracts Approved Direction patterns)",
    )
    parser.add_argument(
        "--pattern",
        action="append",
        default=[],
        help="Lint individual pattern (can be repeated)",
    )
    parser.add_argument(
        "--no-human-evidence",
        action="store_true",
        help="Skip the 自走上限 / human: evidence check (the steering write hook checks the written text itself for Write/Edit/MultiEdit)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress INFO messages",
    )
    args = parser.parse_args()

    patterns: list[str] = list(args.pattern)
    if args.state_md:
        state_path = Path(args.state_md)
        if not state_path.is_file():
            print(f"usage: state.md not found: {args.state_md}", file=sys.stderr)
            return 2
        text = state_path.read_text(encoding="utf-8", errors="replace")
        for msg in [] if args.no_human_evidence else lint_human_evidence(text):
            print(msg)
        rejected = [w for w in read_heading_glob_words(text) or [] if not is_heading_glob_word(w)]
        if rejected:
            print(
                f"WARN: glob field not read: non-glob words {rejected} in '{GLOB_FIELD_LABEL}'。"
                "glob を検査していないので、自走範囲を手で照らしてください"
            )
        state_patterns, scope_patterns = read_state_patterns(text)
        if not scope_patterns and not args.quiet:
            print(
                f"INFO: no Approved Direction patterns found in {args.state_md}",
                file=sys.stderr,
            )
        patterns.extend(state_patterns)
    elif not patterns:
        print("usage: lint-approved-direction.py <state.md> | --pattern PAT", file=sys.stderr)
        return 2

    overall = 0
    for p in patterns:
        sev, msgs = lint_pattern(p)
        for msg in msgs:
            if args.quiet and msg.startswith("INFO:"):
                continue
            print(msg)
        overall = max(overall, sev)

    if overall == 2:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

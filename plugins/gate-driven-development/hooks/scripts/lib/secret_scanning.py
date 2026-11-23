"""`.steering/**` 書込みに対する秘匿情報・PII・省略記法の検出の純粋関数群。

`validate-steering-write.py`（Copilot レビュー是正、コード健全性の目安である
1500 行を再度超過したため分離）
から抽出。ここに置く定数・関数は他モジュールへの依存を持たない（`re` のみ）ため、
`hooks/scripts/lib/patch_scoping.py` / `hooks/scripts/lib/transcript.py` のような
sys.modules 衝突回避 bootstrap は不要。
"""

from __future__ import annotations

import re

EMAIL_RE = re.compile(
    r"\b([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b",
    re.IGNORECASE,
)
# 省略記法検出: migration/conversion タスクで原文の一部を ...省略 で書き落とすと、
# 実装で原文保全が破れる。コードブロック外でも弾く。
ELLIPSIS_RE = re.compile(
    r"(\.\.\.\s*省略|…\s*省略|（略）|\(略\)|省略\.\.\.|省略…|（\s*中略\s*）|\(\s*中略\s*\))"
)
AWS_ACCOUNT_ID_RE = re.compile(r"(?<!\d)(\d{12})(?!\d)")
AWS_ACCOUNT_CONTEXT_RE = re.compile(r"(aws|account|アカウント|role|arn:aws)", re.IGNORECASE)
# 既知接頭辞の token 実値検出。これは **接頭辞 allowlist であり網羅ではない**
# （接頭辞を持たない token や未登録サービスの key は素通りする。SECURITY.md 参照）。
#
# 前方境界に `\b` を使わない: Python の `\b` は `\w` 基準で、`\w` は日本語文字と `_` を
# 単語構成文字に含む。分かち書きしない日本語では `トークンはghp_...` が最も自然な
# 書き方なのに `\b` だと境界が立たず素通りする（実測で確認）。明示の lookbehind に
# して、日本語直後・`_` 直後を拾いつつ base64 塊の途中の偶発一致は除外する。
#
# 最小長は「実 token を取りこぼさない」かつ「説明用プレースホルダーを拾わない」下限。
# 判定は **区切り文字（`-` / `_`）を含まない連続長**で見る。`xoxb-your-token-here` の
# ように区切りで細切れなプレースホルダーは連続長が下限に届かず、
# `xoxb-1234567890123-...` のような実 token だけが残る。
# 例外は Slack app-level token（`xapp-1-A01ABC-...`）で、第 1 セグメントが 1 文字の
# ため連続長では見られない。ここだけ区切り込みの全長 30 文字で下限を掛ける。
_NO_ALNUM_BEFORE = r"(?<![A-Za-z0-9])"
SECRET_MARKER_RE = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----"
    # AWS access key ID（永続 AKIA / 一時 ASIA）。実 key は接頭辞 + 16 文字の固定長。
    # `ASIA` は英単語でもあるため前後を締める（`REGION ASIAPACIFIC...` の誤検知回避）。
    rf"|{_NO_ALNUM_BEFORE}(?:AKIA|ASIA)[0-9A-Z]{{16}}(?![0-9A-Z])"
    # GitHub token（ghp_ PAT classic / gho_ OAuth / ghu_ user-to-server /
    # ghs_ server-to-server / ghr_ refresh）。実 token は接頭辞後 36 文字。
    rf"|{_NO_ALNUM_BEFORE}gh[pousr]_[A-Za-z0-9]{{20,}}"
    # GitHub fine-grained PAT。実 token は `github_pat_` + 22 文字 + `_` + 59 文字。
    # 連続長 22 で第 1 セグメントを見る（`_` を含めると `github_pat_YOUR_TOKEN_HERE`
    # のようなプレースホルダーまで拾う）。
    rf"|{_NO_ALNUM_BEFORE}github_pat_[A-Za-z0-9]{{22,}}"
    # Slack token（xoxb- bot / xoxp- user / xoxc-・xoxd- ブラウザセッション ほか）。
    # `xoxo-` は token 種別に無く、英語の定型句（`xoxo-everyone`）を拾うため入れない。
    rf"|{_NO_ALNUM_BEFORE}xox[abcdeprs]-[0-9A-Za-z]{{10,}}"
    # Slack app-level token（Socket Mode 用。`connections:write` を持つ実害のある秘密）
    rf"|{_NO_ALNUM_BEFORE}xapp-[0-9A-Za-z-]{{30,}}"
)
SENSITIVE_VALUE_RE = re.compile(
    r"\b(password|passwd|api[_-]?key|access[_-]?token|auth[_-]?token|secret|credential)\b"
    r"\s*[:=]\s*([^\s`\"']{8,})",
    re.IGNORECASE,
)
# 省略記法の検出の除外パターン（Attempts セクション内は記録用途なので除外）
ELLIPSIS_EXCLUDE_SECTIONS = ("#### Attempts", "#### 試行記録")
LOCAL_PATH_PATTERNS = [
    re.compile(r"/Users/[^/\s]+/[^\s`\"']*"),
    re.compile(r"/home/[^/\s]+/[^\s`\"']*"),
    re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+\\[^\s`\"']*"),
]
EXAMPLE_EMAIL_DOMAINS = {
    "example.com",
    "example.org",
    "example.net",
    "localhost",
    "invalid",
    "test.local",
}
# RED Evidence の必須項目 `Worktree:` 用の例外は、フィールド行そのもの
# （ラベル + 値のみ）にしか適用しない。行頭一致だけだと `- Worktree: <path> --
# 追記 <別の漏洩path>` のように正規の値の後ろへ別のパスを付け足す形で素通りできる
# （実測で確認）ため、値の後に余分な内容がない行だけを許す fullmatch にする。
WORKTREE_FIELD_LINE_RE = re.compile(r"^-\s*Worktree:\s*`?[^\s`]+`?\s*$")
# legacy metadata の `Active Worktree Path` も同じく、欄の行そのもの（ラベル + 値のみ）に限る。
# 部分文字列一致だと、表の行や本文にこの語があるだけで、同じ行の別のパスまで素通りする。
ACTIVE_WORKTREE_FIELD_LINE_RE = re.compile(r"^(?:-\s*)?Active Worktree Path:\s*`?[^\s`]+`?\s*$")


def find_email(line: str) -> str | None:
    for match in EMAIL_RE.finditer(line):
        domain = match.group(2).lower()
        if domain in EXAMPLE_EMAIL_DOMAINS:
            continue
        return match.group(0)
    return None


def find_local_path(line: str) -> str | None:
    # RED Evidence の必須項目 `Worktree:` の値もローカル絶対パスになる。
    # 部分文字列一致だと本文中の「Worktree」という語だけで無関係な漏洩パスまで
    # 素通りする（fail-open）。フィールド行全体との fullmatch に絞る（行頭一致だけだと
    # 値の後に別のパスを付け足して素通りできる）。
    stripped = line.strip()
    if WORKTREE_FIELD_LINE_RE.match(stripped) or ACTIVE_WORKTREE_FIELD_LINE_RE.match(stripped):
        return None
    for pattern in LOCAL_PATH_PATTERNS:
        match = pattern.search(line)
        if match:
            return match.group(0)
    return None


def find_ellipsis(line: str, in_exclude_section: bool) -> str | None:
    # コードブロック内も対象にする: YAML/コード例の中で「...省略」されると
    # そのまま実装にコピーされるため、放置できない。
    if in_exclude_section:
        return None
    match = ELLIPSIS_RE.search(line)
    if match:
        return match.group(0)
    return None


def find_aws_account_id(line: str, in_code_block: bool) -> str | None:
    if in_code_block:
        return None
    if not AWS_ACCOUNT_CONTEXT_RE.search(line):
        return None
    match = AWS_ACCOUNT_ID_RE.search(line)
    if match:
        return match.group(1)
    return None


def find_secret_marker(line: str) -> str | None:
    match = SECRET_MARKER_RE.search(line)
    if match:
        return match.group(0)
    return None


def find_sensitive_value(line: str, in_code_block: bool) -> str | None:
    if in_code_block:
        return None
    match = SENSITIVE_VALUE_RE.search(line)
    if match:
        return match.group(1)
    return None

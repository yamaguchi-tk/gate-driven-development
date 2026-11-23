#!/usr/bin/env python3
"""軽いレーンの独立レビュー（root CLAUDE.md 手順 6）に渡す「呼び出し元の候補」を列挙する。

使い方: git diff <base>..<tip> -- . ':(exclude)review-log/' | python3 scripts/light-lane-review-candidates.py <repo_root>

差分の変更行（+/-）とハンクの見出しから、関数名・クラス名・shell 関数名・大文字の定数名を
抜き出し、`git grep -w` で repo の追跡ファイルを引いた `ファイル:行` をそのまま出す。
main の判断は入れない。同じ差分・同じ repo の状態なら同じ出力になる。
網羅は保証しない（名前で引くだけで、別名での呼び出しや、同じ入力を読む別の実装は拾えない）。
Markdown の差分からは抜き出さない。一致が多すぎる名前は件数だけを出す。
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

MAX_REFS = 30
# これより多く一致する名前（main・run など）は docs や CHANGELOG で埋まり、起点にならないので件数だけ出す
MAX_LISTED_TOTAL = 100
PATTERNS = (
    re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)"),
    re.compile(r"^\s*class\s+([A-Za-z_]\w*)"),
    re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)"),
    re.compile(r"^\s*(?:function\s+)?([A-Za-z_][\w-]*)\s*\(\)\s*\{"),
    re.compile(r"^\s*(?:export\s+)?(?:const|let|var)?\s*([A-Z][A-Z0-9_]{2,})\s*(?::[^=]*)?=(?!=)"),
)
HUNK_RE = re.compile(r"^@@ [^@]* @@ ?(.*)$")
FILE_RE = re.compile(r"^diff --git a/(.*) b/(.*)$")


def _names(text: str) -> set[str]:
    return {m.group(1) for pattern in PATTERNS if (m := pattern.match(text))}


def extract_symbols(diff: str) -> list[str]:
    symbols: set[str] = set()
    scan = False
    in_hunk = False
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            # 空白・非 ASCII を含むパスは git が引用符で囲むので、外してから読む
            file_match = FILE_RE.match(line.replace('"', ""))
            scan = not (file_match and file_match.group(1).endswith(".md") and file_match.group(2).endswith(".md"))
            in_hunk = False
            continue
        hunk = HUNK_RE.match(line)
        if hunk:
            in_hunk = True
            if scan:
                symbols |= _names(hunk.group(1))
            continue
        if scan and in_hunk and line[:1] in "+-" and line:
            symbols |= _names(line[1:])
    return sorted(symbols)


def references(symbol: str, repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "grep", "--no-color", "-z", "-n", "-w", "-F", "-I", "-e", symbol, "--", ".", ":(exclude)review-log/"],
        capture_output=True, check=False,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(f"git grep failed for {symbol!r}: {result.stderr.decode(errors='replace').strip()}")
    # -z で区切りを NUL にする（パスに ':' を含んでも分けられる）。レコードは `パス NUL 行番号 NUL 本文 \n`。
    # bytes のまま、パスと行番号は NUL まで、本文は \n までを読む（text=True は \r を \n に変え、splitlines は
    # U+2028・\x0c でも分ける。パスは改行を含みうるので、レコード全体を \n で割らない）
    out = result.stdout
    hits: list[tuple[str, int]] = []
    pos = 0
    while pos < len(out):
        path_end = out.index(b"\0", pos)
        number_end = out.index(b"\0", path_end + 1)
        text_end = out.find(b"\n", number_end + 1)
        hits.append((out[pos:path_end].decode(errors="replace"), int(out[path_end + 1:number_end])))
        pos = len(out) if text_end < 0 else text_end + 1
    return [f"{path}:{number}" for path, number in sorted(hits)]


def render(symbols: list[str], repo_root: Path) -> str:
    if not symbols:
        return "候補なし（差分から抜き出せる関数名・定数名が無い）\n"
    out: list[str] = []
    for symbol in symbols:
        refs = references(symbol, repo_root)
        if len(refs) > MAX_LISTED_TOTAL:
            out.append(f"- `{symbol}`（{len(refs)} 件。{MAX_LISTED_TOTAL} 件を超えるので一覧を省く）")
            continue
        out.append(f"- `{symbol}`（{len(refs)} 件）")
        out.extend(f"  - {ref}" for ref in refs[:MAX_REFS])
        if len(refs) > MAX_REFS:
            out.append(f"  - …ほか {len(refs) - MAX_REFS} 件")
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: light-lane-review-candidates.py <repo_root> < diff", file=sys.stderr)
        return 2
    repo_root = Path(argv[1])
    check = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True, check=False)
    if check.returncode != 0 or check.stdout.strip() != "true":
        print(f"not a git checkout: {repo_root}", file=sys.stderr)
        return 1
    sys.stdout.write(render(extract_symbols(sys.stdin.read()), repo_root))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

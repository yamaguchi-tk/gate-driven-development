#!/usr/bin/env python3
"""diff で新規追加された Python の module-level 関数・クラス・定数のうち、テスト以外から
参照 0 件のものを列挙する report-only スクリプト。

**block しない**（exit code は常に 0）。`gdd-completion-check` から呼ばれ、レビュー時の
判断材料として finding を提示するだけで、gate 判定（fail-on / exit 1）には使わない。

開いた入力の扱い（このスクリプト自身が対象とする入力の限界を開示する）:
- 対象は Python の module-level def / class / 定数のみ。ネストした関数・メソッド・
  非 Python 言語（shell / TypeScript 等）は対象外（限界として開示する。静的解析なしで
  scope を広げると誤検知が支配的になる）
- 参照カウントは tokenize の `NAME` トークン一致による best-effort であり、AST・import
  解決は行わない。re-export 経由の呼び出しや `getattr` 等の動的参照は検出できない
  （限界として開示する）
- git のデフォルト設定（`core.quotepath=true`）では非 ASCII 文字を含むファイルパスが
  `"b/\\346..."` のような二重引用符 + オクタルエスケープで diff に出力され、
  `_FILE_HEADER_RE` はこの形式を認識しない。該当ファイルは新設シンボルの検出対象から
  漏れる（限界として開示する。独立レビュー low finding。対応は follow-up）
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
import tokenize
from pathlib import Path

EXCLUDE_DIRS = {
    ".git",
    ".gdd",
    ".steering",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "vendor",
    "build",
    "dist",
}

# top-level（行頭に `+` 直後、インデント無し）の def / class / 定数代入だけを対象にする。
_DEF_RE = re.compile(r"^\+(?:async\s+def|def|class)\s+([A-Za-z_][A-Za-z0-9_]*)")
_CONST_RE = re.compile(r"^\+([A-Za-z_][A-Za-z0-9_]*)\s*(?::[^=]+)?=(?!=)")
_FILE_HEADER_RE = re.compile(r"^\+\+\+ b/(.+)$")


def is_test_path(path: str) -> bool:
    p = Path(path)
    if "tests" in p.parts:
        return True
    name = p.name
    return name.startswith("test_") or name.endswith("_test.py")


def parse_added_symbols(diff_text: str) -> dict[str, set[str]]:
    """unified diff テキストから {file_path: {新設シンボル名, ...}} を返す。"""
    result: dict[str, set[str]] = {}
    current_file: str | None = None
    for line in diff_text.splitlines():
        header = _FILE_HEADER_RE.match(line)
        if header:
            current_file = header.group(1)
            continue
        if current_file is None or not current_file.endswith(".py"):
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        m = _DEF_RE.match(line)
        if m:
            result.setdefault(current_file, set()).add(m.group(1))
            continue
        m = _CONST_RE.match(line)
        if m:
            result.setdefault(current_file, set()).add(m.group(1))
    return result


def count_references(repo_root: Path, symbol: str, defining_file: str) -> int:
    """`symbol` の実参照数（テスト以外・定義自身の出現を除く）を返す。

    出現の数え方は tokenize の `NAME` トークンに限定する。コメント・docstring・文字列
    リテラルは tokenize の時点で `COMMENT` / `STRING` トークンとして丸ごと扱われ、
    その中身が `NAME` トークンへ分解されることはない。これにより `API_URL =
    os.getenv("API_URL")` の文字列リテラル内の自己参照や、コメント中の言及を実参照として
    誤カウントしない（PR レビュー指摘: 正規表現の単語境界一致はコメント・文字列内の出現も
    実参照として数えてしまい、本当は参照 0 件のシンボルを見逃していた）。
    定義行の除外ロジック自体は変更していない（独立レビュー medium finding 対応済みの
    「行全体を除外せず定義自身の1出現だけを差し引く」動作を維持する）。
    """
    count = 0
    for path in repo_root.rglob("*.py"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        rel = str(path.relative_to(repo_root))
        if is_test_path(rel):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        lines = text.splitlines()
        name_hits_by_row: dict[int, int] = {}
        try:
            for tok in tokenize.generate_tokens(io.StringIO(text).readline):
                if tok.type == tokenize.NAME and tok.string == symbol:
                    row = tok.start[0]
                    name_hits_by_row[row] = name_hits_by_row.get(row, 0) + 1
        except (tokenize.TokenError, SyntaxError, IndentationError):
            continue
        for row, matches in name_hits_by_row.items():
            line = lines[row - 1] if 0 < row <= len(lines) else ""
            stripped = line.strip()
            # 定義行の除外は、新設シンボル検出（_DEF_RE / _CONST_RE）と同じ「行頭に
            # インデント無し」の制約を課す。行全体をスキップするのではなく「定義自身の
            # 出現1件」だけを差し引く。行全体をスキップすると、`new_helper =
            # staticmethod(new_helper)` のような同一ファイル内の再代入参照（LHS が定義、
            # RHS が実参照）まで丸ごと除外され、実際に参照されているシンボルを 0 件と
            # 誤検知していた（独立レビュー medium finding: 受理集合の非対称）。
            is_top_level_line = bool(line) and not line[:1].isspace()
            is_definition_line = rel == defining_file and is_top_level_line and (
                stripped.startswith(f"def {symbol}")
                or stripped.startswith(f"async def {symbol}")
                or stripped.startswith(f"class {symbol}")
                or stripped.startswith(f"{symbol} ")
                or stripped.startswith(f"{symbol}:")
                or stripped.startswith(f"{symbol}=")
            )
            if is_definition_line:
                matches -= 1
            count += max(matches, 0)
    return count


def find_unreferenced_new_symbols(repo_root: Path, base_ref: str) -> tuple[list[dict[str, str]], str | None]:
    """戻り値は (findings, error)。`error` は git diff 実行自体が失敗した場合の理由文字列で、
    正常時は `None`。呼び出し側は `error` が非 `None` のとき「新設シンボル無し」と
    「スキャン自体が失敗した」を区別して扱う（独立レビュー medium finding: git diff 失敗時に
    `check=False` の空 stdout をそのまま「該当なし」として報告し、スキャン未実施を隠していた）。
    """
    proc = subprocess.run(
        ["git", "diff", "--unified=0", f"{base_ref}...HEAD", "--", "*.py"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        reason = proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else f"git diff exit {proc.returncode}"
        return [], reason

    added = parse_added_symbols(proc.stdout)
    findings: list[dict[str, str]] = []
    for file_path, symbols in sorted(added.items()):
        if is_test_path(file_path):
            continue
        for symbol in sorted(symbols):
            if count_references(repo_root, symbol, file_path) == 0:
                findings.append({"file": file_path, "symbol": symbol})
    return findings, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=os.getcwd(), help="対象リポジトリ / worktree のルート")
    parser.add_argument("--base-ref", default="origin/main", help="比較元 ref")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()

    # 境界チェック: `git diff` を実行する前に --repo-root が実在するディレクトリかを
    # 確認する（Snyk Code python/PT: CLI 引数由来の未検証パスがそのまま subprocess /
    # ファイル操作に流れる経路への指摘）。存在しない・ディレクトリでない場合は
    # 「該当なし」への黙殺を避け、明示的な error として報告する。
    if not repo_root.is_dir():
        findings, error = [], f"invalid --repo-root（存在しないかディレクトリでない）: {repo_root}"
    else:
        # report-only 契約（exit code は常に 0）を守るため、実行環境の不備（git バイナリが
        # 無い等）による例外も含めて全体を捕捉する（独立レビュー high finding: 未捕捉の
        # FileNotFoundError 等で exit 1 になり、completion-check の呼び出し前提を裏切っていた）。
        try:
            findings, error = find_unreferenced_new_symbols(repo_root, args.base_ref)
        except Exception as exc:  # noqa: BLE001 - report-only: 何が起きても block しない
            findings, error = [], f"{type(exc).__name__}: {exc}"

    if args.format == "json":
        payload: dict[str, object] = {"report_only": True, "findings": findings}
        if error is not None:
            payload["error"] = error
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if error is not None:
            print(f"未参照シンボル検出（report-only）: スキャン失敗のため未実施（{error}）")
        elif not findings:
            print("未参照シンボル検出（report-only）: 該当なし")
        else:
            print("未参照シンボル検出（report-only、block しない。テスト以外から参照0件の新設シンボル）:")
            for f in findings:
                print(f"- {f['file']}: `{f['symbol']}`")

    return 0  # report-only: block しない。findings / error があっても常に exit 0


if __name__ == "__main__":
    sys.exit(main())

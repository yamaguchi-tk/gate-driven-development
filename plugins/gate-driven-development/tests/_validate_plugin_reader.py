"""Shared helper for contract tests that search validate-plugin.sh content.

validate-plugin.sh は tests/checks/*.sh へ分割済み（PR-0c）。分割前は単一
ファイルへの文字列検索で済んでいた既存 contract test が、分割後もチェック
内容を検索できるようにするための共通ヘルパー。
"""
from __future__ import annotations

from pathlib import Path

from _paths import PLUGIN_ROOT


def read_validate_plugin_and_checks() -> str:
    """validate-plugin.sh 本体 + manifest.tsv に列挙された script を連結して返す。

    manifest.tsv に列挙された script のみを対象にすることで、
    validate-plugin.sh が実際に実行するチェックと検索対象を一致させる
    （ディレクトリ全走査は manifest に載らない孤立ファイルまで拾い
    false-pass を招くため使わない）。
    """
    parts = [(PLUGIN_ROOT / "tests" / "validate-plugin.sh").read_text(encoding="utf-8")]
    manifest_path = PLUGIN_ROOT / "tests" / "checks" / "manifest.tsv"
    for raw_line in manifest_path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        # validate-plugin.sh（bash `IFS=$'\t' read`）と同じ前提でパースする:
        # 行や列の前後空白を strip しない。空白混入は fail-closed で検出する。
        columns = raw_line.split("\t")
        if len(columns) != 3 or any(column != column.strip() for column in columns):
            raise AssertionError(f"malformed manifest.tsv row (expected 3 tab-separated columns, no extra whitespace): {raw_line!r}")
        _, _, script_rel = columns
        if Path(script_rel).is_absolute() or ".." in script_rel:
            raise AssertionError(f"manifest.tsv script column must be repo-relative with no '..': {script_rel!r}")
        script_path = (PLUGIN_ROOT / script_rel).resolve()
        if PLUGIN_ROOT not in script_path.parents:
            raise AssertionError(f"manifest.tsv script escapes plugin root: {script_rel!r}")
        if not script_path.is_file():
            raise AssertionError(f"manifest.tsv references missing script: {script_rel!r}")
        parts.append(script_path.read_text(encoding="utf-8"))
    return "\n".join(parts)

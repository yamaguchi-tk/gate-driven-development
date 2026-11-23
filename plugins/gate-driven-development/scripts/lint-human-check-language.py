#!/usr/bin/env python3
"""Lint GDD human-check text for unexplained internal terms.

人間向け HITL では、内部用語を出してよいが、先に日本語で意味を説明する。
この lint は代表的な内部用語が説明なしで出ていないかを軽量に検出する。

Exit code:
  0: pass
  1: unexplained internal term found
  2: usage error / file not found
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# hook は lib/kill-switch.sh で python3 を -I で起動し、PYTHONSAFEPATH も設定する。その下では、このファイルの
# ディレクトリが sys.path に入らない
if sys.flags.isolated or getattr(sys.flags, "safe_path", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.hitl_fields import required_words


TERM_EXPLANATIONS: dict[str, tuple[str, ...]] = {
    "holdout": ("評価用に取り分けたサンプル",),
    "human-confirm": ("人が内容を確認済みにする", "人が内容を確認済み"),
    "executable": ("自動テストやコマンドで実行できる状態",),
    "no-post": ("外部投稿しない",),
    "prod_equivalent": ("本番に近い条件で検証する", "本番に近い条件"),
    "production model env": ("本番相当のモデル設定",),
    "human_recheck_required": ("人間に戻して確認し直す", "人が確認し直す"),
    "design_detail_only": ("設計の細部だけを直す",),
    "implementation_fix_only": ("実装だけを直す",),
    "Route In Progress": ("今どの進め方で動いているか",),
    "Next Action": ("次にAIが行う作業",),
    "release gate": ("リリース前に必ず確認する条件",),
    "fixture": ("再現用のサンプル",),
}
FINAL_HITL_MARKER = '<gdd-stop reason="human-check-waiting">'
FINAL_HITL_REQUIRED_PHRASES = (
    "整理した要件",
    "実装する方法・内容",
    "検証する方法・内容",
    "どこまで自走するのか",
    "判断ポイント",
    # 各 stop marker 直前のタグがすべて `stage="none"` のときは要求しない（`lib.hitl_fields`）。
    "段階実装サマリー",
)
CANONICAL_SOURCES = (
    "references/human-check-template-compact.md",
    "references/human-check-template.md",
)


def line_has_explanation(line: str, term: str) -> bool:
    explanations = TERM_EXPLANATIONS[term]
    return any(explanation in line for explanation in explanations)


def lint_text(text: str) -> list[tuple[int, str, str]]:
    violations: list[tuple[int, str, str]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        lowered = line.lower()
        for term in TERM_EXPLANATIONS:
            if term.lower() in lowered and not line_has_explanation(line, term):
                violations.append((line_number, term, line.strip()))

    if FINAL_HITL_MARKER in text:
        for phrase in required_words(FINAL_HITL_REQUIRED_PHRASES, text):
            if phrase not in text:
                violations.append((0, phrase, "final HITL missing non-engineer decision brief"))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="HITL sample or Markdown files to lint")
    parser.add_argument("--quiet", action="store_true", help="Suppress OK output")
    args = parser.parse_args()

    all_violations: list[tuple[Path, int, str, str]] = []
    for raw_path in args.paths:
        path = Path(raw_path)
        if not path.is_file():
            print(f"ERROR: file not found: {path}", file=sys.stderr)
            return 2
        text = path.read_text(encoding="utf-8", errors="replace")
        all_violations.extend((path, line_no, term, line) for line_no, term, line in lint_text(text))

    if all_violations:
        print("ERROR: 説明なしの内部用語があります。先にやさしい日本語で意味を書き、内部名は括弧で補足してください。")
        for path, line_no, term, line in all_violations:
            if line_no == 0:
                print(f"- 最終HITLに必要な判断ポイントの欄がありません: {term} ({path})")
                print("  line: final HITL must show the six decision essentials")
            else:
                print(f"- 説明なしの内部用語: {term} ({path}:{line_no})")
                print(f"  line: {line}")
        return 1

    if not args.quiet:
        print("OK: human-check language lint passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

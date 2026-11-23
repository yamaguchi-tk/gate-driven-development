#!/usr/bin/env python3
"""Lint final human-check output for required HITL trace visibility.

This checks the final user-visible HITL text, not only requirements.md.
It prevents the regression where a subagent-generated HITL included trace
details, but the main session re-summarized it and dropped the high-risk
`ズレ確認` blocks before asking the user for OK.

Exit code:
  0: pass
  1: required final HITL detail is missing
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
from lib.lint_base import check_file


REQUIRED_MARKERS = (
    "なぜやるか",
    "整理した要件",
    "実装する方法・内容",
    "変更予定ファイル（WHERE）",
    "検証する方法・内容",
    "現在地",
    "どこまで自走するのか",
    "OKでも許可されないこと",
    "人間に戻す条件",
    "判断ポイント",
    "この案を選ぶと次に何が起きるか",
    "無回答時のデフォルト",
    "ズレ確認",
    # 各 stop marker 直前のタグがすべて `stage="none"`（段階が 1 つだけ）のときは要求しない
    # （`lib.hitl_fields.required_words`）。
    "段階実装",
    '<gdd-stop reason="human-check-waiting">',
)
REQUIRED_MARKER_GROUPS = (
    ("完了条件の変換", "テスト化確認", "技術スタック確認", "作り方の重要判断"),
    # 壁打ち・初期案からの差分（旧 `### 初期案・壁打ちから変わったこと`）。
    # compact は `採用しない案`、full は `却下した代替案` と語彙が違うため any-of で受ける。
    ("採用しない案", "却下した代替案"),
)
CANONICAL_SOURCES = (
    "references/human-check-template-compact.md",
    "references/human-check-template.md",
)


def lint_text(text: str) -> list[str]:
    missing = [marker for marker in required_words(REQUIRED_MARKERS, text) if marker not in text]
    for group in REQUIRED_MARKER_GROUPS:
        if not any(word in text for word in group):
            missing.append(f"any-of: {' / '.join(group)}")
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="final HITL markdown sample path")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    path = Path(args.path)
    if (rc := check_file(path)) is not None:
        return rc

    missing = lint_text(path.read_text(encoding="utf-8", errors="replace"))
    if missing:
        print("ERROR: Final HITL Display Integrity failed.")
        print("最終表示HITLで、承認判断に必要な表示要素が省略されています。")
        print("（壁打ち・初期案からの差分は any-of: 採用しない案 / 却下した代替案 で検査します）")
        print("subagent が生成した HITL を main session が再要約して省略しないでください。")
        for marker in missing:
            print(f"- missing: {marker}")
        return 1

    if not args.quiet:
        print("OK: Final HITL Display Integrity passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

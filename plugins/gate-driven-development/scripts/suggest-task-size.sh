#!/usr/bin/env bash
set -euo pipefail

# suggest-task-size.sh — タスクサイズの自動判定ヘルパー
#
# Usage: bash suggest-task-size.sh [task-description]
#
# 現在のリポジトリ状態（staged/unstaged diff, ユーザー入力）から
# quick / standard を提案する。
# references/task-sizing.md の判定基準に基づく。
#
# 出力: JSON { "suggested_size": "quick|standard", "reason": "..." }
# brainstorming から呼ばれることを想定。

description="${1:-}"

# git が使えなければ standard を提案
if ! command -v git >/dev/null 2>&1 || ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  printf '{"suggested_size":"standard","reason":"git repository not detected"}\n'
  exit 0
fi

# ユーザーの入力テキストからキーワードベースの判定
if [[ -n "$description" ]]; then
  desc_lower="$(echo "$description" | LC_ALL=C tr '[:upper:]' '[:lower:]')"

  # quick キーワード（旧 micro 相当: typo/config/one-line は quick に統合）
  if echo "$desc_lower" | grep -qE '(typo|タイポ|誤字|設定値変更|config.*変更|1行|one.?line|コメント修正|文言変更|version.*bump)'; then
    printf '{"suggested_size":"quick","reason":"keyword match: typo/config/one-line change"}\n'
    exit 0
  fi

  # quick キーワード
  if echo "$desc_lower" | grep -qE '(ちょっとした|軽い|簡単|simple|small|1ファイル|single.?file|ちょい修正|微修正)'; then
    printf '{"suggested_size":"quick","reason":"keyword match: small/simple change"}\n'
    exit 0
  fi

  # standard キーワード
  if echo "$desc_lower" | grep -qE '(しっかり|フル|full|大きな|large|リファクタ|refactor|新機能|new.?feature|セキュリティ|security|api.*追加|外部.*連携)'; then
    printf '{"suggested_size":"standard","reason":"keyword match: large/security/new-feature change"}\n'
    exit 0
  fi
fi

# staged + unstaged の diff stats を使った判定
diff_files=0
diff_lines=0

if git diff --stat HEAD 2>/dev/null | tail -1 | grep -q 'files\? changed'; then
  stat_line="$(git diff --stat HEAD 2>/dev/null | tail -1)"
  diff_files="$(echo "$stat_line" | grep -oE '[0-9]+ files? changed' | grep -oE '[0-9]+' || echo 0)"
  insertions="$(echo "$stat_line" | grep -oE '[0-9]+ insertions?' | grep -oE '[0-9]+' || echo 0)"
  deletions="$(echo "$stat_line" | grep -oE '[0-9]+ deletions?' | grep -oE '[0-9]+' || echo 0)"
  diff_lines=$(( ${insertions:-0} + ${deletions:-0} ))
fi

# diff ベースの判定
if [[ "$diff_files" -le 5 && "$diff_lines" -le 100 ]]; then
  printf '{"suggested_size":"quick","reason":"diff: %d file(s), %d line(s) changed"}\n' "$diff_files" "$diff_lines"
else
  printf '{"suggested_size":"standard","reason":"diff: %d file(s), %d line(s) changed"}\n' "$diff_files" "$diff_lines"
fi

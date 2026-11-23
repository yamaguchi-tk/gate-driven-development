#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}"

echo "BLOCK: gdd-self-development-tokens"

# GDD 自身を開発するときの層別ルールの契約トークン検証。
# 発火点は reference の存在ではなく、`gdd-using-git-worktrees` の § Guardrails
# からの参照行。参照が無ければ reference は読まれない。
# あわせて、実体が存在しない `gate-driven-development-b` の残存を ban で検出する。

fail=0

req() { # $1=relative file, $2=token
  local f="$ROOT/$1"
  if [[ ! -f "$f" ]]; then
    echo "MISSING FILE: $1"
    fail=1
    return
  fi
  if ! grep -qF -- "$2" "$f"; then
    echo "MISSING: $1 : $2"
    fail=1
  fi
}

ban() { # $1=relative file, $2=残存禁止の文字列
  local f="$ROOT/$1"
  [[ -f "$f" ]] || return 0
  if grep -qF -- "$2" "$f"; then
    echo "STALE: $1 : $2"
    fail=1
  fi
}

# --- 発火点: gdd-using-git-worktrees からの参照 ---
# 「worktree で開発するか local を直接編集するか」の判断そのものなので、
# skill の責務に一致する gdd-using-git-worktrees に置く。
# （gdd-writing-skills は allowlist baseline 558 行で、増やせない）
req "skills/gdd-using-git-worktrees/SKILL.md" "**GDD plugin 自身を変更するとき**は層で使い分ける"
req "skills/gdd-using-git-worktrees/SKILL.md" "references/gdd-self-development.md"

# --- reference の中身（層別ルール・復旧手段） ---
req "references/gdd-self-development.md" "毎回パス実行"
req "references/gdd-self-development.md" "hooks は worktree で開発しテストが green になるまで local に入れない"
req "references/gdd-self-development.md" "skills / references は local を直接編集してよい"
req "references/gdd-self-development.md" "~/.claude/gdd-hooks-disabled"
req "references/gdd-self-development.md" "gdd_kill_switch_active"

# --- 実体の無い plugin への同期指示が残っていないこと ---
for f in \
  "skills/gdd-pr-review/SKILL.md" \
  "skills/gdd-pr-review/references/pr-review.md" \
  "docs/TROUBLESHOOTING.md" \
  "references/gdd-self-development.md" \
  "skills/gdd-using-git-worktrees/SKILL.md"; do
  ban "$f" "gate-driven-development-b"
done

# --- 無改変検証: 同期義務そのものは残っていること ---
req "skills/gdd-pr-review/references/pr-review.md" "**SYNC**:"
req "skills/gdd-pr-review/SKILL.md" "# SYNC:"

if (( fail != 0 )); then
  echo "FAIL: gdd-self-development-tokens"
  exit 1
fi

echo "gdd-self-development-tokens: OK (self-development rules referenced, no stale -b sync target)"
echo "VERDICT: gdd-self-development-tokens: OK"

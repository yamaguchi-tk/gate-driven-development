#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}"

echo "BLOCK: pr-review-followup-polling-tokens"

# E-2: レビュー待ちポーリングの固定間隔 + 差分のみ方針が、
# gdd-pr-review-followup/SKILL.md の `## PR Review Follow-up Loop` セクション
# （Repeat ステップを含む範囲）に明記されていることを section-scope で検証する。
# token は挿入行の canonical bytes（wave dash U+301C）からコピーしている。

SKILL="$ROOT/skills/gdd-pr-review-followup/SKILL.md"

if [[ ! -f "$SKILL" ]]; then
  echo "MISSING: $SKILL"
  exit 1
fi

# `## PR Review Follow-up Loop` 見出しから次の `## ` 見出し直前までを抽出する。
section="$(awk '
  /^## PR Review Follow-up Loop[[:space:]]*$/ { insec=1; next }
  insec && /^## / { exit }
  insec { print }
' "$SKILL")"

if [[ -z "$section" ]]; then
  echo "FAIL: '## PR Review Follow-up Loop' セクションが見つからない"
  exit 1
fi

missing=()
for token in "5〜10 分" "最小フィールド" "全量を取得"; do
  if ! printf '%s' "$section" | grep -qF -- "$token"; then
    missing+=("$token")
  fi
done

if (( ${#missing[@]} > 0 )); then
  echo "FAIL: PR Review Follow-up Loop セクションに必須 token が不在: ${missing[*]}"
  exit 1
fi

echo "pr-review-followup-polling-tokens: OK (5〜10 分 / 最小フィールド / 全量を取得 all present in section)"
echo "VERDICT: pr-review-followup-polling-tokens: OK"

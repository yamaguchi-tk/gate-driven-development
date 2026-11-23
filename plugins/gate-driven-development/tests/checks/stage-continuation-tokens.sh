#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}"

echo "BLOCK: stage-continuation-tokens"

# Stage Continuation（独立 Stage の先行着手）の契約トークン検証。
# 存在検証: 新設契約が各正本に記載されていること。
# 無改変検証: Auto-Arm 発火条件の文字列が対象ファイルごとに 1 hit 以上（件数は assert しない）。
# 残存検出: 継続を禁止していた改訂前文言が残っていないこと。

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

ban() { # $1=relative file, $2=改訂前文言（残存禁止）
  local f="$ROOT/$1"
  [[ -f "$f" ]] || return 0
  if grep -qF -- "$2" "$f"; then
    echo "STALE: $1 : $2"
    fail=1
  fi
}

# --- 存在検証 ---
req "references/post-completion-pr-flow.md" "Stage Continuation"
req "references/post-completion-pr-flow.md" "auto-after-clean"
req "references/requirements-template.md" "Stage Files"
req "references/requirements-template.md" "In-flight PR"
req "references/requirements-template.md" "Continuation Mode"
req "skills/gdd-using-git-worktrees/SKILL.md" "Stage Continuation"
# 発火点そのもの（B1 / B3）: 原文が保持される改訂のため ban ではなく req で担保する
req "skills/gdd-pr-review-followup/SKILL.md" "が発火する場合は done を出さず継続する"
req "references/post-completion-pr-flow.md" "かつ Stage Continuation が発火しないなら"
# 承認境界の中核（自動継続 field の表示・依存宣言・単一 non-terminal steering）
req "references/post-completion-pr-flow.md" "いずれかが未宣言・不明なら依存扱い"
req "references/post-completion-pr-flow.md" "non-terminal steering が同時に複数存在しない"
req "skills/gdd-requirements-gating/SKILL.md" "圧縮表示経路"
req "references/requirements-gating-steps.md" "Continuation Mode=auto-after-clean"
# AC-12b / AC-2 / AC-6
req "references/post-completion-pr-flow.md" "進行中 Stage の steering / worktree を整理対象にしない"
req "references/requirements-template.md" "merge を待たずに着手してよい"
req "skills/gdd-pr-review-followup/SKILL.md" "terminal を確定させる"

# --- 無改変検証（Auto-Arm 発火条件。対象ファイルごとに 1 hit 以上・件数は assert しない） ---
AUTO_ARM_FILES=(
  "references/post-completion-pr-flow.md"
  "references/operation-levels.md"
  "skills/gdd-pr-review-followup/SKILL.md"
)
for f in "${AUTO_ARM_FILES[@]}"; do
  req "$f" "PR 作成 + 外部レビュー収束まで"
done

# --- stacked 分岐（S-2）の存在検証 ---
req "references/post-completion-pr-flow.md" "stacked 分岐"
req "references/post-completion-pr-flow.md" "auto-stacked"
req "references/post-completion-pr-flow.md" "deleteBranchOnMerge"
req "references/post-completion-pr-flow.md" "条件⑤と条件⑥の両方の代替"
req "references/post-completion-pr-flow.md" "の宣言・交差要件は stacked でも維持する"
req "references/post-completion-pr-flow.md" "gh pr view <url> --json headRefName,state,baseRefName"
req "references/post-completion-pr-flow.md" "ちょうど 1 件"
req "references/post-completion-pr-flow.md" "git worktree add <path> -b <new> <先行 branch>"
req "references/post-completion-pr-flow.md" "先行 Stage ID / 先行 head branch / 解決時点の先行 tip SHA"
req "references/post-completion-pr-flow.md" "gh pr create --base <先行 branch>"
req "references/post-completion-pr-flow.md" 'が `MERGED` を返すことで行い'
req "references/post-completion-pr-flow.md" "git diff --name-only origin/<先行 branch>...HEAD"
req "references/post-completion-pr-flow.md" "先行 commit が複製され merge-base が後退"
req "references/post-completion-pr-flow.md" "先行自身が stacked"
req "references/requirements-template.md" "auto-stacked"
req "references/requirements-template.md" "依存 Stage 専用"
req "references/requirements-template.md" "<Stage ID>: <PR URL> (<state>)"
req "references/state-field-tiers.md" "Stacked Base"
req "skills/gdd-using-git-worktrees/SKILL.md" "新規 task の base として直接使わない。 例外は Stage Continuation の stacked 分岐"
req "skills/gdd-using-git-worktrees/SKILL.md" "未マージ先行 Stage の task branch を base にしてよい"
req "skills/gdd-using-git-worktrees/SKILL.md" "stacked 依存の確認"
req "skills/gdd-using-git-worktrees/SKILL.md" 'main tip を完全に含む'
req "references/requirements-gating-steps.md" "auto-stacked"
req "skills/gdd-requirements-gating/SKILL.md" "auto-stacked"

# --- S-1 契約の無改変検証（AC-8） ---
req "references/post-completion-pr-flow.md" "auto-after-clean"

# --- 残存検出（系統 A / B の改訂前文言。Task 2〜3 で逐語を追記する） ---
ban "references/post-completion-pr-flow.md" "ここでは後続 Stage を勝手に開始しない"
ban "references/post-completion-pr-flow.md" "いずれも base=\`origin/<default-branch>\` の独立 PR でありマージ順は不問"
ban "references/state-machine.md" "後続 Stage を開始するには、ユーザーの明示入力または Manual Merge Continuation 後の新 steering seed が必要"
ban "references/phase-progression.md" "後続 Stage をその場で勝手に実装開始しない"
ban "skills/gdd-completion-check/SKILL.md" "後続 Stage を勝手に開始しないこと"
ban "references/post-completion-pr-flow.md" "かつ Auto-Arm（Option 1 手順 6 参照）が無効または収束完了（clean）済みなら"
ban "skills/gdd-pr-review-followup/SKILL.md" "が併記されている限り終端ではない（収束 clean で確定）"

if (( fail != 0 )); then
  echo "FAIL: stage-continuation-tokens"
  exit 1
fi

echo "stage-continuation-tokens: OK (stage continuation contract tokens present)"
echo "VERDICT: stage-continuation-tokens: OK"

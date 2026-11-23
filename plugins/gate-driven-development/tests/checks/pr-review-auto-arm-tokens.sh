#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}"

echo "BLOCK: pr-review-auto-arm-tokens"

# auto-arm（PR 作成後の外部 AI レビュー収束の自動化）の契約トークン検証。
# 存在検証（req 15 件）: auto-arm の新設契約が各正本 8 ファイルに記載されていること。
# 残存検出: 改訂対象の旧・無条件 done 文言が残っていないこと（CT-3）。
# `reason="done"` 文字列自体は正当に残るため grep 対象にしない。

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
req "skills/gdd-pr-review-followup/SKILL.md" "Auto-Arm Entry"
req "skills/gdd-pr-review-followup/SKILL.md" "PR Auto Review Convergence"
req "skills/gdd-pr-review-followup/SKILL.md" "--add-reviewer"
req "skills/gdd-pr-review-followup/SKILL.md" "Resume From=external-review-waiting"
req "references/post-completion-pr-flow.md" "Auto-Arm"
req "references/post-completion-pr-flow.md" "PR Auto Review Convergence"
req "references/operation-levels.md" "PR Auto Review Convergence"
req "references/operation-levels.md" "~/.gdd/config.local.md"
req "references/operation-levels.md" "タスク自走上限 > 設定キー"
req "references/human-check-template.md" "PR 作成 + 外部レビュー収束まで"
req "references/human-check-template.md" "設定キー不在のため収束までは選択不可"
req "references/human-check-template-compact.md" "収束までは選択不可"
req "references/phase-progression.md" "Auto-Arm"
req "references/subagent-dispatch.md" "Resume From=external-review-waiting"
req "skills/gdd-completion-check/SKILL.md" "Auto-Arm"

# --- 残存検出（CT-3。改訂対象 6 行の改訂前文言・逐語。reason="done" 単体は正当に残るため対象外） ---
ban "references/phase-progression.md" "CI pass で初めて \`<gdd-stop reason=\"done\">\` 発行"
ban "references/post-completion-pr-flow.md" "選択した option の処理が終わったら \`<gdd-stop reason=\"done\">\` を出す"
ban "references/post-completion-pr-flow.md" "ただし \`Post-PR Completion Scope\` がある場合は、PR 作成 option の処理が終わっても"
ban "references/subagent-dispatch.md" "PR 作成後に \`<gdd-stop reason=\"done\">\` を出力する。"
ban "skills/gdd-completion-check/SKILL.md" "選択に応じた処理 → \`<gdd-stop reason=\"done\">\` の順で進める"
ban "skills/gdd-completion-check/SKILL.md" "Post-PR Completion Scope が無い場合だけ、最終出力には PR URL を含め"

if (( fail != 0 )); then
  echo "FAIL: pr-review-auto-arm-tokens"
  exit 1
fi

echo "pr-review-auto-arm-tokens: OK (auto-arm contract tokens present, no stale done wording)"
echo "VERDICT: pr-review-auto-arm-tokens: OK"

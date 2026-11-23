#!/usr/bin/env bash
# Find stale steerings (10+ days old, brainstorming phase only) and suggest
# cancelling them (Resume From / Next Action = cancelled). **Read-only**: never
# edits, deletes or moves anything.
#
# Usage:
#   find-stale-steerings.sh                # current git worktree only
#   find-stale-steerings.sh --all-worktrees  # all worktrees of current repo
#   find-stale-steerings.sh --registry       # cross-repo worktree registry (list only)
#   find-stale-steerings.sh --threshold-days N  # custom threshold (default 10)
#
# Output: per-stale steering, prints metadata + manual cancel / resume steps.
#   Moving or deleting is not suggested: a steering moved out of `.steering/`
#   leaves the ignore and becomes visible to git, and one with an open PR drops
#   out of the merge gate's PR URL match.
#   --registry mode prints one line per worktree and suggests nothing.
#   Stale scan (default / --all-worktrees) reports one candidate per steering
#   ID and excludes git tracked steering copies; both exclusions are listed in
#   the trailing summary. A repo that keeps its steering git tracked is
#   therefore outside the stale detection scope of this script.
# Why: `.steering/*/state.md` may be in active use by another runtime (Cursor
# etc.). Auto-cancel is forbidden — the user must confirm each candidate.

set -euo pipefail

THRESHOLD_DAYS=10
SEARCH_ALL_WORKTREES=0
REGISTRY_MODE=0
WORKTREES_ROOT="${GDD_WORKTREES_ROOT:-$HOME/.gdd/worktrees}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all-worktrees)
      SEARCH_ALL_WORKTREES=1
      shift
      ;;
    --registry)
      REGISTRY_MODE=1
      shift
      ;;
    --threshold-days)
      THRESHOLD_DAYS="$2"
      shift 2
      ;;
    -h|--help)
      # 行番号で範囲を切ると、本文を 1 行足すたびに実行コードが漏れる
      # （実測: `2,19p` は `set -euo pipefail` 以下 3 行を出していた）。
      awk 'NR > 1 { if ($0 !~ /^#/) exit; print }' "$0"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if ! command -v git >/dev/null 2>&1; then
  echo "git is required" >&2
  exit 2
fi

THRESHOLD_SECS=$((THRESHOLD_DAYS * 86400))
NOW_EPOCH=$(date +%s)

# Resolve worktree paths to search（registry モードは自前で走査するのでスキップ）
WORKTREES=()
if [[ "$REGISTRY_MODE" -eq 1 ]]; then
  :
elif [[ "$SEARCH_ALL_WORKTREES" -eq 1 ]]; then
  while IFS= read -r line; do
    if [[ "$line" == worktree* ]]; then
      WORKTREES+=("${line#worktree }")
    fi
  done < <(git worktree list --porcelain 2>/dev/null || true)
else
  if wt="$(git rev-parse --show-toplevel 2>/dev/null)"; then
    WORKTREES+=("$wt")
  else
    echo "Not inside a git worktree" >&2
    exit 2
  fi
fi

iso_to_epoch() {
  local iso="$1"
  [[ -n "$iso" ]] || { echo ""; return 0; }
  # macOS BSD date
  if date -j -f "%Y-%m-%dT%H:%M:%S" "${iso%%[Z+]*}" +%s >/dev/null 2>&1; then
    date -j -f "%Y-%m-%dT%H:%M:%S" "${iso%%[Z+]*}" +%s 2>/dev/null
    return 0
  fi
  # GNU date
  if date -d "$iso" +%s >/dev/null 2>&1; then
    date -d "$iso" +%s 2>/dev/null
    return 0
  fi
  echo ""
}

extract_field() {
  local file="$1" field="$2"
  [[ -f "$file" ]] || return 0
  awk -v field="$field" '
    {
      raw = $0
      gsub(/`/, "", raw)
      sub(/^[[:space:]\-]*/, "", raw)
      if (index(raw, field "=") == 1) { print substr(raw, length(field) + 2); exit }
      if (index(raw, field ":") == 1) { print substr(raw, length(field) + 2); exit }
    }
  ' "$file" 2>/dev/null | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//'
}

file_mtime() {
  # GNU stat (Linux) と BSD stat (macOS) でオプションの意味が異なる。
  # GNU の `-f` は `--file-system` で、`stat -f %m <file>` はファイルシステム情報を
  # 返してしまい mtime にならない（CI = Linux で `File: unbound variable` を起こした）。
  # そのため GNU 形式の `-c` を先に試し、失敗した場合だけ BSD 形式にフォールバックする。
  stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null || echo ""
}

# 末尾サマリの「除外」節を出す。第 1 引数が見出しの種別、第 2 引数が補足行
# （空なら出さない）、以降が `slug @ worktree` の並び。件数 0 なら節ごと出さない。
# 呼び出し側は `set -u` 下の空配列展開を避けるため件数で分岐すること（bash 3.2）。
print_exclusions() {
  local label="$1" note="$2"
  shift 2
  [[ "$#" -gt 0 ]] || return 0
  echo ""
  # 変数展開の直後に全角文字を置くと bash が変数名の一部と解釈するため `${VAR}` 形にする。
  echo "除外（${label}）: $# 件"
  [[ -z "$note" ]] || echo "  $note"
  printf '  - %s\n' "$@"
}

# --- Registry mode: repo をまたいだ worktree 一覧（list only） ---
# 走査は `.git` の存在で判定し、**深さ上限に依存しない**（`-prune` で打ち切る）。
# 深さ固定にすると branch 名のスラッシュ数だけ階層が深くなるため、
# `fix/foo`（実データにある形）は拾えても `feature/foo/bar` のような多段は取りこぼす。
#
# ただし prune だけでは、worktree 配下にネストした無関係な git リポジトリまで拾う
# （実データに `.terraform/modules/<name>/.git` が存在する）。
# prune は「最初に見つけた .git で打ち切る」ので、worktree 自身が先に一致すれば
# その配下は走査されない。root 直下に無関係な git がある場合に備え、
# `.steering/` を持たないものは GDD worktree でないとみなして除外する。
#
# 破壊的な提案は出さない: 実測では停止分が完了間際（gdd-completion-check /
# human-check-waiting）で、多くが未コミット変更を持つ。削除を勧めてよい状態ではない。
if [[ "$REGISTRY_MODE" -eq 1 ]]; then
  if [[ ! -d "$WORKTREES_ROOT" ]]; then
    echo "worktrees root not found: $WORKTREES_ROOT" >&2
    exit 0
  fi

  printf '%-46s %-24s %-26s %-12s %-7s %s\n' \
    "worktree" "branch" "next_action" "updated" "merged" "dirty"

  WT_COUNT=0
  SEEN_WORKTREES=()
  while IFS= read -r GITPATH; do
    [[ -n "$GITPATH" ]] || continue
    WT="$(dirname "$GITPATH")"
    REL="${WT#"$WORKTREES_ROOT"/}"
    # git worktree の `.git` は**ファイル**（gitdir ポインタ）なので `-prune` が効かず、
    # その配下にある vendored repo（実データの `.terraform/modules/*/.git`）まで拾う。
    # 既出の worktree の内側にあるものは除外する。find の出力は sort 済みで
    # 親が先に来るため、直前までに採用したパスの接頭辞一致で判定できる。
    #
    # `.steering/` の有無では判定しない: steering は cleanup 後に消えるため、
    # 「作業が終わって steering だけ消した worktree」（実データにある）まで落ちてしまう。
    _nested=0
    for _seen in "${SEEN_WORKTREES[@]:-}"; do
      [[ -n "$_seen" ]] || continue
      if [[ "$WT" == "$_seen"/* ]]; then
        _nested=1
        break
      fi
    done
    [[ "$_nested" -eq 0 ]] || continue
    SEEN_WORKTREES+=("$WT")
    WT_COUNT=$((WT_COUNT + 1))

    BRANCH="$(git -C "$WT" branch --show-current 2>/dev/null || true)"
    [[ -n "$BRANCH" ]] || BRANCH="-"

    # 代表 state.md は最終更新が最も新しいもの（1 worktree 1 行に畳む）
    NEWEST_STATE=""
    NEWEST_MTIME=0
    for SF in "$WT"/.steering/*/state.md; do
      [[ -f "$SF" ]] || continue
      M="$(file_mtime "$SF")"
      # 非数値（stat の出力形式が想定外だった場合）は算術比較でエラーになるので弾く
      [[ "$M" =~ ^[0-9]+$ ]] || continue
      if [[ "$M" -gt "$NEWEST_MTIME" ]]; then
        NEWEST_MTIME="$M"
        NEWEST_STATE="$SF"
      fi
    done

    NEXT_ACTION="-"
    UPDATED="-"
    if [[ -n "$NEWEST_STATE" ]]; then
      # `Started At` ではなく mtime を使う。既存の stale 判定が Started At 基準のため
      # 完了間際で停止した steering を検出できていなかった。
      NA="$(extract_field "$NEWEST_STATE" "Next Action")"
      # 実データの Next Action には phase 名の後ろに長い補足が付くものがある
      # （例: `human-check-waiting（recall gap 調査を…）`）。一覧では phase 名だけ要る。
      # `${VAR:0:N}` はバイト単位で切って全角を壊すため、区切り文字でのパターン切りにする。
      NA="${NA%%[[:space:]]*}"
      NA="${NA%%（*}"
      NA="${NA%%(*}"
      [[ -n "$NA" ]] && NEXT_ACTION="$NA"
      if [[ "$NEWEST_MTIME" -gt 0 ]]; then
        AGE_D=$(( (NOW_EPOCH - NEWEST_MTIME) / 86400 ))
        UPDATED="${AGE_D}d ago"
      fi
    fi

    # merge-base は ref を列挙しないので `branch -r --contains` より大幅に速い
    if git -C "$WT" merge-base --is-ancestor HEAD origin/main >/dev/null 2>&1; then
      MERGED="yes"
    else
      MERGED="no"
    fi

    DIRTY="$(git -C "$WT" status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
    [[ -n "$DIRTY" ]] || DIRTY=0

    # `${VAR:0:N}` は locale 未設定だとバイト単位で切るため、全角を含みうる値
    # （実データに `human-check-waiting（...）` のような値が存在する）は切り詰めない。
    # 列がずれても、値が壊れて読めなくなるより良い。パスと branch は ASCII 前提で切る。
    printf '%-46s %-24s %-26s %-12s %-7s %s\n' \
      "${REL:0:46}" "${BRANCH:0:24}" "$NEXT_ACTION" "$UPDATED" "$MERGED" "$DIRTY"
  done < <(find "$WORKTREES_ROOT" -name .git -prune -print 2>/dev/null | sort)

  echo ""
  # 変数展開の直後に全角文字を置くと bash が変数名の一部と解釈する（`$VAR）` → unbound variable）。
  # 日本語文と隣接する変数は必ず `${VAR}` の形にする。
  echo "合計 ${WT_COUNT} worktree（root: ${WORKTREES_ROOT}）"
  echo ""
  echo "**この一覧は read-only です**。merged=yes かつ dirty=0 でも、"
  echo "別 runtime が worktree を掴んでいる可能性があるため自動削除はしません。"
  echo "next_action が done 以外のものは作業が途中で止まっています。"
  exit 0
fi

STALE_COUNT=0

# 同一 steering ID が複数 worktree に出た場合、`WORKTREES` の順
# （= `git worktree list --porcelain` の順）で最初に残ったものを代表とする。
# macOS 既定の bash 3.2 には連想配列が無いため、改行区切りの文字列で持つ。
SEEN_SLUGS=$'\n'
EXCLUDED_DUP=()
EXCLUDED_TRACKED=()

for WT in "${WORKTREES[@]}"; do
  [[ -d "$WT/.steering" ]] || continue
  for DIR in "$WT"/.steering/*/; do
    [[ -d "$DIR" ]] || continue
    STATE_FILE="$DIR/state.md"
    [[ -f "$STATE_FILE" ]] || continue

    STARTED_AT="$(extract_field "$STATE_FILE" "Started At")"
    RESUME_FROM="$(extract_field "$STATE_FILE" "Resume From")"

    # Skip if not brainstorming-phase (only abandoned-early steerings qualify)
    [[ "$RESUME_FROM" == "gdd-brainstorming" ]] || continue

    STARTED_EPOCH="$(iso_to_epoch "$STARTED_AT")"
    [[ -n "$STARTED_EPOCH" ]] || continue

    AGE_SECS=$((NOW_EPOCH - STARTED_EPOCH))
    [[ "$AGE_SECS" -gt "$THRESHOLD_SECS" ]] || continue

    AGE_DAYS=$((AGE_SECS / 86400))
    SLUG="$(basename "${DIR%/}")"

    # git tracked な steering は候補から外す（tracked コピーによる再汚染の防止）。
    # dedupe より先に判定する: tracked コピーが先頭 worktree にあると、
    # 後段の worktree にある**追跡されていない本物**まで道連れに消えるため。
    # `ls-files` が失敗する環境（repo 外・git の異常）は fail-open で候補に残す。
    if git -C "$WT" ls-files --error-unmatch -- ":(literal)$STATE_FILE" >/dev/null 2>&1; then
      EXCLUDED_TRACKED+=("$SLUG @ $WT")
      continue
    fi

    if [[ "$SEEN_SLUGS" == *$'\n'"$SLUG"$'\n'* ]]; then
      EXCLUDED_DUP+=("$SLUG @ $WT")
      continue
    fi
    SEEN_SLUGS="$SEEN_SLUGS$SLUG"$'\n'

    STALE_COUNT=$((STALE_COUNT + 1))

    cat <<EOF

--- Stale steering #$STALE_COUNT ---
worktree:    $WT
slug:        $SLUG
started_at:  $STARTED_AT
age:         $AGE_DAYS 日（>$THRESHOLD_DAYS 日）
resume_from: $RESUME_FROM

Cancel 提案（終えてよいかユーザーに確認してください。別 runtime で作業中かもしれません）:
  ${DIR%/}/state.md の Resume From と Next Action をどちらも cancelled にする
  （手順: references/self-review-lanes.md § 使わないステアリングの終え方。移動・削除はしない）

Resume 提案（再開したい場合）:
  cd "$WT" && /gdd-dev resume $SLUG
EOF
  done
done

echo ""
if [[ "$STALE_COUNT" -eq 0 ]]; then
  echo "Stale steering 候補なし（${THRESHOLD_DAYS} 日超 + Resume From=gdd-brainstorming）"
else
  echo "合計 $STALE_COUNT 件の stale 候補を検出"
  echo ""
  echo "**注意**:"
  echo "- このスクリプトは read-only です。cancel は手動で実行してください"
  echo "- Cursor 等の別 runtime で作業中の steering が含まれる可能性があります"
  echo "- cancel の前に各 candidate の Resume From 状態と最終更新日を確認してください"
fi

if [[ "${#EXCLUDED_DUP[@]}" -gt 0 ]]; then
  print_exclusions "重複" "" "${EXCLUDED_DUP[@]}"
fi

if [[ "${#EXCLUDED_TRACKED[@]}" -gt 0 ]]; then
  print_exclusions "git tracked" \
    "steering を git tracked で運用している repo は本スクリプトの stale 検出対象外です" \
    "${EXCLUDED_TRACKED[@]}"
fi

#!/usr/bin/env bash
# git の pre-push hook（設定による hook。run-push-review-env-hook.sh が差し込む）。
# PR がある branch への push を、レビュー済みの tip かどうかで判定してログに書く。
# log-only なので、どの判定でも、判定が失敗しても exit 0 で push を通す。
# 引数（remote の名前と URL）と stdin（push する ref の行）は git が渡す。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" || exit 0
source "$SCRIPT_DIR/lib/kill-switch.sh" || exit 0
gdd_kill_switch_active && exit 0

python3 "$SCRIPT_DIR/git_pre_push_review.py" "$@" >/dev/null 2>&1 || true
exit 0

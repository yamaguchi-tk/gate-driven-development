#!/usr/bin/env bash
set -euo pipefail

# PreToolUse hook: /gdd-dev session 中の host-native EnterWorktree tool 呼び出しをブロックする。
# 非 active・別 session なら通す。marker で判定できない（state 破損・読めないなど）ときは止める（lib/exact-path.sh）。
# worktree 作成経路を GDD managed（gdd-using-git-worktrees skill）に一本化するため
# （references/workspace-policy.md）。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/kill-switch.sh"
gdd_kill_switch_active && exit 0
# payload の cwd（セッションの cwd）へ移してから steering・marker を探す
# shellcheck source=lib/payload-cwd.sh
source "$SCRIPT_DIR/lib/payload-cwd.sh"
gdd_enter_payload_cwd
# shellcheck source=lib/detect-steering.sh
source "$SCRIPT_DIR/lib/detect-steering.sh"

# gdd-dev.local.md が active でこのセッションのもの、または判定できないときにブロック
# shellcheck source=lib/exact-path.sh
source "$SCRIPT_DIR/lib/exact-path.sh"
gdd_resolve_project_root
PROJECT_ROOT="$GDD_PROJECT_ROOT"

# payload の cwd の repo と、入口で移す前の repo のすべてで、このセッションの active な marker が
# 無いと言い切れたときだけ通す。判定できない（cwd を取れない・marker が読めないなど）ときは止める（lib/exact-path.sh）。
gdd_marker_allows && exit 0

# gdd-dev session が active なので host-native EnterWorktree をブロック
# JSON 文字列内で改行を表現するには \\n が必要（printf が \\n を \n に変換し、JSON パーサが改行として解釈する）
printf '{"decision":"block","reason":"⛔ /gdd-dev session が active です。host-native EnterWorktree は使用できません。\\n\\nなぜ: active な /gdd-dev session 中の worktree 作成は gdd-using-git-worktrees skill 経由に一本化されています。host-native EnterWorktree で作成すると .steering/ 配置・pollution guard・post-merge cleanup 追跡から外れ、後続の GDD ワークフロー前提が崩れます。\\n\\nどうする: gdd-using-git-worktrees skill 経由で worktree を作成してください。使い分けは references/workspace-policy.md を参照してください。"}\n'

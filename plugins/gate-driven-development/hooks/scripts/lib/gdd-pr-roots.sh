#!/usr/bin/env bash
# GDD の PR 台帳（GDD worktree の root の一覧。1 行 1 絶対パス）。
# 書き手は pre-PR gate（`gh pr create` を active GDD で検査する時点）、読み手は merge
# gate（GDD の証跡を見ずに通す 5 経路〔root 未解決・git cwd の marker 不在・同じ repo の
# 別 worktree や root checkout へ共通ディレクトリで通した実行先・対象を repo つきで明示した
# merge・trusted root の steering が対象 PR を記録していない出口〕で、対象 PR が GDD の PR かを照合する）。PR URL は pre-PR gate の時点ではまだ無いので台帳には持たず、
# merge 時に各 root の `.steering/*/state.md` の `PR URL` を読む。
#
# 限界（2026-10-12 実測。直さずに受け入れた。PR 作成時・push 時の検査の素通りは
# 旧#431）: 台帳に載るのは、pre-PR gate が root の marker を見て
# 検査したときだけである。marker は `/gdd-dev` を始めた root にだけ作られ、通常の GDD worktree には
# 無い。2026-09-28 以降の、steering を持つ root から作った PR のうち、照合で当たりうるのはごく一部
# だった。root が台帳に無い PR の内訳は次のとおり。
#   - 大半は `cd <GDD worktree> && … gh pr create` の形で、移動先に marker が無かった。pre-PR gate は
#     marker の判定より後の検査すべて（completion-check・PR body の機密の検査・ADR・Codebase Health・
#     `--head` の照合・steering の一意性・レビューの証跡など）をせずに通し、台帳にも書かない（その前の
#     raw task steering の検査は、base branch を解決できるときだけ走る）。同じ形の `git push` でも、
#     pre-push gate は移動先に marker が無ければ証跡を検査せずに通す（09-28 以降の push の一部が当たる）
#   - 残りは、作成時に session の root の marker が無いか別の session のもので、原因は個別には
#     特定していない
#   - これらの半分以上は、仮に台帳に載っても state.md に `PR URL` が無いので当たらない
# merge gate は台帳より先に、repo の binding が指す state.md の `PR URL` で対象 PR の
# steering を探し、見つかればその worktree の証跡で検査する（lib/merge-gate-binding.sh）。
# binding でも台帳でも外れた merge は、root に marker が無いとき（root の steering に対象 PR があっても読まない）、
# root を決められず GDD の外と判定できたとき、marker のある root の steering が対象 PR を記録して
# いないとき（reason code `state-unreadable`・`pr-url-unrecorded`・`steering-ambiguous`・
# `untrusted-root-unverified`・`pr-target-unresolvable` など、理由つきで不足として通知する場合と、自セッションが
# 所有する active な marker の下で steering の証跡を検査する場合を除く）に証跡を見ずに通り、GDD は
# この経路でマージの承認を検査しない。測った範囲では、agent が打った `gh pr merge` はどれもユーザーの承認の
# 下だった（GitHub の画面での merge は数えていない）。逆に台帳で当たった PR は、binding が対象 PR の
# steering を指さず、marker を持つ場所の無いセッションからは、案内どおり GDD worktree へ cd しても同じ照合で不足として通知され、通知を消す出口は kill switch か
# 人の手の merge になる。PR 作成後の hook で台帳に PR URL を書く案は、この通知の場面を増やすので
# 採らなかった。

# 台帳のパス。state dir が決まらない（GDD_HOOK_STATE_DIR も HOME も空）ときは空を返す。
gdd_pr_roots_file() {
  local _dir="${GDD_HOOK_STATE_DIR:-}"
  if [[ -z "$_dir" && -n "${HOME:-}" ]]; then
    _dir="$HOME/.claude/.gdd-hook-state"
  fi
  [[ -n "$_dir" ]] || return 0
  printf '%s/gdd-pr-roots' "$_dir"
}

# root を重複なく追記する（best-effort。失敗しても呼び出し側の判定を変えない）。
gdd_pr_roots_register() {
  local _root="${1:-}" _file
  [[ -n "$_root" && -d "$_root" ]] || return 0
  _file="$(gdd_pr_roots_file)"
  [[ -n "$_file" ]] || return 0
  mkdir -p "${_file%/*}" 2>/dev/null || return 0
  # 在るのに通常ファイルでない台帳（FIFO など）は開かない。FIFO の grep は待ち続けて
  # hook が timeout し、呼び出し側（pre-PR gate）の検査ごと素通りになる。
  if [[ -e "$_file" || -L "$_file" ]]; then
    [[ -f "$_file" && -r "$_file" ]] || return 0
  fi
  if grep -Fxq -- "$_root" "$_file" 2>/dev/null; then
    return 0
  fi
  printf '%s\n' "$_root" >>"$_file" 2>/dev/null || return 0
  chmod 600 "$_file" 2>/dev/null || true
}

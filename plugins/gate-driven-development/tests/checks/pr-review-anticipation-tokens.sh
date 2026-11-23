#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}"

echo "BLOCK: pr-review-anticipation-tokens"

# 3f External Reviewer Anticipation Check の契約トークン検証。
# 発火点は節見出しではなく「手順 step 2 の実行対象列挙」である。節だけ追加しても
# 列挙に載らなければ実行されない（2a / 3d-2 / 3e が現に漏れていた）ため、
# 列挙行そのものを逐語 pin し、改訂前の列挙が残っていないことを ban で担保する。
# 無改変検証: 既存節の見出しと High 差し戻し契約が残っていること。

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

# --- 発火点（最重要）: 手順 step 2 の実行対象列挙 ---
# 節を増減したらこの literal も同時に直す。**節の実在と列挙の一致は
# `tests/test_pr_review_section_enumeration.py` が機械照合する**ので、
# ここは「列挙が消えていない / 旧版に戻っていない」ことだけを固定する。
req "skills/gdd-pr-review/SKILL.md" "（2a, 2b, 3a, 3b, 3c, 3d, 3d-2, 3e, 3f, 3g, 5, 6）"
ban "skills/gdd-pr-review/SKILL.md" "（3a, 3b, 3c, 3d, 5, 6）"
ban "skills/gdd-pr-review/SKILL.md" "（2a, 3a, 3b, 3c, 3d, 3d-2, 3e, 3f, 5, 6）"
ban "skills/gdd-pr-review/SKILL.md" "（2a, 2b, 3a, 3b, 3c, 3d, 3d-2, 3e, 3f, 5, 6）"

# --- 3f 節の存在検証 ---
req "skills/gdd-pr-review/SKILL.md" "3f. External Reviewer Anticipation Check"
req "skills/gdd-pr-review/SKILL.md" "数値・列挙の自己不整合"
req "skills/gdd-pr-review/SKILL.md" "コマンド・式の引数省略"
req "skills/gdd-pr-review/SKILL.md" "断定の過剰一般化"
# D（v0.22.0 追加）: 型そのものと、見落としの原因だった適用対象の拡張を別トークンで pin する。
# 見出しだけ足して適用対象を直さないと、コード側の見落としが残ったまま緑になる。
req "skills/gdd-pr-review/SKILL.md" "**D. 検証・ガードの緩さ**"
# D④（v0.23.0 追加）: 「検証が空振りしていないか」は①〜③（ガードの緩さ）とは別の失敗型。
# 実測で見つかった型（TMPDIR 差し替えが効かず空のディレクトリを数えていた / レビュー結果を未検証で比較した）
req "skills/gdd-pr-review/SKILL.md" "**その検証は本当に対象を見ているか**"
req "skills/gdd-pr-review/SKILL.md" "**常に成功する検証は検証していないのと同じ**"
req "skills/gdd-pr-review/SKILL.md" "コード内の docstring / テストの assertion / 検証スクリプトの pin"
# E（v0.25.0 追加）: 「実装中に設計を変えたとき、先に書いた説明文が追随しているか」。
# A（数え直し）とは検出方法が違い、diff との突き合わせで見る。
req "skills/gdd-pr-review/SKILL.md" "**E. 設計変更の追随漏れ**"
req "skills/gdd-pr-review/SKILL.md" "名指ししているファイル・節・skill を実際の変更ファイル一覧と突き合わせる"
req "skills/gdd-pr-review/SKILL.md" "A / B / C / D / E 内訳"

# --- fail の重さ（既存 High 差し戻し契約と混同させない） ---
req "skills/gdd-pr-review/SKILL.md" "High finding にせず"
req "skills/gdd-pr-review/SKILL.md" '`Pre-PR Fix Attempts` は増やさない'
req "skills/gdd-pr-review/SKILL.md" "修正せず PR 本文に残し"

# --- パターン追加の運用（指標 / 記録先 / 見直しトリガ） ---
req "skills/gdd-pr-review/SKILL.md" "3 PR 連続で 3f の検出が 0 件"

# --- 無改変検証: 既存節の見出しが残っていること ---
for heading in \
  "2a. Evidence Before PR Claims" \
  "3a. Spec Drift" \
  "3d-2." \
  "3e. Superpowers Benchmark"; do
  req "skills/gdd-pr-review/SKILL.md" "$heading"
done

# --- 無改変検証: High 差し戻し契約（別ファイル・本 check では改訂しない） ---
req "references/post-completion-pr-flow.md" "High 残存時の差し戻し"
req "references/post-completion-pr-flow.md" "Pre-PR Fix Attempts"

if (( fail != 0 )); then
  echo "FAIL: pr-review-anticipation-tokens"
  exit 1
fi

echo "pr-review-anticipation-tokens: OK (3f firing point and contract tokens present)"
echo "VERDICT: pr-review-anticipation-tokens: OK"

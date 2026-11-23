#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}"

echo "BLOCK: self-review-lane-tokens"
FAIL=0

# 検査は 2 種類。どちらも失敗時は同じ `FAIL: self-review-lane-tokens: <label> ...` 書式で出す。
#   check_token — 逐語 token が対象ファイルに存在すること（presence）
#   check_order — 逐語 token 群が「この順で」現れること（order。presence は包含する）
# ファイル不在は token 不在と別の診断にする（fail-closed 性は同じで、原因の切り分けだけを分ける）。
check_token() {
  local file="$1" token="$2" label="$3"
  local path="$ROOT/$file"
  if [[ ! -f "$path" ]]; then
    echo "FAIL: self-review-lane-tokens: $label target file not found: $file"
    FAIL=1
    return
  fi
  if ! grep -qF -- "$token" "$path"; then
    echo "FAIL: self-review-lane-tokens: $label missing token '$token' in $file"
    FAIL=1
  fi
}

# check_order <file> <label> <token1> <token2> ...
# 各 token の初出行が狭義単調増加であることを検査する。presence 述語は置換不変なので
# check_token を何本足しても「文言を温存したまま並べ替える」変異は判別できない。
# 出現順そのものを見ることでその型を閉じる（primitive を presence から order へ替えるだけで、
# 検査対象ファイルも実行系も check_token と同じ）。
check_order() {
  local file="$1" label="$2"
  shift 2
  local path="$ROOT/$file"
  if [[ ! -f "$path" ]]; then
    echo "FAIL: self-review-lane-tokens: $label target file not found: $file"
    FAIL=1
    return
  fi
  local prev=0 prev_token="" line token
  for token in "$@"; do
    line="$(grep -nF -- "$token" "$path" | head -1 | cut -d: -f1 || true)"
    if [[ -z "$line" ]]; then
      echo "FAIL: self-review-lane-tokens: $label missing token '$token' in $file"
      FAIL=1
      return
    fi
    # 初出行で順序を見るため、同じ token が 2 箇所に現れると「literal だけを正しい位置へ
    # 再掲し、実体のブロックを順序外へ動かす」変異が素通りする（L-83 = 実測 SURVIVOR）。
    # 出現数 1 を assert してこの経路を閉じる。
    local occurrences
    occurrences="$(grep -cF -- "$token" "$path" || true)"
    if [[ "$occurrences" -ne 1 ]]; then
      echo "FAIL: self-review-lane-tokens: $label token '$token' must appear exactly once in $file (found $occurrences)"
      FAIL=1
      return
    fi
    if [[ "$line" -le "$prev" ]]; then
      echo "FAIL: self-review-lane-tokens: $label out of order in $file: '$token' at line $line must appear after '$prev_token' at line $prev"
      FAIL=1
      return
    fi
    prev="$line"
    prev_token="$token"
  done
}

# check_reference_closure <label>
# 参照側の skill の閉包検査（当初の AC-8 は 3 skill。今の集合は参照元の行が正で、件数をここに書かない）。
# 期待集合は本 check に literal で書かず、正本 `references/self-review-lanes.md` の
# `参照元` 行から機械導出する。実集合は skills/*/SKILL.md を実際に grep して得る。
# 集合一致を見るので次のいずれも FAIL になる:
#   (a) 宣言していない skill が正本を参照し始める（観点の正本が分散する）
#   (b) 宣言済み skill のどれかが参照を落とす（宣言だけ残る片側リンク）
#   (c) 正本側の宣言行だけを書き換える（宣言と実態の乖離）
# 導出側が空になると (b) を素通りさせるため、空の導出は独立に FAIL にする（空洞化アンカー）。
check_reference_closure() {
  local label="$1"
  local doc="references/self-review-lanes.md"
  local path="$ROOT/$doc"
  if [[ ! -f "$path" ]]; then
    echo "FAIL: self-review-lane-tokens: $label target file not found: $doc"
    FAIL=1
    return
  fi
  local declared actual
  # -m1 を付けない: 2 本目の `> **参照元**:` 行で 4 件目を宣言する形が SURVIVOR になる
  # （L-86 = 実測 O1）。宣言行が何本あっても全部を宣言集合に入れて実集合と突き合わせる。
  declared="$(grep -- '^> \*\*参照元\*\*' "$path" | grep -oE 'skills/[a-z0-9-]+/SKILL\.md' | sort -u || true)"
  actual="$( (cd "$ROOT" && grep -lF -- "$doc" skills/*/SKILL.md 2>/dev/null | sort -u) || true)"
  if [[ -z "$declared" ]]; then
    echo "FAIL: self-review-lane-tokens: $label declared reference set is empty in $doc"
    FAIL=1
    return
  fi
  if [[ "$declared" != "$actual" ]]; then
    echo "FAIL: self-review-lane-tokens: $label reference set mismatch"
    echo "  declared in $doc: $(echo "$declared" | tr '\n' ' ')"
    echo "  actually referencing: $(echo "$actual" | tr '\n' ' ')"
    FAIL=1
  fi
}

# --- 3f: 敵対レーン + 内部整合レーンの入口（AC-9）。KILL する変異形は tasklist.md T-26 § の 4 列表が正本 ---
check_token "skills/gdd-pr-review/SKILL.md" "分類の正本は \`references/self-review-lanes.md\`（10 分類・3 レーン・A〜E 対応表）" "TK0 3f レーン参照"
check_token "skills/gdd-pr-review/SKILL.md" "D 型（検証・ガードの緩さ / fail-open）を最優先で確認する" "TK1 3f D型優先"
check_token "skills/gdd-pr-review/SKILL.md" "A〜C・E より先に見る" "TK2 3f 優先順位の向き"
check_token "skills/gdd-pr-review/SKILL.md" "この 3f は敵対レーン + 内部整合レーンの入口" "TK3 3f レーン帰属"
check_token "skills/gdd-pr-review/SKILL.md" "分類根拠: 分類3（A型）/ 分類4（B型）/ 分類5（C型）/ 分類6（D型）/ 分類8（E型）" "TK4 3f 分類根拠の写像"
check_token "skills/gdd-pr-review/SKILL.md" "<!-- self-review-lane-provenance:start -->" "TK5 provenance 開始マーカー"
check_token "skills/gdd-pr-review/SKILL.md" "<!-- self-review-lane-provenance:end -->" "TK6 provenance 終了マーカー"

# --- followup: Fix 手順の 3 段固定（AC-10 の核心語は「3 段で固定」= 順序）---
# ①→②→③ の出現順を直接 pin する。②の逐語（`同型を全域 grep して検出・記録`）は下の第 2 引数群に
# 包含されるため、presence だけを見る check_token は置かない（同じ literal を 2 箇所で pin しない）。
check_order "skills/gdd-pr-review-followup/SKILL.md" "AC-10 Fix 3段固定(①②③の順序)" \
  "**①直す**" \
  "**②同型を全域 grep して検出・記録**" \
  "**③再 review**"
check_token "skills/gdd-pr-review-followup/SKILL.md" "opt-out 等価物の追加禁止" "opt-out等価物"

# T-25 impl-gate Attempt 2 申し送り（採用）: N1/N2/N3 は M-3 の記録スロット/消費者2本の判別力を守る pin token
check_token "skills/gdd-pr-review-followup/SKILL.md" "Ripple check（規律 A / 手順5 ②）" "N1 Ripple check記録スロット"
check_token "skills/gdd-pr-review-followup/SKILL.md" "対応する \`Ripple check\` 行が無い finding" "N2 続行対象"
check_token "skills/gdd-pr-review-followup/SKILL.md" "\`Ripple check\` 行が記録済み" "N3 終了条件"

# T-26 実装時に本文要件を埋め込んだ pin token。T-25 の本文意味破壊形（required→任意 /
# closed 禁止文の削除 / opt-out (vii) 削除 /「AI が行わない」の許可反転 / push 前証跡記録行の削除）を
# presence 一致で KILL する。②③ 出現順の反転は上の check_order が KILL する。
# 変異の形と観測結果は tasklist.md T-26 § Attempts の 4 列表が正本（ここに件数を書かない）。
check_token "skills/gdd-pr-review-followup/SKILL.md" "証跡記録は required" "Fix証跡required"
check_token "skills/gdd-pr-review-followup/SKILL.md" "インスタンス修正だけで closed にしてはならない" "closed宣言禁止(a)"
check_token "skills/gdd-pr-review-followup/SKILL.md" "closed として扱わない" "closed宣言禁止(b)"
check_token "skills/gdd-pr-review-followup/SKILL.md" "GDD_SKIP_PRE_PUSH_GATE\` / \`GDD_HOOK_STATE_DIR\` を書く" "opt-out(vii)"
check_token "skills/gdd-pr-review-followup/SKILL.md" "ユーザーの明示指示なしに AI が行わない" "opt-out禁止主文"
check_token "skills/gdd-pr-review-followup/SKILL.md" "push 前の証跡記録: \`git push\` する前に \`Pre-Push Self Review\` を記録する" "push前証跡記録"

check_token "references/self-review-lanes.md" "followup 周回時のレーン要求" "AC-23 followupレーン"
# AC-24 dry上限: token literal は T-17 § Verification Token（正本）から転記した literal（二重定義しない）
check_token "references/post-completion-pr-flow.md" "未到達のまま差し戻しが発生した回数" "AC-24 dry上限"

# --- T-27: 発火表の単一正本化（AC-7）とレーン正本の参照（AC-8）---
# 参照は「文字列があるだけ」では意味を持たないため、位置と本文要件の両方を pin する。
#   位置: check_order で前後の見出しに挟み、参照が語られるべき文脈の外へ移す変異を KILL する
#   本文: 「正本とする」「重複記載しない」等の要件語を token に埋め込み、見出しを残したまま
#         本文だけを骨抜きにする変異を KILL する
# 同一行に載る 2 語は check_order に並べない（行番号が単調増加にならないため）。片方は check_token に置く。
check_order "references/task-sizing.md" "AC-7 発火表の単一正本参照(位置)" \
  "## パスごとの違い" \
  "## セルフレビューのリスク比例発火" \
  "Task Size 別発火条件は \`references/self-review-lanes.md\` § リスク比例発火表 を正本とする" \
  "## パスごとの並列実行可否"
check_token "references/task-sizing.md" "ここでは重複記載しない" "AC-7 非重複(単一正本)"

# 上流アンカーに見出し `## Guardrails` は使わない。同 SKILL 内に「## Guardrails」節を参照）という
# 散文の言及が先行しており、check_order の初出行 semantics ではそちらを掴んで境界が緩む。
# 節冒頭の共通ルール参照文は同ファイル内で一意なので、こちらを Guardrails 節の開始点として使う。
check_order "skills/gdd-implementation-gating/SKILL.md" "AC-8 レーン正本参照(Guardrails 文脈)" \
  "共通ルールは \`references/common-guardrails.md\` を参照" \
  "実装差分のレビュー観点（3 レーン・10 分類）は \`references/self-review-lanes.md\` を正本とする"
# 参照側の一文が指す責務境界は、レーン正本側の節を実体として持つ（実在しない「対応表」を指していた
# T-27 Attempt 1 M-1 の remediation）。参照側 token と正本側 token を対で pin し、
# 片方だけを消す変異（= dangling reference の再発）をどちらの側からでも KILL する。
check_token "skills/gdd-implementation-gating/SKILL.md" "inline checklist と重複する観点の分類 ID は同 reference § inline checklist との責務境界 に従う" "AC-8 checklist との責務境界(参照側)"
check_order "references/self-review-lanes.md" "AC-8 checklist との責務境界(正本側)" \
  "## A〜E 型 ↔ 10 分類の対応表" \
  "### inline checklist との責務境界" \
  "\`references/inline-review-checklists.md\` は implementation-gating が走査する**検査項目**の正本、本ファイルは**レーン配置と分類 ID** の正本。両者が同じ欠陥を指す場合も走査は checklist 側で行い、finding に付ける分類 ID とレーンは本ファイルの 10 分類に従う（本節は severity を定めない。finding の severity は checklist 側 severity guideline とその上位正本 \`references/reviewer-common.md\` に従う。ただし \`dry\` 判定の severity には § followup 周回時のレーン要求 の例外規定が優先する）。" \
  "## 修正時規律"
# L-92: 上の check_order token 3 は 51 行**全文**を pin する。presence だけの分割 pin では
# 括弧内の severity 連鎖を丸ごと別節へ移す変異（gate 実測 S6 = SURVIVOR）が抜けるため、
# 位置（check_order）と本文（全文 literal）を 1 本にまとめた。同じ literal を 2 箇所で pin しない。
# 両側 pin の対向側。上の token は § inline checklist との責務境界 から carve-out を「指す」相互参照文だけを
# 縛るため、carve-out の実体（§ followup 周回時のレーン要求 の本文）は片側 pin のまま残っていた。
# 実体側を削除する / 否定を反転する（適用しない → 適用する）変異はどちらも参照側 token を壊さないので
# 無検出で空洞化経路を再開放できる。実体の述語そのものを literal で pin して両側から KILL する。
check_token "references/self-review-lanes.md" "「false positive 実績のある項目は severity を 1 段階下げる」規定は \`dry\` 判定には適用しない" "AC-8 dry carve-out(実体側)"

check_reference_closure "AC-8 参照側 skill の閉包"

if [[ "$FAIL" -ne 0 ]]; then
  echo "FAIL: self-review-lane-tokens"
  exit 1
fi
echo "self-review-lane-tokens: OK (self-review lane tokens present, fix stages ordered)"
echo "VERDICT: self-review-lane-tokens: OK"

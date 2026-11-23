#!/usr/bin/env bash
# Unit tests for hooks/scripts/lib/self-review-evidence.sh (bash, no framework).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=hooks/scripts/lib/self-review-evidence.sh
source "$PLUGIN_ROOT/hooks/scripts/lib/self-review-evidence.sh"

FAILS=0
assert_eq() {
  local desc="$1" expected="$2" actual="$3"
  if [[ "$expected" != "$actual" ]]; then
    echo "FAIL: $desc (expected='$expected' actual='$actual')"
    FAILS=$((FAILS + 1))
  else
    echo "PASS: $desc"
  fi
}

TMP="$(mktemp -d)"
# 途中終了を「成功」に見せないための sentinel。bash 3.2 実測では
# (1) EXIT trap の最後のコマンド（`rm`）の終了ステータスがスクリプトの終了ステータスを
# 上書きし、(2) set -u の unbound variable 打ち切り時は trap 内の `$?` すら 0 になる。
# そのため終了ステータスではなく「最後まで到達したか」を明示的に記録して判定する。
COMPLETED=0
trap '_rc=$?; rm -rf "$TMP"; if [[ "$COMPLETED" != "1" ]]; then echo "ABORTED before completion" >&2; exit 1; fi; exit "$_rc"' EXIT

# `<name>` の 1 行を書いたフィクスチャを作り、parse する。stderr は "$TMP/stderr" に退避する
# （bash の算術 syntax error 等が握り潰されていないことを検査するため）。
parse_line() {
  local _name="$1" _line="$2"
  printf '%s\n' "$_line" > "$TMP/$_name.md"
  : > "$TMP/stderr"
  gdd_parse_self_review_field "$TMP/$_name.md" "Pre-Push Self Review" 2>"$TMP/stderr"
}

# Task Size を明示して parse する（委譲 token の受理面検査用）。
parse_line_size() {
  local _name="$1" _line="$2" _size="$3"
  printf '%s\n' "$_line" > "$TMP/$_name.md"
  : > "$TMP/stderr"
  gdd_parse_self_review_field "$TMP/$_name.md" "Pre-Push Self Review" "$_size" 2>"$TMP/stderr"
}

VALID_LINE='Pre-Push Self Review: abc1234 | rounds: 3 | consecutive_clean: 2 | dry: yes | lanes: internal=2,grounding=1,adversarial=0 | at: 2026-08-17T00:00:00Z'

# --- 既存の基本ケース -------------------------------------------------------

parse_line valid "$VALID_LINE"
assert_eq "valid line parses ok" "true" "$GDD_SR_VALID"
assert_eq "sha extracted" "abc1234" "$GDD_SR_SHA"
assert_eq "rounds extracted" "3" "$GDD_SR_ROUNDS"
assert_eq "dry extracted" "yes" "$GDD_SR_DRY"
assert_eq "internal lane extracted" "2" "$GDD_SR_LANES_INTERNAL"
assert_eq "grounding lane extracted" "1" "$GDD_SR_LANES_GROUNDING"
assert_eq "adversarial lane extracted" "0" "$GDD_SR_LANES_ADVERSARIAL"

parse_line missing_key 'Pre-Push Self Review: abc1234 | rounds: 3 | dry: yes | lanes: internal=2,grounding=1,adversarial=0 | at: 2026-08-17T00:00:00Z'
assert_eq "missing consecutive_clean invalid" "false" "$GDD_SR_VALID"
assert_eq "missing key reported" "consecutive_clean" "$GDD_SR_MISSING_KEYS"

parse_line self_contradiction 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: yes | lanes: internal=1,grounding=not_applicable(no-external-dep),adversarial=0 | at: 2026-08-17T00:00:00Z'
assert_eq "dry=yes with consecutive_clean<2 is invalid" "false" "$GDD_SR_VALID"
assert_eq "contradiction reason code" "dry-consecutive-clean-contradiction" "$GDD_SR_MISSING_KEYS"

parse_line not_applicable 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=1,grounding=not_applicable(no-external-dep),adversarial=0 | at: 2026-08-17T00:00:00Z'
assert_eq "not_applicable with reason token is valid" "true" "$GDD_SR_VALID"

gdd_parse_self_review_field "$TMP/does-not-exist.md" "Pre-Push Self Review"
assert_eq "absent file is invalid" "false" "$GDD_SR_VALID"

# --- H-1: 多行値による検証迂回（値は必ず単一行・想定形式） -------------------

# sha に `dry:` を含めると `grep -o` 方式では GDD_SR_DRY が $'no\nyes' になり、
# `== "yes"` が false になって自己矛盾チェックごと迂回できた。
parse_line h1_sha_injection 'Pre-Push Self Review: dry:no-abc1234 | rounds: 1 | consecutive_clean: 0 | dry: yes | lanes: internal=0,grounding=0,adversarial=0 | at: 2026-08-17T00:00:00Z'
assert_eq "H-1 key string inside sha does not pollute dry" "yes" "$GDD_SR_DRY"
assert_eq "H-1 key string inside sha is invalid" "false" "$GDD_SR_VALID"
assert_eq "H-1 malformed sha reported" "sha" "$GDD_SR_MISSING_KEYS"

parse_line h1_sha_short 'Pre-Push Self Review: abc | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=0,grounding=0,adversarial=0 | at: 2026-08-17T00:00:00Z'
assert_eq "H-1 too short sha is invalid" "sha" "$GDD_SR_MISSING_KEYS"

parse_line h1_sha_long 'Pre-Push Self Review: abcdef0123456789abcdef0123456789abcdef012 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=0,grounding=0,adversarial=0 | at: 2026-08-17T00:00:00Z'
assert_eq "H-1 over-long sha is invalid" "sha" "$GDD_SR_MISSING_KEYS"

parse_line h1_sha_full 'Pre-Push Self Review: abcdef0123456789abcdef0123456789abcdef01 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=0,grounding=0,adversarial=0 | at: 2026-08-17T00:00:00Z'
assert_eq "H-1 full-length sha is valid" "true" "$GDD_SR_VALID"

# 同一 key の重複は先頭 1 マッチのみ採用する。`grep -o` 方式では多行値になり、
# `[[ ... -lt 2 ]]` が syntax error を出したまま if の条件位置で握り潰されていた。
parse_line h1_dup_cc 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | consecutive_clean: 2 | dry: yes | lanes: internal=0,grounding=0,adversarial=0 | at: 2026-08-17T00:00:00Z'
assert_eq "H-1 duplicate consecutive_clean takes first match" "0" "$GDD_SR_CONSECUTIVE_CLEAN"
assert_eq "H-1 duplicate consecutive_clean still blocks" "false" "$GDD_SR_VALID"
assert_eq "H-1 duplicate consecutive_clean reason code" "dry-consecutive-clean-contradiction" "$GDD_SR_MISSING_KEYS"
assert_eq "H-1 no stderr noise (no swallowed syntax error)" "" "$(cat "$TMP/stderr")"

parse_line h1_dup_dry 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | dry: yes | lanes: internal=0,grounding=0,adversarial=0 | at: 2026-08-17T00:00:00Z'
assert_eq "H-1 duplicate dry takes first match" "no" "$GDD_SR_DRY"
assert_eq "H-1 duplicate dry stays single-line" "true" "$GDD_SR_VALID"

# 先行ゼロを許すと `00` が `0|1` 照合も算術も擦り抜けて矛盾チェックを迂回できる。
parse_line h1_leading_zero 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 00 | dry: yes | lanes: internal=0,grounding=0,adversarial=0 | at: 2026-08-17T00:00:00Z'
assert_eq "H-1 non-canonical consecutive_clean is invalid" "false" "$GDD_SR_VALID"
assert_eq "H-1 non-canonical consecutive_clean reported" "consecutive_clean" "$GDD_SR_MISSING_KEYS"

# 抽出後の形式 assert（多行値は構造的に発生しないが二重に落とす）。
# `lanes` は値ドメインが「非空」だけなので、多行ガードが無いと通ってしまう key。
if declare -F _gdd_sr_check_value >/dev/null 2>&1; then
  RC_SINGLE=0
  _gdd_sr_check_value "lanes" "internal=2,grounding=1,adversarial=0" || RC_SINGLE=1
  RC_MULTI=0
  _gdd_sr_check_value "lanes" "$(printf 'internal=2\ninternal=3')" || RC_MULTI=1
  assert_eq "H-1 format assert accepts single-line value" "0" "$RC_SINGLE"
  assert_eq "H-1 format assert rejects multiline value" "1" "$RC_MULTI"
else
  assert_eq "H-1 format assert helper exists" "yes" "no"
fi

# --- H-2: lanes sub-key を必須キー集合と同じ規律で検査 -----------------------

parse_line h2_grounding_absent 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=2,adversarial=0 | at: 2026-08-17T00:00:00Z'
assert_eq "H-2 missing grounding lane is invalid" "false" "$GDD_SR_VALID"
assert_eq "H-2 missing grounding lane reported" "lanes.grounding" "$GDD_SR_MISSING_KEYS"

parse_line h2_grounding_empty 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=2,grounding=,adversarial=0 | at: 2026-08-17T00:00:00Z'
assert_eq "H-2 empty grounding lane is invalid" "false" "$GDD_SR_VALID"
assert_eq "H-2 empty grounding lane reported" "lanes.grounding" "$GDD_SR_MISSING_KEYS"

parse_line h2_adversarial_absent 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=2,grounding=1 | at: 2026-08-17T00:00:00Z'
assert_eq "H-2 missing adversarial lane is invalid" "false" "$GDD_SR_VALID"
assert_eq "H-2 missing adversarial lane reported" "lanes.adversarial" "$GDD_SR_MISSING_KEYS"

parse_line h2_adversarial_na 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=2,grounding=1,adversarial=not_applicable(docs-only) | at: 2026-08-17T00:00:00Z'
assert_eq "H-2 not_applicable adversarial is invalid" "false" "$GDD_SR_VALID"
assert_eq "H-2 not_applicable adversarial reported" "lanes.adversarial" "$GDD_SR_MISSING_KEYS"

parse_line h2_internal_na 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=not_applicable(docs-only),grounding=1,adversarial=0 | at: 2026-08-17T00:00:00Z'
assert_eq "H-2 not_applicable internal is invalid" "false" "$GDD_SR_VALID"
assert_eq "H-2 not_applicable internal reported" "lanes.internal" "$GDD_SR_MISSING_KEYS"

parse_line h2_two_lanes_absent 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=2 | at: 2026-08-17T00:00:00Z'
assert_eq "H-2 two missing lanes reported together" "lanes.grounding,lanes.adversarial" "$GDD_SR_MISSING_KEYS"

parse_line h2_lanes_absent 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | at: 2026-08-17T00:00:00Z'
assert_eq "H-2 missing lanes key is invalid" "false" "$GDD_SR_VALID"
assert_eq "H-2 missing lanes key reported without sub-key noise" "lanes" "$GDD_SR_MISSING_KEYS"

parse_line h2_at_absent 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=2,grounding=1,adversarial=0'
assert_eq "H-2 missing at key is invalid" "false" "$GDD_SR_VALID"
assert_eq "H-2 missing at key reported" "at" "$GDD_SR_MISSING_KEYS"

parse_line h2_grounding_bad_token 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=2,grounding=not_applicable(bogus),adversarial=0 | at: 2026-08-17T00:00:00Z'
assert_eq "H-2 unknown grounding token is invalid" "false" "$GDD_SR_VALID"
assert_eq "H-2 unknown grounding token reason code" "grounding-reason-token" "$GDD_SR_MISSING_KEYS"

# --- 独立レビュー #4 (2026-09-06): standard の委譲 token `independent-review` ----
# `standard` は接地・敵対レーンを独立レビューへ委譲する。回していないレーンに 0 を
# 書かせないため、委譲の記録形だけを受理する。

parse_line ir_grounding_delegated 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 1 | dry: yes | lanes: internal=2,grounding=not_applicable(independent-review),adversarial=not_applicable(independent-review) | at: 2026-08-17T00:00:00Z'
assert_eq "delegated grounding/adversarial is valid" "true" "$GDD_SR_VALID"
assert_eq "delegated grounding value is preserved" "not_applicable(independent-review)" "$GDD_SR_LANES_GROUNDING"

parse_line ir_adversarial_other_token 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=2,grounding=1,adversarial=not_applicable(test-only) | at: 2026-08-17T00:00:00Z'
assert_eq "adversarial rejects non-delegation token" "false" "$GDD_SR_VALID"
assert_eq "adversarial non-delegation token reported" "lanes.adversarial" "$GDD_SR_MISSING_KEYS"

parse_line ir_adversarial_bare 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=2,grounding=1,adversarial=not_applicable | at: 2026-08-17T00:00:00Z'
assert_eq "adversarial rejects bare not_applicable" "false" "$GDD_SR_VALID"

parse_line ir_internal_delegated 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=not_applicable(independent-review),grounding=1,adversarial=0 | at: 2026-08-17T00:00:00Z'
assert_eq "internal never accepts delegation token" "false" "$GDD_SR_VALID"
assert_eq "internal delegation token reported" "lanes.internal" "$GDD_SR_MISSING_KEYS"

# --- 独立レビュー R3 #10: 委譲 token は standard 限定 --------------------------
# `quick (standard)` / `quick (express)` は独立レビューを要求する gate が無いため、
# 委譲先が無いまま「回していないレーン」を非 0 件扱いで記録できてしまう。

_DELEGATED_LINE='Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 1 | dry: no | lanes: internal=2,grounding=not_applicable(independent-review),adversarial=not_applicable(independent-review) | at: 2026-08-17T00:00:00Z'

parse_line_size ir_delegation_standard "$_DELEGATED_LINE" "standard"
assert_eq "delegation token is valid for standard" "true" "$GDD_SR_VALID"

parse_line_size ir_delegation_quick_standard "$_DELEGATED_LINE" "quick (standard)"
assert_eq "delegation token is invalid for quick (standard)" "false" "$GDD_SR_VALID"
# R4 #3: grounding にも同じ size 判定を適用したため、両レーンが理由コードを載せる
# （検査順は GDD_SR_REQUIRED_LANE_KEYS の internal→grounding→adversarial）。
assert_eq "delegation token reason code" \
  "grounding-reason-token,adversarial-reason-token" "$GDD_SR_MISSING_KEYS"

parse_line_size ir_delegation_quick_express "$_DELEGATED_LINE" "quick (express)"
assert_eq "delegation token is invalid for quick (express)" "false" "$GDD_SR_VALID"

parse_line_size ir_numeric_quick_standard 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=2,grounding=1,adversarial=0 | at: 2026-08-17T00:00:00Z' "quick (standard)"
assert_eq "numeric adversarial stays valid for quick (standard)" "true" "$GDD_SR_VALID"

# --- 独立レビュー R4 #3: grounding 側の委譲 token も Task Size 依存 ------------
# adversarial だけ size 依存にすると、同じ委譲記録形が lane によって受理面の違う
# 非対称になる（R3 #10 で adversarial 側に閉じた穴が grounding 側に残る）。

_GROUNDING_ONLY_DELEGATED='Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=2,grounding=not_applicable(independent-review),adversarial=0 | at: 2026-08-17T00:00:00Z'

parse_line_size ir_grounding_delegation_standard "$_GROUNDING_ONLY_DELEGATED" "standard"
assert_eq "grounding delegation token is valid for standard" "true" "$GDD_SR_VALID"

parse_line_size ir_grounding_delegation_quick_standard "$_GROUNDING_ONLY_DELEGATED" "quick (standard)"
assert_eq "grounding delegation token is invalid for quick (standard)" "false" "$GDD_SR_VALID"
assert_eq "grounding delegation reason code" "grounding-reason-token" "$GDD_SR_MISSING_KEYS"

parse_line_size ir_grounding_delegation_quick_express "$_GROUNDING_ONLY_DELEGATED" "quick (express)"
assert_eq "grounding delegation token is invalid for quick (express)" "false" "$GDD_SR_VALID"

# 他の理由 token は size 非依存のまま（委譲ではないので受理面を狭めない）。
parse_line_size ir_grounding_docs_only_quick 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=2,grounding=not_applicable(docs-only),adversarial=0 | at: 2026-08-17T00:00:00Z' "quick (standard)"
assert_eq "grounding docs-only stays valid for quick (standard)" "true" "$GDD_SR_VALID"

# adversarial 単独の委譲 token は従来どおり adversarial の理由コードだけを載せる。
parse_line_size ir_adversarial_only_delegated 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=2,grounding=1,adversarial=not_applicable(independent-review) | at: 2026-08-17T00:00:00Z' "quick (standard)"
assert_eq "adversarial-only delegation is invalid for quick (standard)" "false" "$GDD_SR_VALID"
assert_eq "adversarial-only delegation reason code" "adversarial-reason-token" "$GDD_SR_MISSING_KEYS"

# --- O-1: lanes 末尾の grounding が ` | at: ...` を飲まない -------------------

parse_line o1_grounding_tail_na 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=2,adversarial=0,grounding=not_applicable(docs-only) | at: 2026-08-17T00:00:00Z'
assert_eq "O-1 trailing grounding not_applicable is valid" "true" "$GDD_SR_VALID"
assert_eq "O-1 trailing grounding value is not polluted" "not_applicable(docs-only)" "$GDD_SR_LANES_GROUNDING"

parse_line o1_grounding_tail_num 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=2,adversarial=0,grounding=1 | at: 2026-08-17T00:00:00Z'
assert_eq "O-1 trailing grounding count is not polluted" "1" "$GDD_SR_LANES_GROUNDING"

# --- O-2: 値ドメイン検証 ----------------------------------------------------

parse_line o2_dry_domain 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 2 | dry: maybe | lanes: internal=2,grounding=1,adversarial=0 | at: 2026-08-17T00:00:00Z'
assert_eq "O-2 dry outside yes|no is invalid" "false" "$GDD_SR_VALID"
assert_eq "O-2 dry domain violation reported" "dry" "$GDD_SR_MISSING_KEYS"

parse_line o2_cc_trailing 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 2abc | dry: no | lanes: internal=2,grounding=1,adversarial=0 | at: 2026-08-17T00:00:00Z'
assert_eq "O-2 non-numeric consecutive_clean is invalid" "false" "$GDD_SR_VALID"

parse_line o2_at_domain 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=2,grounding=1,adversarial=0 | at: yesterday'
assert_eq "O-2 non ISO-8601 at is invalid" "false" "$GDD_SR_VALID"

parse_line o2_at_trailing 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=2,grounding=1,adversarial=0 | at: 2026-08-17T00:00:00Z trailing junk'
assert_eq "O-2 at with trailing junk is invalid" "at" "$GDD_SR_MISSING_KEYS"

# --- 既存の受理面が壊れていないこと（区切り両対応 / 並び順非依存 / markdown 前置）

parse_line delimiter_eq 'Pre-Push Self Review= abc1234 | rounds= 3 | consecutive_clean= 2 | dry= yes | lanes= internal=2,grounding=1,adversarial=0 | at= 2026-08-17T00:00:00Z'
assert_eq "equals delimiter accepted" "true" "$GDD_SR_VALID"

parse_line reordered 'Pre-Push Self Review: abc1234 | at: 2026-08-17T00:00:00Z | lanes: internal=2,grounding=1,adversarial=0 | dry: yes | consecutive_clean: 2 | rounds: 3'
assert_eq "top-level key order independent" "true" "$GDD_SR_VALID"

parse_line markdown_prefix '- `Pre-Push Self Review`: abc1234 | rounds: 3 | consecutive_clean: 2 | dry: yes | lanes: internal=2,grounding=1,adversarial=0 | at: 2026-08-17T00:00:00Z'
assert_eq "markdown bullet + backtick prefix accepted" "true" "$GDD_SR_VALID"

printf 'Pre-Push Self Review: abc1234 | rounds: 3 | consecutive_clean: 2 | dry: yes | lanes: internal=2,grounding=1,adversarial=0 | at: 2026-08-17T00:00:00Z\r\n' > "$TMP/crlf.md"
gdd_parse_self_review_field "$TMP/crlf.md" "Pre-Push Self Review"
assert_eq "CRLF line accepted" "true" "$GDD_SR_VALID"

# 状態持ち越しなし
parse_line valid_again "$VALID_LINE"
gdd_parse_self_review_field "$TMP/does-not-exist.md" "Pre-Push Self Review"
assert_eq "globals reset between calls" "" "$GDD_SR_SHA"
assert_eq "missing file reason code" "file" "$GDD_SR_MISSING_KEYS"

# --- O-4: 引数なし呼び出しで呼び出し元を落とさない ---------------------------

gdd_parse_self_review_field
assert_eq "no-arg call is invalid, not fatal" "false" "$GDD_SR_VALID"
assert_eq "no-arg reason code" "args" "$GDD_SR_MISSING_KEYS"

# --- O-5: 読み取り不可ファイルを field 欠落と区別する -------------------------

printf '%s\n' "$VALID_LINE" > "$TMP/unreadable.md"
chmod 000 "$TMP/unreadable.md"
if [[ -r "$TMP/unreadable.md" ]]; then
  echo "SKIP: unreadable-file case (running with read override)"
else
  gdd_parse_self_review_field "$TMP/unreadable.md" "Pre-Push Self Review"
  assert_eq "unreadable file is invalid" "false" "$GDD_SR_VALID"
  assert_eq "unreadable file reason code" "file-unreadable" "$GDD_SR_MISSING_KEYS"
fi
chmod 644 "$TMP/unreadable.md"

# --- M-1: 必須 key 集合の 2 定数が実際に「正本」であること ---------------------
# T-5 § Carry Forward が T-6 / T-7 に渡している契約は「key の追加はこの 2 定数を変える
# だけ」。個別分岐を持たない key が silent pass すると、契約どおりに key を足した次の
# タスクでその key が無検査のまま通り、H-2 と同じ失敗モードが再生産される。
# 定数を一時的に拡張して「足した key が実際に必須として効く」ことを機械的に固定する。

_SAVED_TOP_KEYS="$GDD_SR_REQUIRED_TOP_KEYS"
_SAVED_LANE_KEYS="$GDD_SR_REQUIRED_LANE_KEYS"

GDD_SR_REQUIRED_TOP_KEYS="$_SAVED_TOP_KEYS newkey"
parse_line m1_top_key_absent "$VALID_LINE"
assert_eq "M-1 key added to REQUIRED_TOP_KEYS blocks when absent" "false" "$GDD_SR_VALID"
assert_eq "M-1 unknown top key reported by name" "newkey" "$GDD_SR_MISSING_KEYS"

parse_line m1_top_key_empty "$VALID_LINE | newkey:"
assert_eq "M-1 unknown top key with empty value blocks" "false" "$GDD_SR_VALID"
assert_eq "M-1 unknown top key empty value reported" "newkey" "$GDD_SR_MISSING_KEYS"

parse_line m1_top_key_present "$VALID_LINE | newkey: present"
assert_eq "M-1 unknown top key with value passes" "true" "$GDD_SR_VALID"
GDD_SR_REQUIRED_TOP_KEYS="$_SAVED_TOP_KEYS"

GDD_SR_REQUIRED_LANE_KEYS="$_SAVED_LANE_KEYS newlane"
parse_line m1_lane_key_absent "$VALID_LINE"
assert_eq "M-1 key added to REQUIRED_LANE_KEYS blocks when absent" "false" "$GDD_SR_VALID"
assert_eq "M-1 unknown lane key reported with lanes prefix" "lanes.newlane" "$GDD_SR_MISSING_KEYS"

parse_line m1_lane_key_present 'Pre-Push Self Review: abc1234 | rounds: 3 | consecutive_clean: 2 | dry: yes | lanes: internal=2,grounding=1,adversarial=0,newlane=7 | at: 2026-08-17T00:00:00Z'
assert_eq "M-1 unknown lane key with value passes" "true" "$GDD_SR_VALID"
GDD_SR_REQUIRED_LANE_KEYS="$_SAVED_LANE_KEYS"

parse_line m1_constants_restored "$VALID_LINE"
assert_eq "M-1 required key constants restored after probe" "true" "$GDD_SR_VALID"

# --- M-2: 独立 mutation で生存した 3 形の判別力ガード -------------------------
# いずれも実装は既に正しく、境界を判別するテストだけが欠けていた形。

# 理由 token なしの裸 `not_applicable`。既存テストは `not_applicable(bogus)` =
# 語彙照合側しか踏まないため、reject 分岐そのものを消す変異が生存していた。
parse_line m2_bare_not_applicable 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=2,grounding=not_applicable,adversarial=0 | at: 2026-08-17T00:00:00Z'
assert_eq "M-2 bare not_applicable grounding is invalid" "false" "$GDD_SR_VALID"
assert_eq "M-2 bare not_applicable reason code" "grounding-reason-token" "$GDD_SR_MISSING_KEYS"

# 2026-09-06 改訂: 「2 連続」要件の撤廃（正本: references/self-review-lanes.md
# § followup 周回時のレーン要求）に伴い、矛盾判定の閾値は `< 2` から `== 0` へ緩んだ。
# `consecutive_clean: 1`（= 内部整合レーン 1 周が clean）は **valid** になる。
# 閾値を 2 へ戻す変異はここで KILL される（cc=0 側は上の self_contradiction が固定）。
parse_line m2_cc_one_is_valid_after_two_consecutive_requirement_removed 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 1 | dry: yes | lanes: internal=2,grounding=1,adversarial=0 | at: 2026-08-17T00:00:00Z'
assert_eq "M-2 consecutive_clean=1 with dry=yes is valid (2 連続要件の撤廃)" "true" "$GDD_SR_VALID"
assert_eq "M-2 consecutive_clean=1 leaves no missing-key reason" "" "$GDD_SR_MISSING_KEYS"

# key 照合は segment 先頭一致。部分一致に緩めると別 key の部分文字列で必須 key を
# 満たせてしまう（H-1 の「値の混線で検証を迂回する」クラスの再発口）。
parse_line m2_lane_key_boundary 'Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 | dry: no | lanes: internal=0,xgrounding=1,adversarial=0 | at: 2026-08-17T00:00:00Z'
assert_eq "M-2 lane key match is anchored at segment head" "false" "$GDD_SR_VALID"
assert_eq "M-2 partial lane key does not satisfy grounding" "lanes.grounding" "$GDD_SR_MISSING_KEYS"

parse_line m2_top_key_boundary 'Pre-Push Self Review: abc1234 | rounds: 1 | xconsecutive_clean: 2 | dry: no | lanes: internal=0,grounding=1,adversarial=0 | at: 2026-08-17T00:00:00Z'
assert_eq "M-2 top-level key match is anchored at segment head" "false" "$GDD_SR_VALID"
assert_eq "M-2 partial top-level key does not satisfy consecutive_clean" "consecutive_clean" "$GDD_SR_MISSING_KEYS"

# 上の 2 本は「別 key の部分文字列で必須 key を満たせない」方向だけを見ており、照合だけを
# 部分一致に緩めた変異は値ドメイン assert に阻まれて invalid のまま生存する。decoy segment
# を真の key より前に置き、真の値が横取りされずに取れることまで固定して両方向を塞ぐ。
parse_line m2_decoy_does_not_shadow 'Pre-Push Self Review: abc1234 | xrounds: 9 | rounds: 3 | consecutive_clean: 2 | dry: no | lanes: xgrounding=9,internal=2,grounding=1,adversarial=0 | at: 2026-08-17T00:00:00Z'
assert_eq "M-2 decoy segment does not shadow the real key" "true" "$GDD_SR_VALID"
assert_eq "M-2 real grounding value survives a decoy segment" "1" "$GDD_SR_LANES_GROUNDING"
assert_eq "M-2 real rounds value survives a decoy segment" "3" "$GDD_SR_ROUNDS"

# --- O-3: detect-steering.sh の再 source でグローバルを巻き戻さない -----------

GDD_STEERING_DIR="/already/resolved"
# shellcheck source=hooks/scripts/lib/self-review-evidence.sh
source "$PLUGIN_ROOT/hooks/scripts/lib/self-review-evidence.sh"
assert_eq "O-3 re-source keeps resolved steering globals" "/already/resolved" "$GDD_STEERING_DIR"

# --- A-23 / A-24: T-5 impl-gate Attempt 3 advisory の回帰ガード（AC-6） -------
# 実装は既に正しい（T-5 Attempt 3 で fail-closed を確認済み）ため、ここは RED では
# なく判別力のある回帰ガードの追加。production code に変更は必要ない想定。

# A-23: lanes キー自体が丸ごと欠落した2回目の呼び出しで、前回呼び出しの
# GDD_SR_LANES_ADVERSARIAL 等が持ち越されずリセットされること。lanes sub-key の
# store は「lanes 本体が取れたときだけ」回すループ内でしか行われないため、関数先頭の
# 明示リセット行を消す変異は sub-key ループが走らないケースでのみ検出できる。
parse_line a23_lanes_present 'Pre-Push Self Review: abc1234 | rounds: 3 | consecutive_clean: 2 | dry: yes | lanes: internal=2,grounding=1,adversarial=9 | at: 2026-08-17T00:00:00Z'
assert_eq "A-23 baseline adversarial lane set" "9" "$GDD_SR_LANES_ADVERSARIAL"

parse_line a23_lanes_absent 'Pre-Push Self Review: abc1234 | rounds: 3 | consecutive_clean: 2 | dry: yes | at: 2026-08-17T00:00:00Z'
assert_eq "A-23 lanes key entirely absent is invalid" "false" "$GDD_SR_VALID"
assert_eq "A-23 adversarial global does not carry over when lanes entirely absent" "" "$GDD_SR_LANES_ADVERSARIAL"

# A-24: field 行そのものがファイルに存在しない場合、reason code は個別 key の
# コンマ列挙ではなく field 名そのもの。`[[ -n "$_line" ]] || { GDD_SR_MISSING_KEYS="$_field"; ... }`
# の早期 return を消す変異は、抽出ループが空文字を全 key に流して個別 key 名の列挙を
# 返すため判別できる。
printf 'Some other content\nNo self review line in this file.\n' > "$TMP/a24_field_absent.md"
gdd_parse_self_review_field "$TMP/a24_field_absent.md" "Pre-Push Self Review"
assert_eq "A-24 evidence line entirely absent is invalid" "false" "$GDD_SR_VALID"
assert_eq "A-24 evidence line absent reason is the field name, not a key enumeration" "Pre-Push Self Review" "$GDD_SR_MISSING_KEYS"

# --- T-6: gdd_pre_push_resolve_steering（AC-25） -----------------------------
# design.md § steering resolver の設計。呼び出し規約は gdd_detect_active_steering と
# 同じ: 呼び出し側が対象 root へ非 subshell で `cd` してから呼ぶ（結果はグローバル変数
# で返るため、subshell `( cd ... && fn )` 越しに呼ぶと親プロセスに伝播しない）。

_T6_CALLER_PWD="$PWD"

_t6_init_repo() {
  local _repo="$1"
  git init -q -b main "$_repo"
  git -C "$_repo" config user.email test@example.com
  git -C "$_repo" config user.name "Test User"
}

_t6_write_state() {
  local _repo="$1" _slug="$2" _resume_from="$3" _next_action="$4"
  mkdir -p "$_repo/.steering/$_slug"
  cat > "$_repo/.steering/$_slug/state.md" <<EOF
Resume From: $_resume_from
Human Check Status: approved
Route In Progress: none
Next Action: $_next_action
Started At: 2026-01-01T00:00:00Z
EOF
}

# T6-1: primary（gdd_detect_active_steering）が found を返す場合はそれを最優先で
# 採用し、union 側に done candidate が同時に存在してもそちらへ引きずられない
# （design.md「上が found 以外を返した場合に限り ... 候補を拾う」の前提条件）。
# union を無条件に実行する変異は done-task を誤って拾い GDD_PP_STEERING_DIR が
# ずれるため判別できる。
T6_A="$TMP/t6-primary-precedence"
_t6_init_repo "$T6_A"
_t6_write_state "$T6_A" "20260101-active-task" "gdd-implementation-gating" "gdd-implementation-gating"
_t6_write_state "$T6_A" "20260102-done-task" "done" "done"
cd "$T6_A"
gdd_pre_push_resolve_steering "$T6_A"
cd "$_T6_CALLER_PWD"
assert_eq "T6-1 primary found takes precedence over union done candidate" "found" "$GDD_PP_STEERING_STATUS"
assert_eq "T6-1 resolved dir is the active task, not the done task" "$T6_A/.steering/20260101-active-task" "$GDD_PP_STEERING_DIR"

# T6-2 / T6-3: union の候補条件は `Resume From == done || Next Action == done`。
# 両方を同時に done にした fixture だけでは `||` を `&&` に縮める変異を判別しない
# ので、片方だけ done にした fixture を 2 本用意して両方向を固定する。
T6_B="$TMP/t6-union-resume-from-done"
_t6_init_repo "$T6_B"
_t6_write_state "$T6_B" "20260101-task" "done" "gdd-implementation-gating"
cd "$T6_B"
gdd_pre_push_resolve_steering "$T6_B"
cd "$_T6_CALLER_PWD"
assert_eq "T6-2 Resume From=done alone resolves via union (OR, not AND)" "found" "$GDD_PP_STEERING_STATUS"

T6_C="$TMP/t6-union-next-action-done"
_t6_init_repo "$T6_C"
_t6_write_state "$T6_C" "20260101-task" "gdd-implementation-gating" "done"
cd "$T6_C"
gdd_pre_push_resolve_steering "$T6_C"
cd "$_T6_CALLER_PWD"
assert_eq "T6-3 Next Action=done alone resolves via union (OR, not AND)" "found" "$GDD_PP_STEERING_STATUS"

# T6-4: union candidate が 2 件以上なら fail-closed で multiple。1 件だけを黙って
# 採用する形は fail-open 経路
# 4(i)（.steering に候補を増やす迂回）そのものになる。
T6_D="$TMP/t6-union-multiple"
_t6_init_repo "$T6_D"
_t6_write_state "$T6_D" "20260101-done-a" "done" "done"
_t6_write_state "$T6_D" "20260102-done-b" "done" "done"
cd "$T6_D"
gdd_pre_push_resolve_steering "$T6_D"
cd "$_T6_CALLER_PWD"
assert_eq "T6-4 two union candidates is multiple, not silently picked" "multiple" "$GDD_PP_STEERING_STATUS"
assert_eq "T6-4 multiple reason code" "multiple-terminal" "$GDD_PP_STEERING_REASON"

# T6-5: primary 自体が multiple を返す場合（2 件のアクティブ steering）は union
# フォールバックを試さずそのまま multiple を伝播する。primary の multiple を無視して
# union だけを見る変異は、done candidate が 0 件のため誤って none/no-candidate に
# 倒れる（判別可能）。
T6_E="$TMP/t6-primary-multiple"
_t6_init_repo "$T6_E"
_t6_write_state "$T6_E" "20260101-active-a" "gdd-implementation-gating" "gdd-implementation-gating"
_t6_write_state "$T6_E" "20260102-active-b" "gdd-design-gating" "gdd-design-gating"
cd "$T6_E"
gdd_pre_push_resolve_steering "$T6_E"
cd "$_T6_CALLER_PWD"
assert_eq "T6-5 primary multiple propagates without union fallback" "multiple" "$GDD_PP_STEERING_STATUS"
assert_eq "T6-5 primary multiple reason code" "multiple" "$GDD_PP_STEERING_REASON"

# T6-6: `.steering/` が存在しない（trivial task 相当）場合は none/no-candidate。
# design.md § opt-out ログ「trivial タスクは `.steering/` を作らないため毎回
# no-candidate に落ちる（設計上の正常系）」と対応させる。
T6_F="$TMP/t6-no-steering-dir"
_t6_init_repo "$T6_F"
cd "$T6_F"
gdd_pre_push_resolve_steering "$T6_F"
cd "$_T6_CALLER_PWD"
assert_eq "T6-6 no .steering dir resolves to none" "none" "$GDD_PP_STEERING_STATUS"
assert_eq "T6-6 no .steering dir reason is no-candidate" "no-candidate" "$GDD_PP_STEERING_REASON"

# T6-7: blocked 統一（design.md「blocked steering の扱いを両経路で統一する」）。
# `gdd_detect_active_steering` 自身の fallback は Resume From=blocked を除外するため
# （hooks/scripts/lib/detect-steering.sh 実装）、primary だけでは none になる。union 側が
# blocked を候補に含めて拾わない限り found にならない。
T6_G="$TMP/t6-blocked-unification"
_t6_init_repo "$T6_G"
_t6_write_state "$T6_G" "20260101-blocked-task" "blocked" "gdd-implementation-gating"
cd "$T6_G"
gdd_pre_push_resolve_steering "$T6_G"
cd "$_T6_CALLER_PWD"
assert_eq "T6-7 blocked steering resolves as found (unified with registry path)" "found" "$GDD_PP_STEERING_STATUS"

# T6-8: project_root がそもそも git repo でない場合は none/not-a-git-repo。
T6_H="$TMP/t6-not-a-git-repo"
mkdir -p "$T6_H"
cd "$T6_H"
gdd_pre_push_resolve_steering "$T6_H"
cd "$_T6_CALLER_PWD"
assert_eq "T6-8 non-git project_root resolves to none" "none" "$GDD_PP_STEERING_STATUS"
assert_eq "T6-8 non-git project_root reason is not-a-git-repo" "not-a-git-repo" "$GDD_PP_STEERING_REASON"

# T6-9: `.steering/` 自体は存在するが候補が全て cancelled（done でも blocked でもない）
# の場合、「.steering が無かった」(no-candidate) とは区別し terminal-only とする。
# design.md の reason 列挙に terminal-only は存在するが個別の発火条件は明記されていない
# ため、この解釈は推論。実装時に食い違う場合は本 assertion を見直すこと（RED Evidence の
# Carry Forward 参照）。
T6_I="$TMP/t6-terminal-only"
_t6_init_repo "$T6_I"
_t6_write_state "$T6_I" "20260101-cancelled-task" "cancelled" "cancelled"
cd "$T6_I"
gdd_pre_push_resolve_steering "$T6_I"
cd "$_T6_CALLER_PWD"
assert_eq "T6-9 steering dir with only cancelled candidates is none" "none" "$GDD_PP_STEERING_STATUS"
assert_eq "T6-9 cancelled-only reason is terminal-only (distinct from no-candidate)" "terminal-only" "$GDD_PP_STEERING_REASON"

# --- T-7: gdd_sr_log_event（AC-4 / AC-19）------------------------------------
# design.md § opt-out / 可観測化ログ（確定版）を正本とする。tasklist Step 1
# ドラフトの write-failure アサーションは `WRITE_STATUS=$?` を `set -e` 下で
# 素の文として実行しており、関数が 1 を返した時点でテストスクリプト自体が
# abort する（意図した RED ではなく誤 abort）。`|| VAR=$?` に修正し、かつ
# 「optout の書き込み失敗のみ block」（design.md 189 行目）の両方向 —
# optout=block / それ以外の event=best-effort（記録失敗で push を止めない）—
# を固定する。ドラフトは block 側しか踏んでおらず best-effort 側の分岐が
# 無検査だった（Next Exact Step が名指しした 4 点の 1 つ）。

export GDD_HOOK_STATE_DIR="$TMP/hook-state-t7"
LOGFILE="$GDD_HOOK_STATE_DIR/pre-push-optout.log"

# T7-1: 基本の書式・パーミッション・via/head/reason フィールド。
# AC-4 の testable claim「ログ行に via: と head: が含まれる」に対応。
gdd_sr_log_event "optout" "-" "$TMP/repo-a" "deadbeef0123456789" "command-prefix"
assert_eq "T7-1 log file created" "true" "$([[ -f "$LOGFILE" ]] && echo true || echo false)"
assert_eq "T7-1 log contains event field" "1" "$(grep -c '| event: optout |' "$LOGFILE")"
assert_eq "T7-1 log contains via field" "1" "$(grep -c 'via: command-prefix$' "$LOGFILE")"
assert_eq "T7-1 log contains head field" "1" "$(grep -c '| head: deadbeef0123456789 |' "$LOGFILE")"
assert_eq "T7-1 log contains dash reason placeholder" "1" "$(grep -c '| reason: - |' "$LOGFILE")"
T7_PERM="$(stat -f '%Lp' "$LOGFILE" 2>/dev/null || stat -c '%a' "$LOGFILE" 2>/dev/null)"
assert_eq "T7-1 log file is 0600" "600" "$T7_PERM"

# T7-2: append-only（上書きではなく行が増える）。design.md 181 行目
# 「append-only、1 行」/ 190 行目「ローテーションは行わない」と対応。
gdd_sr_log_event "unresolved-steering" "no-candidate" "$TMP/repo-b" "cafebabe" "-"
assert_eq "T7-2 second call appends, does not overwrite" "2" "$(wc -l < "$LOGFILE" | tr -d ' ')"
assert_eq "T7-2 second line has its own event" "1" "$(grep -c '| event: unresolved-steering |' "$LOGFILE")"
assert_eq "T7-2 second line reason code recorded" "1" "$(grep -c '| reason: no-candidate |' "$LOGFILE")"
assert_eq "T7-2 second line via dash placeholder" "1" "$(grep -c 'via: -$' "$LOGFILE")"
assert_eq "T7-2 first line untouched by second call" "1" "$(grep -c '| event: optout |' "$LOGFILE")"

# T7-3: repo は非可逆 ID。絶対パスはもちろん、リポジトリ名（basename）も
# ログに出ない（design.md 186 行目「絶対パスも repo 名も worktree slug も
# 書かない」/ AC-18 の秘匿方針との整合）。
SECRET_REPO="$TMP/repo-secret-project-name"
mkdir -p "$SECRET_REPO"
gdd_sr_log_event "optout" "-" "$SECRET_REPO" "0000000" "process-env"
assert_eq "T7-3 raw absolute path not leaked" "0" "$(grep -c "$SECRET_REPO" "$LOGFILE")"
assert_eq "T7-3 repo basename not leaked" "0" "$(grep -c 'repo-secret-project-name' "$LOGFILE")"

# T7-4: 同一 repo_root は毎回同じ repo id を生成する（決定的ハッシュ。ランダム値
# やタイムスタンプ由来の id にすり替える変異はここで判別できる）。
REPO_X="$TMP/repo-determinism-x"
mkdir -p "$REPO_X"
gdd_sr_log_event "hook-error" "-" "$REPO_X" "1111111" "-"
ID_CALL_1="$(grep 'event: hook-error' "$LOGFILE" | tail -1 | sed -n 's/.*repo: \([^ ]*\) .*/\1/p')"
gdd_sr_log_event "hook-error" "-" "$REPO_X" "2222222" "-"
ID_CALL_2="$(grep 'event: hook-error' "$LOGFILE" | tail -1 | sed -n 's/.*repo: \([^ ]*\) .*/\1/p')"
assert_eq "T7-4 same repo_root yields same repo id across calls" "$ID_CALL_1" "$ID_CALL_2"

# T7-5: basename が同じでも repo_root（絶対パス全体）が違えば別の repo id に
# なる。「basename だけをハッシュする」実装の取り違えを判別する — design.md
# 186 行目は絶対パスをハッシュ元と規定しており、basename 一致だけで同一視して
# はいけない。
REPO_Y1="$TMP/group-a/same-name"
REPO_Y2="$TMP/group-b/same-name"
mkdir -p "$REPO_Y1" "$REPO_Y2"
gdd_sr_log_event "session-mismatch" "-" "$REPO_Y1" "3333333" "-"
ID_Y1="$(grep 'event: session-mismatch' "$LOGFILE" | tail -1 | sed -n 's/.*repo: \([^ ]*\) .*/\1/p')"
gdd_sr_log_event "session-mismatch" "-" "$REPO_Y2" "4444444" "-"
ID_Y2="$(grep 'event: session-mismatch' "$LOGFILE" | tail -1 | sed -n 's/.*repo: \([^ ]*\) .*/\1/p')"
assert_eq "T7-5 different repo_root with same basename yields different repo id" "false" "$([[ "$ID_Y1" == "$ID_Y2" ]] && echo true || echo false)"

# T7-6: timestamp は ISO 8601（design.md 182 行目）。
TS_LINE="$(head -1 "$LOGFILE")"
TS_FIELD="${TS_LINE%% |*}"
case "$TS_FIELD" in
  [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z) TS_OK=true ;;
  *) TS_OK=false ;;
esac
assert_eq "T7-6 timestamp field is ISO 8601" "true" "$TS_OK"

# T7-9（impl-gate Attempt 1 / M-2）: repo id は「小文字 hex ちょうど 8 桁」。
# T7-5 は「2 つの repo_root の id が異なる」ことしか見ないため、`cut -c1-8` を
# 1〜3 文字に縮める変異は衝突しない限り通過する確率依存のガードにしかならず、
# gate 独立 mutation で 5/5 生存した。ここでは長さと文字種を同時に固定し、
# 切り詰め削除（full sha1 化）と過剰な切り詰めの両方向を決定的に殺す
# （design.md 186 行「絶対パスの sha1 先頭 8 桁」）。前後の `| ` と ` | head: ` で
# フィールド境界を挟むため、8 桁ちょうど以外はマッチしない。
# ここまでに書かれた全行を母数にして、行単位の取りこぼしも作らない。
assert_eq "T7-9 every repo id is exactly 8 lowercase hex chars" \
  "$(wc -l < "$LOGFILE" | tr -d ' ')" \
  "$(grep -c '| repo: [0-9a-f]\{8\} | head: ' "$LOGFILE")"

# T7-10（impl-gate Attempt 1 / M-1）: timestamp は UTC。T7-6 は ISO 8601 の *形* しか
# 見ないため、`date -u` から `-u` を落として local 時刻を `Z` 付きで記録する変異
# （design.md 182 行の書式が含意する UTC 違反）が生き残る。design.md 185 行の S-4
# fail-open 母数の測定は記録値が実時刻順であることに依存するため無検査にできない。
# host の TZ に判別力を左右させないよう、UTC からずれた TZ を明示的に強制して記録し、
# 記録値を UTC として解釈した epoch が実 UTC と ±120 秒以内であることを固定する。
_t7_iso_to_epoch() {
  local _iso="$1"
  # BSD date（macOS）と GNU date（Linux）の両方を順に試す。
  date -u -j -f '%Y-%m-%dT%H:%M:%SZ' "$_iso" +%s 2>/dev/null ||
    date -u -d "$_iso" +%s 2>/dev/null
}

# 実際に UTC からずれる TZ を 1 つ選ぶ（zoneinfo 不在環境向けに POSIX 形式も候補）。
T7_SKEW_TZ=""
for _t7_tz in "Asia/Tokyo" "America/New_York" "XXX-09"; do
  _t7_local_as_utc="$(TZ="$_t7_tz" date +%Y-%m-%dT%H:%M:%SZ)"
  _t7_local_epoch="$(_t7_iso_to_epoch "$_t7_local_as_utc")" || _t7_local_epoch=""
  _t7_utc_epoch="$(date -u +%s)"
  if [[ -n "$_t7_local_epoch" ]] &&
    [[ "$((_t7_local_epoch - _t7_utc_epoch))" -ge 3600 ||
      "$((_t7_local_epoch - _t7_utc_epoch))" -le -3600 ]]; then
    T7_SKEW_TZ="$_t7_tz"
    break
  fi
done

if [[ -n "$T7_SKEW_TZ" ]]; then
  ( export TZ="$T7_SKEW_TZ"
    gdd_sr_log_event "hook-error" "-" "$TMP/repo-utc" "7777777" "-" )
  T7_UTC_TS_LINE="$(tail -1 "$LOGFILE")"
  T7_UTC_TS="${T7_UTC_TS_LINE%% |*}"
  T7_NOW_EPOCH="$(date -u +%s)"
  T7_TS_EPOCH="$(_t7_iso_to_epoch "$T7_UTC_TS")" || T7_TS_EPOCH=""
  T7_TS_DRIFT=-1
  if [[ -n "$T7_TS_EPOCH" ]]; then
    T7_TS_DRIFT=$((T7_TS_EPOCH - T7_NOW_EPOCH))
    if [[ "$T7_TS_DRIFT" -lt 0 ]]; then
      T7_TS_DRIFT=$((-T7_TS_DRIFT))
    fi
  fi
  assert_eq "T7-10 timestamp is UTC, not local time labeled Z (TZ=$T7_SKEW_TZ)" \
    "true" "$([[ "$T7_TS_DRIFT" -ge 0 && "$T7_TS_DRIFT" -le 120 ]] && echo true || echo false)"
else
  # TZ を強制しても UTC からずらせない環境では、この形の変異は原理的に観測できない。
  echo "SKIP: T7-10 UTC timestamp case (no non-UTC timezone available)"
fi

# T7-7 / T7-8: 書き込み失敗時の block/best-effort の非対称（design.md 189 行目
# 「optout は block。それ以外の event は best-effort（記録失敗で push を
# 止めない）」）。tasklist Step 1 ドラフトは T7-7 側（optout=block）しか踏んで
# おらず、T7-8（非 optout=best-effort）が無いと block/best-effort の分岐
# そのものを消して「常に block」または「常に成功」にする変異を判別できない。
READONLY_DIR="$TMP/t7-readonly"
mkdir -p "$READONLY_DIR"
chmod 500 "$READONLY_DIR"

T7_OPTOUT_STATUS=0
( export GDD_HOOK_STATE_DIR="$READONLY_DIR/nested"
  gdd_sr_log_event "optout" "-" "$TMP/repo-fail" "5555555" "process-env" ) || T7_OPTOUT_STATUS=$?
assert_eq "T7-7 optout write failure blocks (non-zero)" "1" "$T7_OPTOUT_STATUS"

T7_HOOKERROR_STATUS=0
( export GDD_HOOK_STATE_DIR="$READONLY_DIR/nested"
  gdd_sr_log_event "hook-error" "-" "$TMP/repo-fail" "6666666" "-" ) || T7_HOOKERROR_STATUS=$?
assert_eq "T7-8 non-optout write failure is best-effort (does not block)" "0" "$T7_HOOKERROR_STATUS"

chmod 700 "$READONLY_DIR"

COMPLETED=1
if [[ "$FAILS" -gt 0 ]]; then
  echo "$FAILS test(s) failed"
  exit 1
fi
echo "All self-review-evidence parse tests passed"

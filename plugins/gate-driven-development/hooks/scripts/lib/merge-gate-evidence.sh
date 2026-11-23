#!/usr/bin/env bash
# merge gate 専用の証跡パーサ。design.md § 証跡フィールドの書式（確定版）が正本。
# gdd_parse_self_review_field は self-review 用に必須 key が固定されているため
# 流用しない。ただし segment 抽出は self-review-evidence.sh の
# _gdd_sr_lookup / _gdd_sr_top_value（公開契約）を再利用する。
# Source this file — do not execute directly.

_GDD_MG_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
declare -F _gdd_sr_lookup >/dev/null 2>&1 ||
  source "$_GDD_MG_SCRIPT_DIR/self-review-evidence.sh"
declare -F gdd_extract_doc_field >/dev/null 2>&1 ||
  source "$_GDD_MG_SCRIPT_DIR/detect-steering.sh"

GDD_MG_VALID="false"
GDD_MG_SHA=""
GDD_MG_REASON=""
GDD_MG_AT=""
GDD_MG_AT_EPOCH=""
GDD_MG_NEW_BLOCKING=""
GDD_MG_RECEIVED=""
GDD_MG_HIGH=""
GDD_MG_MEDIUM=""
GDD_MG_APPROVAL_PR=""
GDD_MG_APPROVED_AT=""
GDD_MG_APPROVED_AT_EPOCH=""
GDD_MG_PR_OWNER=""
GDD_MG_PR_REPO=""
GDD_MG_PR_NUMBER=""
GDD_MG_BLOCKING=""
GDD_MG_DISPOSITION_COUNT=""
GDD_MG_DISPOSITION_RECORDED=""
GDD_MG_DISPOSITION_NOTE=""

# 旧書式（`blocking` key 欠落）の既定挙動を切り替えるフラグ（正本:
# references/self-review-lanes.md § 旧書式（`blocking` 欠落）の既定挙動）。
# 現状 "false" = 欠落時は GDD_MG_BLOCKING="0" とみなし legacy-no-blocking-field
# で通す。reviewer の category 出力契約の着地後に "true" へ反転すると、
# 欠落時が unparsable になる。この PR では反転しない（値の読み取り・分岐は
# T-4 が run-merge-gate-hook.sh 側で行う）。
# shellcheck disable=SC2034
GDD_MG_REQUIRE_BLOCKING_FIELD="false"

# design.md § block reason に必ず含める復旧要素の merge gate 側正本。
# key 一覧はその時点で不足している key に限定して呼び出し側が組み立てる。
# shellcheck disable=SC2034
GDD_MG_RECOVERY_CORE='書き込み先 <steering-dir>/state.md（正本: references/self-review-lanes.md）'

# `Independent Review` を要求する block reason（`independent-review-missing` /
# `-stale` / `-high`）の復旧要素 2（必要 key の全列挙）。self-review 系の
# `GDD_SR_RECOVERY_CORE` は必須 key が違う（sha,rounds,consecutive_clean,dry,lanes）ため
# 流用すると、operator は `Independent Review` 行の書式を hook ソースからしか
# 復元できない（独立レビュー R3 #7）。key 一覧は下の `Independent Review` パーサが
# 実際に必須とする集合と一致していなければならず、
# tests/test_independent_review_recovery_contract.py が key を 1 つずつ落として
# 突き合わせる（手書き literal のドリフトを機械検出する）。
# shellcheck disable=SC2034
GDD_IR_RECOVERY_CORE='書き込み先 <steering-dir>/state.md、必要な key は sha,reviewer,context,high,medium,blocking,at（context は diff-only 固定。正本: references/independent-review.md）'

# gate 側の故障（design.md § reason code カタログ code 14 / 17 / 18 / 19 = 出す key
# が無い 4 code）専用の出口。design.md § block reason の復旧要素:「kill-switch の
# 明示は code 14 以降に限る。これらは policy 違反ではなく gate 側の故障であり、
# 出口を示さないと人間は hook 本体を編集する」。policy 違反（code 1〜13）には
# 付けない（kill-switch を使わずに解ける 1 アクションを持つため）。
# パスは lib/kill-switch.sh の gdd_kill_switch_active が実際に見るファイルと
# 一致していなければならない（契約テストが両者を突き合わせる）。
# shellcheck disable=SC2034
GDD_MG_KILL_SWITCH_HINT='gate 自体の故障で作業が進まない場合は ~/.claude/gdd-hooks-disabled を作成して hook を一時停止できます（hook 本体は編集しないでください）'

_gdd_mg_is_hex_sha() {
  case "${1:-}" in
    '' | *[!0-9a-fA-F]*) return 1 ;;
  esac
  [[ "${#1}" -ge 7 && "${#1}" -le 40 ]]
}

_gdd_mg_is_uint() {
  case "${1:-}" in
    0) return 0 ;;
    '' | *[!0-9]* | 0*) return 1 ;;
  esac
  return 0
}

# ISO 8601 を UTC epoch 秒へ正規化する。Z / +HH:MM オフセットのみ受理し
# naive（オフセットなし）は失敗させる（design.md § 証跡フィールドの書式）。
# 既存 detect-steering.sh の gdd_iso_to_epoch は naive をローカル時刻として
# **受理する**ため merge gate には流用しない（時刻を後ろ倒しして待機を即解除する
# 経路を塞げなくなる）。名前が近いのは意図的な独立実装。
_gdd_mg_iso_to_epoch() {
  local _iso="${1:-}"
  [[ -n "$_iso" ]] || return 1
  case "$_iso" in
    *Z | *+[0-9][0-9]:[0-9][0-9] | *-[0-9][0-9]:[0-9][0-9]) ;;
    *) return 1 ;;
  esac
  python3 -c '
import sys, datetime
v = sys.argv[1]
if v.endswith("Z"):
    v = v[:-1] + "+00:00"
try:
    dt = datetime.datetime.fromisoformat(v)
    if dt.tzinfo is None:
        raise ValueError
    print(int(dt.astimezone(datetime.timezone.utc).timestamp()))
except ValueError:
    sys.exit(1)
' "$_iso" 2>/dev/null
}

# 鮮度判定 helper。design.md § 既定値の正本・§ 承認判定の設計 条件C が正本。
# <iso8601> からの経過が <limit_minutes> 以内かを判定する。境界は「等しい場合は
# 鮮度内」（40 分ちょうど・120 分ちょうどが解除側という design の境界規律と揃える）。
# 経過が負（未来日付）や iso8601 が不正な場合は鮮度内としない。T-12/T-13 が
# Pre-Merge Review Recheck / Last Review Push At / Merge Approval の鮮度判定に使う。
gdd_mg_within_minutes() {
  local _epoch
  _epoch="$(_gdd_mg_iso_to_epoch "${1:-}")" || return 1
  gdd_mg_epoch_within_minutes "$_epoch" "${2:-}"
}

# gdd_mg_within_minutes の、変換済みの epoch を受ける形（parser の GDD_MG_*_EPOCH を使い回す）。
gdd_mg_epoch_within_minutes() {
  local _epoch="${1:-}" _limit_minutes="${2:-}"
  local _now _elapsed
  [[ "$_epoch" =~ ^-?[0-9]+$ ]] || return 1
  [[ "$_limit_minutes" =~ ^[0-9]+$ ]] || return 1
  _now="$(date -u +%s)"
  _elapsed=$(( _now - _epoch ))
  [[ "$_elapsed" -ge 0 ]] || return 1
  [[ "$_elapsed" -le $(( _limit_minutes * 60 )) ]]
}

# 必須 key の値を `_GDD_MG_VALUE` に取り出す。値が空（= key 欠落 or 空値。design.md
# § 証跡フィールドの書式「欠落と空文字を同一扱い」）なら 1 を返し、呼び出し側が
# `unparsable` を立てる。非空だが値ドメイン違反の場合は呼び出し側が `malformed`。
# この 2 者を分けないと design code 15 `evidence-unparsable`（不足 key 名を出す）が
# 到達不能になり、code 16（値ドメインを確認する）に化ける。
_gdd_mg_required() {
  _GDD_MG_VALUE="$(_gdd_sr_top_value "${1:-}" "${2:-}")"
  [[ -n "$_GDD_MG_VALUE" ]]
}

# `<field>` の値ドメインを検査する。field ごとに要求する key 集合が違うため
# gdd_parse_self_review_field のような固定 key ループにはしない。
#
# GDD_MG_REASON の generic 語彙は `missing`（field 不在）/ `unparsable`（必須 key 欠落）/
# `malformed`（値ドメイン違反）の 3 値（tasklist T-3 Stage Output Contract）。
# T-12/T-13 が field ごとの最終 reason code へ `case` でマップする。唯一の例外は
# `state-unreadable`（design code 14）で、これは field 層の外側 = state.md 自体が
# 読めない gate 側故障のため generic 3 値に還元できない。
gdd_parse_merge_gate_field() {
  local _file="${1:-}" _field="${2:-}" _head_committer_date="${3:-}"
  # 姉妹関数 gdd_parse_self_review_field と同じく、出力グローバルは全て先頭でリセットする
  # （`at` は 4 field で共有されるため、field をまたぐ連続呼び出しで前値が残る）。
  GDD_MG_VALID="false"
  GDD_MG_SHA=""
  GDD_MG_REASON=""
  GDD_MG_AT=""
  # 検証のときに変換した epoch。呼び出し側は時刻を変換し直さず、これを使う。
  GDD_MG_AT_EPOCH=""
  GDD_MG_NEW_BLOCKING=""
  GDD_MG_RECEIVED=""
  GDD_MG_HIGH=""
  GDD_MG_MEDIUM=""
  GDD_MG_APPROVAL_PR=""
  GDD_MG_APPROVED_AT=""
  GDD_MG_APPROVED_AT_EPOCH=""
  GDD_MG_PR_OWNER=""
  GDD_MG_PR_REPO=""
  GDD_MG_PR_NUMBER=""
  GDD_MG_BLOCKING=""
  GDD_MG_DISPOSITION_COUNT=""
  GDD_MG_DISPOSITION_RECORDED=""
  GDD_MG_DISPOSITION_NOTE=""

  [[ -n "$_file" && -f "$_file" && -r "$_file" ]] || {
    GDD_MG_REASON="state-unreadable"
    return 0
  }

  local _line
  _line="$(gdd_extract_doc_field "$_file" "$_field")"
  _line="${_line%%$'\n'*}"
  _gdd_sr_trim "$_line"
  _line="$_GDD_SR_TRIMMED"
  [[ -n "$_line" ]] || {
    GDD_MG_REASON="missing"
    return 0
  }

  local _sha _at _at_epoch
  _sha="${_line%%|*}"
  _gdd_sr_trim "$_sha"
  _sha="$_GDD_SR_TRIMMED"
  if [[ "$_field" == "PR URL" ]]; then
    # PR URL は sha を持たない完全一致 field。glob だと `*` が `/` と空白にも一致し
    # `.../pull/42/files` や owner の空白を通すため、アンカー付き正規表現で判定する
    # （design.md § 値ドメイン。lib/constants.py の `PR_URL_RE` は無アンカーで
    #   `/pull/0` や末尾余剰も受理するため、ここが要求する厳格形とは別物。lib/gh_command_parse.py の
    #   `PR_URL_PATH_RE` は gh が読む形〔番号の後の続きを読まない前方一致〕で、これとも別物）。
    # owner/repo/number を分解して返し、T-12 の文字列切り出しを不要にする。
    if [[ "$_line" =~ ^https://github\.com/([^/[:space:]]+)/([^/[:space:]]+)/pull/([1-9][0-9]*)$ ]]; then
      GDD_MG_PR_OWNER="${BASH_REMATCH[1]}"
      GDD_MG_PR_REPO="${BASH_REMATCH[2]}"
      GDD_MG_PR_NUMBER="${BASH_REMATCH[3]}"
      GDD_MG_VALID="true"
    else
      GDD_MG_REASON="malformed"
    fi
    return 0
  fi
  if [[ "$_field" == "Merge Approval" ]]; then
    # 他 4 種と書式が違う（先頭 segment が `PR #<n> / head <sha>`、時刻 key が
    # at ではなく approved_at）。design.md § 証跡フィールドの書式（確定版）。
    local _pr _approved_at _approved_epoch _now_epoch
    if [[ "$_sha" =~ ^PR\ \#([1-9][0-9]*)\ /\ head\ ([0-9a-fA-F]{7,40})$ ]]; then
      _pr="${BASH_REMATCH[1]}"
      GDD_MG_SHA="${BASH_REMATCH[2]}"
    else
      GDD_MG_REASON="malformed"
      return 0
    fi
    # evidence: 必須 key。空・key 欠落は unparsable（design.md § 条件A）。
    _gdd_mg_required "$_line" "evidence" || {
      GDD_MG_REASON="unparsable"
      return 0
    }
    _gdd_mg_required "$_line" "approved_at" || {
      GDD_MG_REASON="unparsable"
      return 0
    }
    _approved_at="$_GDD_MG_VALUE"
    _approved_epoch="$(_gdd_mg_iso_to_epoch "$_approved_at")" || {
      GDD_MG_REASON="malformed"
      return 0
    }
    _now_epoch="$(date -u +%s)"
    if [[ "$_approved_epoch" -gt "$_now_epoch" ]]; then
      # 未来日付（経過が負）は invalid（design.md § 条件C）。
      GDD_MG_REASON="malformed"
      return 0
    fi
    GDD_MG_APPROVAL_PR="$_pr"
    GDD_MG_APPROVED_AT="$_approved_at"
    GDD_MG_APPROVED_AT_EPOCH="$_approved_epoch"
    GDD_MG_VALID="true"
    return 0
  fi
  # 先頭 segment（sha）は key を持たない位置指定。空なら必須要素の欠落。
  [[ -n "$_sha" ]] || { GDD_MG_REASON="unparsable"; return 0; }
  _gdd_mg_is_hex_sha "$_sha" || { GDD_MG_REASON="malformed"; return 0; }
  GDD_MG_SHA="$_sha"

  _gdd_mg_required "$_line" "at" || { GDD_MG_REASON="unparsable"; return 0; }
  _at="$_GDD_MG_VALUE"
  _at_epoch="$(_gdd_mg_iso_to_epoch "$_at")" || { GDD_MG_REASON="malformed"; return 0; }

  case "$_field" in
    "Pre-Merge Review Recheck")
      _gdd_mg_required "$_line" "new_blocking" || { GDD_MG_REASON="unparsable"; return 0; }
      _gdd_mg_is_uint "$_GDD_MG_VALUE" || { GDD_MG_REASON="malformed"; return 0; }
      GDD_MG_NEW_BLOCKING="$_GDD_MG_VALUE"
      ;;
    "Bot Review Received")
      _gdd_mg_required "$_line" "received" || { GDD_MG_REASON="unparsable"; return 0; }
      case "$_GDD_MG_VALUE" in
        yes | no) GDD_MG_RECEIVED="$_GDD_MG_VALUE" ;;
        *) GDD_MG_REASON="malformed"; return 0 ;;
      esac
      ;;
    "Independent Review")
      # reviewer / context は「実装文脈から切り離した独立レビュー」であることの
      # 標識。これを検査しないと self-review 由来の証跡が AC-3 の待機解除を通る。
      local _high
      _gdd_mg_required "$_line" "reviewer" || { GDD_MG_REASON="unparsable"; return 0; }
      case "$_GDD_MG_VALUE" in
        *[[:space:]]*) GDD_MG_REASON="malformed"; return 0 ;;
      esac
      _gdd_mg_required "$_line" "context" || { GDD_MG_REASON="unparsable"; return 0; }
      [[ "$_GDD_MG_VALUE" == "diff-only" ]] || { GDD_MG_REASON="malformed"; return 0; }
      _gdd_mg_required "$_line" "high" || { GDD_MG_REASON="unparsable"; return 0; }
      _gdd_mg_is_uint "$_GDD_MG_VALUE" || { GDD_MG_REASON="malformed"; return 0; }
      _high="$_GDD_MG_VALUE"
      _gdd_mg_required "$_line" "medium" || { GDD_MG_REASON="unparsable"; return 0; }
      _gdd_mg_is_uint "$_GDD_MG_VALUE" || { GDD_MG_REASON="malformed"; return 0; }
      GDD_MG_HIGH="$_high"
      GDD_MG_MEDIUM="$_GDD_MG_VALUE"
      _gdd_mg_required "$_line" "blocking" || {
        # near-miss key（Blocking / blockin / blocking2 / **blocking** / blocking (space)`:` 等）
        # を先に検査する。行内の各 `:` について、その直前にある許容文字（英数字・
        # `_`/`-`/`*`/空白）の最大連続を key 候補とし（数字・強調記法・コロン前空白を
        # 持つ key も取りこぼさない。`|` segment の先頭に限定せず、値の内側に埋まった
        # `foo: see blocking: 1` も拾う）、正規化（`_`/`-`/`*`/空白 除去 + 大小文字を
        # 区別しない比較）した各 key が `blocking` を部分文字列として含む、または
        # `blocking` の 6 文字以上の接頭辞なら malformed とする。
        #
        # 抽出・正規化とも外部コマンド（`grep` / `tr`）は使わない。ここは fail-closed
        # 判定の本体であり、通知を返せなくなる失敗モードを持つ依存を足してはならない
        # （`run-merge-gate-hook.sh` の同規律）。`set -euo pipefail` 下でも
        # `for` list の command substitution では `set -e` が発火しないため、
        # `grep` が失敗すると near-miss 検出が無音で無効化され、near-miss key が
        # `legacy-no-blocking-field` として素通りした（Round 16 SR-M1 で実測）。
        # `tr` は代入位置で hook ごと即死させ、かつ GNU coreutils で delete-set の
        # 逆順 range が reject された（H-1）。`nocasematch`（bash builtin。fork も
        # 失敗モードも無い）で大小文字を吸収し、抽出・文字除去は parameter expansion
        # で行う。save/restore は `run-merge-gate-hook.sh` の `_mg_equals_ci` と同じ形。
        local _rest _k _norm _near_miss=0 _saved_nocasematch
        _saved_nocasematch="$(shopt -p nocasematch || true)"
        shopt -s nocasematch
        # `_gdd_sr_lookup`（self-review-evidence.sh）は `gate_field_delimiter` 契約により
        # key 区切りとして `:` と `=` の両方を受理する。near-miss walk も同じ区切り集合を
        # 見なければ `Blocking= 1` のような `=` 区切りの near-miss key が無音で
        # `legacy-no-blocking-field` へ倒れる（completion-check Round 20 H-1 で実測）。
        # `=` を `:` へ正規化してから walk する（parameter expansion のみ、外部コマンド不使用）。
        _rest="${_line//=/:}"
        while [[ "$_rest" == *:* ]]; do
          _k="${_rest%%:*}"
          _rest="${_rest#*:}"
          # 直前の非許容文字までを落とし、コロン直前の許容文字の連続だけを残す
          _k="${_k##*[!A-Za-z0-9_*[:space:]-]}"
          [[ -n "$_k" ]] || continue
          _norm="${_k//[[:space:]_*-]/}"
          # 無関係な語（例: note の自由文「mentions blocking key」）が候補の
          # 先頭に来ると、末尾の無関係語（`key`）まで含めて連結した結果
          # `mentionsblockingkey` が `*blocking*`（無アンカー部分一致）に
          # 誤って一致していた（実測）。候補の**先頭**が `blocking` から
          # 始まる場合のみ near-miss とする（`blocking*`。`blocking2` /
          # `blockingcount` のような末尾追加はそのまま許容し、`block ing` /
          # `blocking count` のような分割・言い換え typo も維持する）。
          case "$_norm" in
            blocking*) _near_miss=1; break ;;
          esac
          if [[ "${#_norm}" -ge 6 && "blocking" == "${_norm}"* ]]; then
            _near_miss=1; break
          fi
        done
        eval "$_saved_nocasematch"
        if [[ "$_near_miss" -eq 1 ]]; then
          GDD_MG_REASON="malformed"; return 0
        fi
        GDD_MG_BLOCKING="0"
        GDD_MG_REASON="legacy-no-blocking-field"
      }
      if [[ -n "$_GDD_MG_VALUE" && -z "$GDD_MG_REASON" ]]; then
        _gdd_mg_is_uint "$_GDD_MG_VALUE" || { GDD_MG_REASON="malformed"; return 0; }
        GDD_MG_BLOCKING="$_GDD_MG_VALUE"
      fi
      ;;
    "Last Review Push At")
      if [[ -n "$_head_committer_date" ]]; then
        local _head_epoch
        # 呼び出し側は `set -euo pipefail` 下で本関数を素の文として呼ぶ契約のため
        # unguarded assignment にしない。変換不能（= 制約を検証できない）は黙って
        # skip せず block() で通知する側へ倒す（AC-10 fail-closed）。
        _head_epoch="$(_gdd_mg_iso_to_epoch "$_head_committer_date")" || _head_epoch=""
        if [[ -z "$_head_epoch" || "$_at_epoch" -lt "$_head_epoch" ]]; then
          GDD_MG_REASON="malformed"
          return 0
        fi
      fi
      ;;
    "Medium Disposition")
      _gdd_mg_required "$_line" "count" || { GDD_MG_REASON="unparsable"; return 0; }
      _gdd_mg_is_uint "$_GDD_MG_VALUE" || { GDD_MG_REASON="malformed"; return 0; }
      GDD_MG_DISPOSITION_COUNT="$_GDD_MG_VALUE"
      _gdd_mg_required "$_line" "recorded" || { GDD_MG_REASON="unparsable"; return 0; }
      case "$_GDD_MG_VALUE" in
        # 正本テンプレート（self-review-lanes.md）の値は `|` を内部に含むため、
        # `|` 区切りの segment 抽出後は片端しか残らないことがある（例:
        # `<follow-up PR URL / issue 参照` — 閉じ `>` を失う）。両端一致
        # `'<'*'>'` は素通りするため、片端だけでも placeholder とみなす。
        '' | '<'* | *'>') GDD_MG_REASON="malformed"; return 0 ;;
      esac
      GDD_MG_DISPOSITION_RECORDED="$_GDD_MG_VALUE"
      _gdd_mg_required "$_line" "note" || { GDD_MG_REASON="unparsable"; return 0; }
      case "$_GDD_MG_VALUE" in
        '' | '<'* | *'>') GDD_MG_REASON="malformed"; return 0 ;;
      esac
      GDD_MG_DISPOSITION_NOTE="$_GDD_MG_VALUE"
      ;;
  esac

  GDD_MG_AT="$_at"
  GDD_MG_AT_EPOCH="$_at_epoch"
  GDD_MG_VALID="true"
  return 0
}

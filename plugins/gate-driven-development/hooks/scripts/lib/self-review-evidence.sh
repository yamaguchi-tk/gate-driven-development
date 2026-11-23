#!/usr/bin/env bash
# Shared self-review evidence parsing / resolver / opt-out logging for
# run-pre-push-gate-hook.sh and run-pre-pr-gate-hook.sh.
# Source this file — do not execute directly.
#
# design.md § 証跡フィールドの書式（確定版）
#   Pre-PR Self Review: <sha> | rounds: <N> | consecutive_clean: <0|1|2> | dry: <yes|no>
#     | lanes: internal=<n>,grounding=<n|not_applicable(<reason-token>)>,adversarial=<n|not_applicable(<reason-token>)> | at: <ISO 8601>
#   Pre-Push Self Review: 同型

_GDD_SR_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=hooks/scripts/lib/detect-steering.sh
# 既に source 済みなら再 source しない。無条件に source すると detect-steering.sh の
# トップレベル初期化が走り、解決済みの GDD_STEERING_DIR / GDD_TASKLIST_CANONICAL 等を
# 空へ巻き戻す（source 順序に依存する latent bug）。
declare -F gdd_extract_doc_field >/dev/null 2>&1 ||
  source "$_GDD_SR_SCRIPT_DIR/detect-steering.sh"

GDD_SR_VALID="false"
GDD_SR_SHA=""
GDD_SR_ROUNDS=""
GDD_SR_CONSECUTIVE_CLEAN=""
GDD_SR_DRY=""
GDD_SR_LANES_INTERNAL=""
GDD_SR_LANES_GROUNDING=""
GDD_SR_LANES_ADVERSARIAL=""
GDD_SR_MISSING_KEYS=""

# 内部作業用（公開契約ではない。`set -u` 下で未定義参照にならないよう初期化する）
_GDD_SR_TRIMMED=""
_GDD_SR_REASON=""
_GDD_SR_LANES_RAW=""
_GDD_SR_AT=""

# references/self-review-lanes.md § not_applicable 理由 token 語彙 と同期する
# (T-22 で定義される固定集合をここでも独立して受理する)
GDD_SR_NOT_APPLICABLE_TOKENS="no-external-dep docs-only prompt-only test-only independent-review"
# 独立レビューへの委譲を表す理由 token。`grounding` / `adversarial` に共通の記録形で、
# `adversarial` はこの記録形だけを受理する（他の理由 token は従来どおり uint 検査に
# 落ちて `lanes.adversarial` を報告する）。
GDD_SR_DELEGATION_TOKEN="independent-review"
GDD_SR_ADVERSARIAL_NOT_APPLICABLE="not_applicable(${GDD_SR_DELEGATION_TOKEN})"

# 委譲記録形を受理する Task Size（独立レビューを要求する gate がある size のみ）。
# `quick (standard)` / `quick (express)` は独立レビューが免除されるため、委譲先が
# 存在しないのに「回していないレーン」を非 0 件扱いで記録できてしまう（R3 #10）。
# **`grounding` / `adversarial` の両レーンに同じ集合を適用する**（R4 #3: 片側だけ
# size 依存にすると、同じ委譲記録形が lane によって受理面が変わる非対称になる）。
# 呼び出し元が Task Size を渡さない場合は従来どおり受理する（後方互換の既定）。
GDD_SR_DELEGATION_SIZES="standard"
_GDD_SR_TASK_SIZE=""

# 委譲記録形を現在の Task Size で受理してよいかを判定する（受理なら 0）。
# lane ごとに case を書き分けると受理集合が二重化するため、判定はここ 1 本に置く。
_gdd_sr_delegation_size_ok() {
  [[ -n "$_GDD_SR_TASK_SIZE" ]] || return 0
  case " $GDD_SR_DELEGATION_SIZES " in
    *" $_GDD_SR_TASK_SIZE "*) return 0 ;;
    *) return 1 ;;
  esac
}

# ---- 必須 key 集合の正本（design.md § 証跡フィールドの書式）------------------
# 「どの key を検査するか」はこの 2 定数だけを正本とし、検査は下の 1 本のループで
# 全 key を同じ規律（存在 + 値ドメイン assert）にかける。key の追加・削除はここだけを
# 変える。key ごとの個別 if を増やすと、増やし忘れた key が黙って無検査になる。
GDD_SR_REQUIRED_TOP_KEYS="sha rounds consecutive_clean dry lanes at"
GDD_SR_REQUIRED_LANE_KEYS="internal grounding adversarial"

# ---- block reason の復旧要素の正本（design.md § block reason に必ず含める 3 要素）----
# 要素 1（記録先）・要素 2（必要 key の全列挙 + 正本パス）は pre-push / pre-PR の
# **両 hook** が同一文言で出す。hook ごとに手書きすると片方だけ欠落しても機械検査に
# 掛からない（T-14 M-1 = 1 本だけ suffix 未共有 / T-15 M-1 = pre-PR 側 2 code が
# 3 要素を持たないまま通過、と 2 回続けて同型で再発した）。ここを唯一の正本にし、
# hook 側は要素 3（逃げ道）の差分だけを足す。
#
# key 一覧を `GDD_SR_REQUIRED_TOP_KEYS` から機械導出しないのは、同定数が内部検査用に
# `at` を含む一方、reason に載せてよい token は design.md § block reason の許可トークン
# 集合 3 の 5 個に限られるため（導出すると allow-list 外の token が reason へ漏れる）。
# shellcheck disable=SC2034  # source した hook 側（pre-push / pre-PR）が参照する公開定数
GDD_SR_RECOVERY_CORE='書き込み先 <steering-dir>/state.md、必要な key は sha,rounds,consecutive_clean,dry,lanes（正本: references/self-review-lanes.md）'

# 前後の空白を落として `_GDD_SR_TRIMMED` に置く。
# 戻り値ではなく変数で返すのは、hot path での subshell fork を避けるため。
_gdd_sr_trim() {
  local _s="${1:-}"
  _s="${_s#"${_s%%[![:space:]]*}"}"
  _GDD_SR_TRIMMED="${_s%"${_s##*[![:space:]]}"}"
}

# `<text>` を `<sep>` で区切り、`<key>[:=]<value>` に一致する **最初の 1 segment** の
# value を返す。区切りは `:` / `=` の両方を受理する（gate_field_delimiter 契約）。
#
# 行全体に対する `grep -o` は同じ key が 2 回現れると全マッチを改行区切りで返し、
# 多行値が `[[ ]]` の算術・文字列比較を壊して検証を迂回させた（H-1）。segment 単位の
# 厳密パースにすることで、返る値は常に単一 segment = 単一行になる。
# 公開契約: hooks/scripts/lib/merge-gate-evidence.sh もこの関数を呼ぶ。
# 挙動を変えずに rename せず、ここでシグネチャを固定する。
_gdd_sr_lookup() {
  local _text="${1:-}" _sep="${2:-}" _key="${3:-}"
  local _seg _val
  while [[ -n "$_text" ]]; do
    if [[ "$_text" == *"$_sep"* ]]; then
      _seg="${_text%%"$_sep"*}"
      _text="${_text#*"$_sep"}"
    else
      _seg="$_text"
      _text=""
    fi
    _gdd_sr_trim "$_seg"
    _seg="$_GDD_SR_TRIMMED"
    case "$_seg" in
      "$_key":* | "$_key"=*) ;;
      *) continue ;;
    esac
    _val="${_seg#"$_key"}"
    _val="${_val#[:=]}"
    _gdd_sr_trim "$_val"
    printf '%s' "$_GDD_SR_TRIMMED"
    return 0
  done
  return 0
}

# top-level key の値。`sha` だけは key を持たない位置指定（最初の `|` segment）。
# 先頭 segment は sha 専用なので keyed lookup の対象から外す。外さないと
# `<field>: dry:no-abc1234 | ... | dry: yes` のように sha へ key 文字列を混ぜて
# 後段の key を先取りできる（H-1 と同じ「値の混線で検証を迂回する」クラス）。
# 公開契約: hooks/scripts/lib/merge-gate-evidence.sh もこの関数を呼ぶ。
# 挙動を変えずに rename せず、ここでシグネチャを固定する。
_gdd_sr_top_value() {
  local _line="${1:-}" _key="${2:-}" _keyed=""
  if [[ "$_key" == "sha" ]]; then
    _gdd_sr_trim "${_line%%|*}"
    printf '%s' "$_GDD_SR_TRIMMED"
    return 0
  fi
  if [[ "$_line" == *"|"* ]]; then
    _keyed="${_line#*|}"
  fi
  _gdd_sr_lookup "$_keyed" "|" "$_key"
}

# 正準 10 進の非負整数だけを受理する（先行ゼロは不可）。
# `00` を許すと「値としては 0 なのに `0` との文字列照合を擦り抜ける」形が作れる。
_gdd_sr_is_uint() {
  case "${1:-}" in
    0) return 0 ;;
    '' | *[!0-9]* | 0*) return 1 ;;
  esac
  return 0
}

# 抽出値の形式 assert。OK なら 0、NG なら 1 を返し、報告用の理由コードを
# `_GDD_SR_REASON` に置く。欠落（空文字）と値ドメイン違反は同一扱い
# （design.md § 証跡フィールドの書式「欠落と空文字を同一扱い」）。
_gdd_sr_check_value() {
  local _key="${1:-}" _value="${2:-}" _reason
  _gdd_sr_report_name "$_key"
  _GDD_SR_REASON="$_GDD_SR_TRIMMED"

  # 抽出は単一行を保証しているが、多行値は制御構文を壊して検証そのものを迂回させる
  # クラスの不具合だったので、抽出側と独立にここでも落とす（H-1 の二重防御）。
  case "$_value" in
    *$'\n'*) return 1 ;;
  esac

  case "$_key" in
    sha)
      case "$_value" in
        '' | *[!0-9a-fA-F]*) return 1 ;;
      esac
      # git の short sha 〜 full sha
      [[ "${#_value}" -ge 7 && "${#_value}" -le 40 ]] || return 1
      ;;
    rounds | consecutive_clean | internal)
      # `internal` に not_applicable は許さない（design.md 同節）
      _gdd_sr_is_uint "$_value" || return 1
      ;;
    adversarial)
      # 敵対レーンの not_applicable は独立レビューへの委譲だけを受理する
      # （references/self-review-lanes.md § not_applicable 理由 token 語彙）。
      # 委譲先の独立レビューを要求する gate が無い Task Size では invalid にする。
      if [[ "$_value" == "$GDD_SR_ADVERSARIAL_NOT_APPLICABLE" ]]; then
        if ! _gdd_sr_delegation_size_ok; then
          _GDD_SR_REASON="adversarial-reason-token"
          return 1
        fi
      else
        _gdd_sr_is_uint "$_value" || return 1
      fi
      ;;
    dry)
      case "$_value" in
        yes | no) ;;
        *) return 1 ;;
      esac
      ;;
    lanes)
      [[ -n "$_value" ]] || return 1
      ;;
    at)
      # ISO 8601。空白を含む値は「timestamp の後ろに別物が続いている」形なので落とす。
      case "$_value" in
        *[[:space:]]*) return 1 ;;
        [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9]*) ;;
        *) return 1 ;;
      esac
      ;;
    grounding)
      # 接地レーン非該当時のみ not_applicable を許可。理由 token は固定語彙必須。
      case "$_value" in
        not_applicable\(*\))
          _reason="${_value#not_applicable(}"
          _reason="${_reason%)}"
          case " $GDD_SR_NOT_APPLICABLE_TOKENS " in
            *" $_reason "*) ;;
            *)
              _GDD_SR_REASON="grounding-reason-token"
              return 1
              ;;
          esac
          # 委譲記録形は adversarial と同じ受理面にする（R4 #3）。独立レビューを
          # 要求する gate が無い Task Size では委譲先が存在しない。
          if [[ "$_reason" == "$GDD_SR_DELEGATION_TOKEN" ]] && ! _gdd_sr_delegation_size_ok; then
            _GDD_SR_REASON="grounding-reason-token"
            return 1
          fi
          ;;
        not_applicable*)
          _GDD_SR_REASON="grounding-reason-token"
          return 1
          ;;
        *) _gdd_sr_is_uint "$_value" || return 1 ;;
      esac
      ;;
    *)
      # 個別の値ドメインを持たない key（＝必須 key 定数にだけ追加された key）。
      # 「存在 + 非空」は全 key 共通の最低規律として必ずかける。この catch-all が無いと
      # 定数に足しただけの key が黙って無検査で通り、定数が正本として機能しない。
      [[ -n "$_value" ]] || return 1
      ;;
  esac
  _GDD_SR_REASON=""
  return 0
}

# `GDD_SR_MISSING_KEYS` に載せる key 名（lane sub-key は `lanes.<name>`）。
# lane かどうかは `GDD_SR_REQUIRED_LANE_KEYS` を引いて決める。key 名を直接列挙すると
# 定数に足した lane key が prefix なしで報告され、ここでも正本が二重化する。
_gdd_sr_report_name() {
  local _name="${1:-}"
  case " $GDD_SR_REQUIRED_LANE_KEYS " in
    *" $_name "*) _GDD_SR_TRIMMED="lanes.$_name" ;;
    *) _GDD_SR_TRIMMED="$_name" ;;
  esac
}

# 抽出値を契約グローバルへ格納する。`lanes` / `at` は公開契約に含まれないため私有変数。
_gdd_sr_store() {
  case "${1:-}" in
    sha) GDD_SR_SHA="${2:-}" ;;
    rounds) GDD_SR_ROUNDS="${2:-}" ;;
    consecutive_clean) GDD_SR_CONSECUTIVE_CLEAN="${2:-}" ;;
    dry) GDD_SR_DRY="${2:-}" ;;
    lanes) _GDD_SR_LANES_RAW="${2:-}" ;;
    at) _GDD_SR_AT="${2:-}" ;;
    internal) GDD_SR_LANES_INTERNAL="${2:-}" ;;
    grounding) GDD_SR_LANES_GROUNDING="${2:-}" ;;
    adversarial) GDD_SR_LANES_ADVERSARIAL="${2:-}" ;;
  esac
}

gdd_parse_self_review_field() {
  local _file="${1:-}"
  local _field="${2:-}"
  # 第 3 引数は正規化済み Task Size（任意）。委譲記録形の受理面判定にだけ使う。
  _GDD_SR_TASK_SIZE="${3:-}"
  GDD_SR_VALID="false"
  GDD_SR_SHA=""
  GDD_SR_ROUNDS=""
  GDD_SR_CONSECUTIVE_CLEAN=""
  GDD_SR_DRY=""
  GDD_SR_LANES_INTERNAL=""
  GDD_SR_LANES_GROUNDING=""
  GDD_SR_LANES_ADVERSARIAL=""
  GDD_SR_MISSING_KEYS=""
  _GDD_SR_LANES_RAW=""
  _GDD_SR_AT=""

  # NOTE: 呼び出し元は `set -euo pipefail` 下で本関数を素の文として呼ぶ（if/&&/|| で
  # 包まない）契約のため、無効判定はすべて `return 0` とし GDD_SR_VALID="false" のみで
  # 通知する。ここで非 0 を返すと set -e により呼び出し元スクリプトごと即座に終了する。
  # 引数欠落も同じ理由で `${1:-}` で受けてから invalid にする（set -u で落とさない）。
  [[ -n "$_file" && -n "$_field" ]] || {
    GDD_SR_MISSING_KEYS="args"
    return 0
  }
  [[ -f "$_file" ]] || {
    GDD_SR_MISSING_KEYS="file"
    return 0
  }
  [[ -r "$_file" ]] || {
    GDD_SR_MISSING_KEYS="file-unreadable"
    return 0
  }

  local _line
  _line="$(gdd_extract_doc_field "$_file" "$_field")"
  _line="${_line%%$'\n'*}"
  [[ -n "$_line" ]] || {
    GDD_SR_MISSING_KEYS="$_field"
    return 0
  }

  local _missing="" _key _value
  # shellcheck disable=SC2086  # 必須 key 集合は空白区切りの固定文字列（意図的な word split）
  for _key in $GDD_SR_REQUIRED_TOP_KEYS; do
    _value="$(_gdd_sr_top_value "$_line" "$_key")"
    _gdd_sr_store "$_key" "$_value"
    _gdd_sr_check_value "$_key" "$_value" || _missing="$_missing,$_GDD_SR_REASON"
  done

  # lanes 本体が取れているときだけ sub-key を同じ規律で検査する
  # （lanes ごと欠落しているときに sub-key 3 件を重ねて報告しない）。
  if [[ -n "$_GDD_SR_LANES_RAW" ]]; then
    # shellcheck disable=SC2086  # 同上
    for _key in $GDD_SR_REQUIRED_LANE_KEYS; do
      _value="$(_gdd_sr_lookup "$_GDD_SR_LANES_RAW" "," "$_key")"
      _gdd_sr_store "$_key" "$_value"
      _gdd_sr_check_value "$_key" "$_value" || _missing="$_missing,$_GDD_SR_REASON"
    done
  fi

  if [[ -n "$_missing" ]]; then
    GDD_SR_MISSING_KEYS="${_missing#,}"
    return 0
  fi

  # dry: yes かつ consecutive_clean == 0 は自己矛盾（正本:
  # references/self-review-lanes.md § followup 周回時のレーン要求）。2026-09-06 改訂で
  # 「2 連続」要件を撤廃したため、閾値は 2 未満から 0 のみへ緩めた（1 = 内部整合レーン
  # 1 周が clean、が新しい下限）。撤廃の根拠は reviewer recall 実測 — 3 レーン自己周回は
  # 確定欠陥を 1 件も拾わず approved を出したため、周回数は検出力の代理にならない。
  # 算術評価（`-lt`）を `if` の条件位置に置くと、想定外の値のときに出る
  # `syntax error in expression` が「条件が false」と区別できず、set -e も発火せずに
  # チェックごと静かにスキップされる（H-1 の被害面）。値はここまでで正準 10 進整数だと
  # 確定しているので、算術を使わず値照合で判定する。
  if [[ "$GDD_SR_DRY" == "yes" ]]; then
    case "$GDD_SR_CONSECUTIVE_CLEAN" in
      0)
        GDD_SR_MISSING_KEYS="dry-consecutive-clean-contradiction"
        return 0
        ;;
    esac
  fi

  GDD_SR_VALID="true"
  return 0
}

# ---- AC-25: gdd_pre_push_resolve_steering（steering resolver の和集合）------
# design.md § steering resolver の設計 / ADR-2。
#
# 呼び出し規約は gdd_detect_active_steering と同じ: 呼び出し側が対象 root へ
# **非 subshell** で `cd` してから呼ぶこと（結果はグローバル変数で返るため、
# `( cd "$dir" && gdd_pre_push_resolve_steering "$dir" )` のような subshell 越しの
# 呼び出しは親プロセスへ伝播しない）。
#
# gdd_parse_self_review_field と同じ規約で **常に exit 0** を返す。成否は戻り値
# ではなく GDD_PP_STEERING_STATUS（found/none/multiple）で判定する。呼び出し元は
# `set -euo pipefail` 下で本関数を素の文として呼べる契約のため、ここで非 0 を
# 返すと set -e により呼び出し元スクリプトごと即座に終了してしまう。
GDD_PP_STEERING_DIR=""
GDD_PP_STEERING_STATUS=""
GDD_PP_STEERING_REASON=""

# パスの状態。0 = 使える、1 = 在るのに期待の種類でない・辿れない（壊れた symlink を
# 含む）、2 = 無い。種類: file（読める通常ファイル）、dir（辿れるディレクトリ）、
# listdir（一覧もできるディレクトリ）。symlink は辿って判定する。
gdd_path_kind() {
  local _p="$1" _kind="$2"
  [[ -e "$_p" || -L "$_p" ]] || return 2
  case "$_kind" in
    file) [[ -f "$_p" && -r "$_p" ]] || return 1 ;;
    dir) [[ -d "$_p" && -x "$_p" ]] || return 1 ;;
    listdir) [[ -d "$_p" && -r "$_p" && -x "$_p" ]] || return 1 ;;
    *) return 1 ;;
  esac
  return 0
}

# root の `.steering` の下に、steering の列挙（resolver・merge gate の探し直しの
# `find -mindepth 2 -maxdepth 2 -name state.md -type f`。symlink を辿らない）から落ちる
# ものがあれば 0 を返す。無い `.steering` は 1。列挙から落ちると、その steering は
# 「無い」に見えて、両 gate が検査せずに通す（#218 の H1・H2）。落ちる形:
# - `.steering` が symlink・一覧できるディレクトリでない
# - `.steering` の下の entry（ドットで始まるものを含む）が symlink
# - task dir が一覧できない
# - task dir の state.md が在るのに読めない・列挙に載らない（symlink・FIFO・ディレクトリ）
# task dir でないファイル（README など）と、state.md の無い task dir は飛ばす。
gdd_steering_unreadable() {
  local _s="$1/.steering" _listed="" _e="" _rc=0
  gdd_path_kind "$_s" listdir || _rc=$?
  if [[ "$_rc" -eq 2 ]]; then return 1; fi
  if [[ "$_rc" -ne 0 || -L "$_s" ]]; then return 0; fi
  # 一覧できない task dir があると find は 0 以外で終わる（0600 の task dir は黙って飛ばす
  # ので、下の entry ごとの判定でも見る）。
  _listed="$(find "$_s" -mindepth 2 -maxdepth 2 -name state.md -type f 2>/dev/null)" || return 0
  for _e in "$_s"/* "$_s"/.[!.]* "$_s"/..?*; do
    if [[ -L "$_e" ]]; then return 0; fi
    # 一致が 0 件の glob の文字列と、task dir でないファイルは飛ばす。
    [[ -d "$_e" ]] || continue
    gdd_path_kind "$_e" listdir || return 0
    [[ -e "$_e/state.md" || -L "$_e/state.md" ]] || continue
    if [[ ! -r "$_e/state.md" ]]; then return 0; fi
    case $'\n'"$_listed"$'\n' in
      *$'\n'"$_e/state.md"$'\n'*) ;;
      *) return 0 ;;
    esac
  done
  return 1
}

# status と reason は必ず対で通知する契約なので、片方だけ書き換える取り違えを
# 構造的に防ぐためここに集約する。
_gdd_pp_steering_result() {
  GDD_PP_STEERING_STATUS="${1:-}"
  GDD_PP_STEERING_REASON="${2:-}"
  return 0
}

gdd_pre_push_resolve_steering() {
  local _project_root="${1:-}"
  GDD_PP_STEERING_DIR=""
  GDD_PP_STEERING_STATUS=""
  GDD_PP_STEERING_REASON=""

  # project_root 自体が git repo でない場合（`.steering` の有無を見るより前に判定
  # する。`.steering` が無いだけの通常ケース = no-candidate と取り違えないため）。
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    _gdd_pp_steering_result "none" "not-a-git-repo"
    return 0
  fi

  # 1. primary: gdd_detect_active_steering（非 done 系）を先に呼ぶ。binding が終端
  # （done・cancelled・stale な brainstorming）の steering を指しても、binding の無いときと
  # 同じ規則で作業中の steering を数え直させる（数えないと、binding の無い作業中の steering
  # の push・merge を、none や終端の steering の Task Size で検査して通してしまう）。
  if gdd_detect_active_steering --recount-terminal-binding; then
    # gdd_detect_active_steering は内部で `git rev-parse --show-toplevel` を経由するため
    # （macOS では /var が /private/var のシンボリックリンクの実測どおり）、
    # GDD_STEERING_DIR は呼び出し引数 `_project_root` とは異なる実体パス表記になりうる。
    # 呼び出し元が渡した `_project_root` を基準にした表記へ揃えるため、`.steering/` 以降の
    # 相対部分だけを引き継ぐ（`.steering` を含まない形は構造的に発生しない想定だが、
    # 想定外の形はそのまま GDD_STEERING_DIR を使う fail-safe とする）。
    if [[ "$GDD_STEERING_DIR" == *"/.steering/"* ]]; then
      GDD_PP_STEERING_DIR="$_project_root/.steering/${GDD_STEERING_DIR##*/.steering/}"
    else
      GDD_PP_STEERING_DIR="$GDD_STEERING_DIR"
    fi
    GDD_PP_STEERING_STATUS="found"
    return 0
  fi
  # primary 自体が multiple を返す場合は union フォールバックを試さずそのまま伝播する
  # （done 候補が 0 件の環境では union が誤って none/no-candidate に倒れるため）。
  if [[ "$GDD_STEERING_STATUS" == "multiple" ]]; then
    _gdd_pp_steering_result "multiple" "multiple"
    return 0
  fi

  # 2. union: 上が found 以外のときだけ、Resume From==done || Next Action==done の
  # 候補を拾う。`blocked` は両経路で gate 対象に統一する（design.md 156 行目 / ADR-2）
  # — gdd_detect_active_steering の fallback 経路は blocked を除外するため、この統一は
  # ここで候補条件を拡張しない限り成立しない。
  local _candidates=()
  local _any_state_found=0
  local _state_file _resume_from _next_action
  while IFS= read -r _state_file; do
    [[ -n "$_state_file" && -f "$_state_file" ]] || continue
    _any_state_found=1
    # terminal 値の比較は先頭セグメントだけで行う（detect-steering.sh の gdd_value_head）。
    # primary（gdd_detect_active_steering）と同じ切り出しにしないと、primary が
    # terminal として外した `done | evidence: x` をここで拾えず none に倒れる。
    _resume_from="$(gdd_value_head "$(gdd_extract_doc_field "$_state_file" "Resume From")")"
    _next_action="$(gdd_value_head "$(gdd_extract_doc_field "$_state_file" "Next Action")")"
    if [[ "$_resume_from" == "done" || "$_next_action" == "done" \
      || "$_resume_from" == "blocked" || "$_next_action" == "blocked" ]]; then
      _candidates+=("$_state_file")
    fi
  done < <(find "$_project_root/.steering" -mindepth 2 -maxdepth 2 -name state.md -type f 2>/dev/null | sort -r)

  # 3. どちらの経路でも候補が 1 件のときだけ found。0 件 / 2 件以上は解決不能。
  if [[ ${#_candidates[@]} -eq 1 ]]; then
    GDD_PP_STEERING_DIR="$(cd "$(dirname "${_candidates[0]}")" && pwd)"
    GDD_PP_STEERING_STATUS="found"
    return 0
  fi
  # union の 2 件以上は終端の steering だけが並ぶ形で、primary の multiple（active が
  # 2 件）と reason を分ける（pre-push はどちらの multiple も不足として通知する）。
  if [[ ${#_candidates[@]} -gt 1 ]]; then
    _gdd_pp_steering_result "multiple" "multiple-terminal"
    return 0
  fi

  # 候補ゼロ件。state.md が 1 件も無ければ no-candidate（trivial タスクは `.steering/`
  # 自体を作らないため毎回ここに落ちる = 設計上の正常系。design.md § opt-out ログの Why）。
  # state.md はあるが全て cancelled 等の terminal で done/blocked に該当しないなら
  # terminal-only として区別する（reason 列挙の未検証メンバー。design.md の個別発火条件は
  # 明記が無いためこの解釈は推論 — tasklist.md T-6 § Carry Forward 参照）。
  if [[ "$_any_state_found" == "1" ]]; then
    _gdd_pp_steering_result "none" "terminal-only"
  else
    _gdd_pp_steering_result "none" "no-candidate"
  fi
  return 0
}

# ---- AC-4 / AC-19: opt-out / 可観測化ログ書き込み --------------------------
# design.md § opt-out / 可観測化ログ（確定版）。
#
# 呼び出し規約: gdd_parse_self_review_field / gdd_pre_push_resolve_steering とは
# 異なり、本関数の戻り値そのものが呼び出し側への通知チャネルである
# （design.md Stage Output Contract「戻り値 0 = 書き込み成功、1 = 失敗
# （呼び出し側が opt-out の block/allow を決める）」）。したがって「常に return 0」
# 規約はここには適用しない — design.md 189 行目が定める非対称
# （optout の記録失敗のみ block=1、それ以外の event は best-effort=0）を戻り値で
# 表現するのが本関数の契約そのもの。
#
# repo は非可逆 ID（絶対パス全体の sha1 先頭 8 桁）にする。絶対パス・repo 名・
# worktree slug は残さない（design.md 186 行目、AC-18 の秘匿方針との整合）。
# basename だけをハッシュする、またはハッシュせず先頭 8 文字を生値のまま使う実装は
# T7-5 の RED で判別済み（basename 衝突・非可逆性の弱化を検出する）。
#
# `set -euo pipefail` 下で `[[ cond ]] && return N` を独立文として `||` ブロック内に
# 置くと、条件が false のときその文自体の終了ステータス（非 0）で set -e が発火し、
# 後続の `return 0` に到達せず意図せぬステータスで関数が抜ける（本 codebase の H-1 系
# 「算術評価を if の条件位置に置くと構文エラーが握り潰される」と同型の落とし穴）。
# そのため以下は必ず `if [[ cond ]]; then return N; fi` の明示形にする。
gdd_sr_log_event() {
  local _event="${1:-}" _reason="${2:-}" _repo_root="${3:-}" _head_sha="${4:-}" _via="${5:-}"
  # 記録先が決まらない場合は空のままにし、後段の書き込み条件で「書き込み失敗」に合流させる。
  # `${HOME}` を直接展開すると set -u 下でシェルごと即死し、呼び出し側の fail-closed 判定
  # （run-pre-push-gate-hook.sh の optout 分岐）に到達できない。安全形は lib/kill-switch.sh:5 に揃える。
  local _state_dir="${GDD_HOOK_STATE_DIR:-}"
  if [[ -z "$_state_dir" && -n "${HOME:-}" ]]; then
    _state_dir="${HOME}/.claude/.gdd-hook-state"
  fi
  local _logfile="$_state_dir/pre-push-optout.log"
  local _repo_id _ts

  if command -v shasum >/dev/null 2>&1; then
    _repo_id="$(printf '%s' "$_repo_root" | shasum -a 1 | cut -c1-8)"
  else
    _repo_id="$(printf '%s' "$_repo_root" | sha1sum | cut -c1-8)"
  fi
  _ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  if [[ -n "$_state_dir" ]] && mkdir -p "$_state_dir" 2>/dev/null &&
    { printf '%s | event: %s | reason: %s | repo: %s | head: %s | via: %s\n' \
      "$_ts" "$_event" "$_reason" "$_repo_id" "$_head_sha" "$_via" \
      >>"$_logfile"; } 2>/dev/null; then
    chmod 600 "$_logfile" 2>/dev/null || true
    return 0
  fi

  # 書き込み失敗時の非対称: optout のみ block(1)、それ以外の event は best-effort(0)。
  if [[ "$_event" == "optout" ]]; then
    return 1
  fi
  return 0
}

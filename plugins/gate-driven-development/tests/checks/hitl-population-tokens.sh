#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}"

echo "BLOCK: hitl-population-tokens"

# 「根拠の母集団」必須化の契約トークン検証。
# 発火点は template のテキストではなく lint-hitl-decision-quality.py の条件付き判定
# （HITL 出力そのものを CI で検査する）。判定行と marker 値を逐語 pin する。
# 無改変検証: 既存の REQUIRED_DECISION_MARKERS 10 件が残っていること。

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

# --- 発火点（最重要）: linter の条件付き判定と marker 値 ---
req "scripts/lint-hitl-decision-quality.py" "EVIDENCE_CLAIM_PHRASES"
req "scripts/lint-hitl-decision-quality.py" "EVIDENCE_POPULATION_MARKER"
req "scripts/lint-hitl-decision-quality.py" 'EVIDENCE_POPULATION_MARKER = "根拠の母集団"'
req "scripts/lint-hitl-decision-quality.py" \
  "if any(phrase in text for phrase in EVIDENCE_CLAIM_PHRASES) and EVIDENCE_POPULATION_MARKER not in text:"
# 発火語（最小 3 語。実データで広げる運用）
req "scripts/lint-hitl-decision-quality.py" '"件の実測"'
req "scripts/lint-hitl-decision-quality.py" '"実測"'
req "scripts/lint-hitl-decision-quality.py" '"件中"'

# --- fixture が発火点を実際に踏むこと ---
req "tests/checks/hitl-decision-quality-lint.sh" "根拠の母集団"
req "tests/checks/hitl-decision-quality-lint.sh" "TMP_HITL_POPULATION_BAD"

# --- 一次表示への搭載（Template と Required Words の両方を別トークンで pin） ---
# Template 側（一次表示に実際に出る行）
req "references/human-check-template-compact.md" "根拠の母集団: <"
# Required Words 側（必須欄の列挙 = 発火点。ここに載らないと圧縮時に落ちる）
req "references/human-check-template-compact.md" "- 実測・件数を根拠に出す場合は根拠の母集団"

# --- 計画側テンプレート ---
req "references/requirements-template.md" "根拠の母集団"

# --- 上位正本: 母集団の仕様と既存 2 欄の記入規則強化 ---
req "references/human-check-template.md" "根拠の母集団"
req "references/human-check-template.md" "権限の話ではなく scope の話"
req "references/human-check-template.md" "当初目的のどこを取りに行かないか"

# --- 無改変検証: 既存 REQUIRED_DECISION_MARKERS 10 件 ---
for marker in \
  "整理した要件" \
  "実装する方法・内容" \
  "検証する方法・内容" \
  "どこまで自走するのか" \
  "判断ポイント" \
  "段階実装サマリー" \
  "OKで進む範囲" \
  "OKでも許可されないこと" \
  "人間が今やること" \
  "OK 後に残る作業"; do
  req "scripts/lint-hitl-decision-quality.py" "$marker"
done

if (( fail != 0 )); then
  echo "FAIL: hitl-population-tokens"
  exit 1
fi

echo "hitl-population-tokens: OK (evidence population marker enforced in linter and templates)"
echo "VERDICT: hitl-population-tokens: OK"

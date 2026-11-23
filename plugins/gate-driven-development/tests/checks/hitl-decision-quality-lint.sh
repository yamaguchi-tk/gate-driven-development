#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: hitl-decision-quality-lint"
TMP_HITL_DECISION_OK=$(mktemp -t hitl-decision-ok.XXXXXX.md)
# assertion 失敗時（set -e で即終了する）にも temp を残さない。
# 後段で作る temp も含めて最初の mktemp 直後に登録する（未定義の間は空に展開される）。
trap 'rm -f "${TMP_HITL_DECISION_OK:-}" "${TMP_HITL_DECISION_BAD:-}" "${TMP_HITL_POPULATION_BAD:-}"' EXIT
TMP_HITL_DECISION_BAD=$(mktemp -t hitl-decision-bad.XXXXXX.md)
TMP_HITL_POPULATION_BAD=$(mktemp -t hitl-population-bad.XXXXXX.md)
cat > "$TMP_HITL_DECISION_OK" <<'HITL_DECISION_OK_EOF'
## 🔍 確認
### 30秒判断
どこまで自走するのか？
**整理した要件**: 既存コード読解を先に行い、完了条件に沿ってテストを書きます。
**実装する方法・内容**: 既存の HITL contract と lint を更新します。
**検証する方法・内容**: lint smoke と contract test で確認します。
**どこまで自走するのか**: PR 作成まで。merge と deploy は別承認です。
**判断ポイント**: 完了条件と検証範囲が意図通りか。
**段階実装サマリー**: 単一段階: 今回の PR で完結。
**根拠の母集団**: 直近 3 PR の実測 6 件。いずれも docs のみの PR で、コードを含む PR は未測。

### OKで進む範囲
既存コード読解を先に行い、HITLで見えた完了条件に沿ってテストを書きます。

### OKでも許可されないこと
本番反映、外部投稿、追加の仕様変更は承認しません。

### 現在地
| 項目 | 内容 |
|---|---|
| 人間が今やること | 上の2点が意図どおりか確認して OK と返す |
| OK 後に残る作業 | 設計、テスト、実装、PRレビュー後ループ |

### PR検証後の次の導線
| PR検証後の状態 | 次にやること | 同じチャットで続けるか / 新しいチャットか |
|---|---|---|
| PR の検証・レビューが通った | merge は人間判断。後続実装があるなら次の GDD タスクにする | 新しいチャット推奨: 別 scope になるため |
| レビュー指摘や CI 失敗が出た | PRレビュー後ループで修正して再レビュー依頼する | 同じチャット推奨: PR URL と指摘が同じ文脈にあるため |

### やらないこと
本番デプロイはしません。

### 人間に戻す条件
完了条件、技術スタック、外部公開範囲が変わる場合。
HITL_DECISION_OK_EOF
cat > "$TMP_HITL_DECISION_BAD" <<'HITL_DECISION_BAD_EOF'
次に必要な判断はどちらかです。

既存 holdout 2件を human-confirm して executable にする
active/new PR を 2件指定して holdout no-post 対象にする
prod_equivalent まで release gate にするなら、production model env の設定も必要です。
HITL_DECISION_BAD_EOF
# 件数・実測を根拠に出しているのに「根拠の母集団」が無い HITL は reject されること。
# OK fixture から母集団の 1 行だけを落として作る（他の必須欄は満たしたまま）。
grep -v '^\*\*根拠の母集団\*\*' "$TMP_HITL_DECISION_OK" > "$TMP_HITL_POPULATION_BAD"
printf '\n直近 3 PR の実測 6 件を根拠にしています。\n' >> "$TMP_HITL_POPULATION_BAD"

"$PYTHON_BIN" "$ROOT/scripts/lint-hitl-decision-quality.py" "$TMP_HITL_DECISION_OK" --quiet
if "$PYTHON_BIN" "$ROOT/scripts/lint-hitl-decision-quality.py" "$TMP_HITL_DECISION_BAD" --quiet >/dev/null 2>&1; then
  echo "FAIL: lint-hitl-decision-quality.py should reject undecidable HITL"
  exit 1
fi
if "$PYTHON_BIN" "$ROOT/scripts/lint-hitl-decision-quality.py" "$TMP_HITL_POPULATION_BAD" --quiet >/dev/null 2>&1; then
  echo "FAIL: lint-hitl-decision-quality.py should reject cited counts without 根拠の母集団"
  exit 1
fi
# 後片付けは EXIT trap が行う

echo "VERDICT: hitl-decision-quality-lint: OK"

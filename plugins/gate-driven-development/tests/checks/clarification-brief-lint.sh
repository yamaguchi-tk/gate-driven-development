#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: clarification-brief-lint"
TMP_CLARIFICATION_OK=$(mktemp -t clarification-ok.XXXXXX.md)
# assertion 失敗時（set -e で即終了する）にも temp を残さない。
# 後段で作る temp も含めて最初の mktemp 直後に登録する（未定義の間は空に展開される）。
trap 'rm -f "${TMP_CLARIFICATION_OK:-}" "${TMP_CLARIFICATION_BAD:-}"' EXIT
TMP_CLARIFICATION_BAD=$(mktemp -t clarification-bad.XXXXXX.md)
cat > "$TMP_CLARIFICATION_OK" <<'CLARIFICATION_OK_EOF'
**Intake Brief**

1. 確定済み
- 目的: 調査機能全体を底上げする

2. 判断材料（今回わかっていること）
- ReAct は調査中の行動と観測を往復させるので、仮説検証ループの再現性を上げる候補です。
- Reflexion は失敗から次回方針を更新するので、wiki への履歴化と改善学習に向いています。
- Tree of Thoughts は複数仮説を並べて比較するので、調査漏れ削減をテストしやすいです。

3. まだ曖昧
- 最初に改善する範囲

4. 次に決めること
A. workflow 全体の改善ロードマップ
B. AWS 障害調査に絞る
この回答は requirements.md の scope / AC / Deferred に反映します。

5. 回答後にどう進むか
回答後、requirements.md と design.md を作り、human-check へ進みます。

<gdd-stop reason="clarification-needed">
CLARIFICATION_OK_EOF
cat > "$TMP_CLARIFICATION_BAD" <<'CLARIFICATION_BAD_EOF'
**Intake Brief**

1. 確定済み
- 目的: 調査機能全体を底上げする

2. まだ曖昧
- 調査機能全体が指す範囲

3. 次に決めること
A. workflow 全体
B. AWS 障害調査

初期確認した外部ソース候補: ReAct, Reflexion, Tree of Thoughts

<gdd-stop reason="clarification-needed">
CLARIFICATION_BAD_EOF
"$PYTHON_BIN" "$ROOT/scripts/lint-clarification-brief.py" "$TMP_CLARIFICATION_OK" --quiet
if "$PYTHON_BIN" "$ROOT/scripts/lint-clarification-brief.py" "$TMP_CLARIFICATION_BAD" --quiet >/dev/null 2>&1; then
  echo "FAIL: lint-clarification-brief.py should reject research clarification without decision material"
  exit 1
fi

echo "VERDICT: clarification-brief-lint: OK"

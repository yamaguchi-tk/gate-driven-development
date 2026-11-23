#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: hitl-display-integrity-lint"
TMP_HITL_DISPLAY_OK=$(mktemp -t hitl-display-ok.XXXXXX.md)
# assertion 失敗時（set -e で即終了する）にも temp を残さない。
# 後段で作る temp も含めて最初の mktemp 直後に登録する（未定義の間は空に展開される）。
trap 'rm -f "${TMP_HITL_DISPLAY_OK:-}" "${TMP_HITL_DISPLAY_BAD:-}"' EXIT
TMP_HITL_DISPLAY_BAD=$(mktemp -t hitl-display-bad.XXXXXX.md)
# OK fixture は手書きのため、正本テンプレートにまだ無い語（この案を選ぶと次に何が起きるか /
# 無回答時のデフォルト。owner=T-7）を先取りしても、この check だけでは乖離が見えない。
# marker と正本の乖離は
# tests/test_hitl_lint_marker_sync_contract.py::test_display_integrity_markers_exist_in_canonical_sources
# が正本ファイルそのものを読んで検査する（impl-gate #1 F-2）。
cat > "$TMP_HITL_DISPLAY_OK" <<'HITL_DISPLAY_OK_EOF'
## 確認

### なぜやるか（WHY・根本原因）
障害対応で repo 単位の索引しか無く、該当 path に辿り着けないため。

### 何を作るか（整理した要件）
AWS inventory の事前学習を path 単位へ拡張します。

### どう作るか（実装する方法・内容）
既存の source evidence chain を再利用し、path index を追加します。

**変更予定ファイル（WHERE）**: scripts/build-path-index.py / references/inventory.md

### どう確かめるか（検証する方法・内容）
unit と contract で path index の生成と参照解決を確認します。

### 現在地
完了フェーズ: 要件整理 / 今やること: OK 判断 / OK後: 設計 / 残タスク: 実装・レビュー

### どこまで自走するか（どこまで自走するのか）
- OKで進む範囲: 実装 / テスト / review / PR 作成
- OKでも許可されないこと: merge / deploy / apply / production write
- 人間に戻す条件: scope / AC / security / architecture の変更

### 判断ポイント
1. 索引の粒度 — 変更前: repo 単位 / 変更後: path 単位 / 採用しない案: 全文検索
   - この案を選ぶと次に何が起きるか: path index の生成コストが増え、後続 PR で cache が要る
   - 無回答時のデフォルト: path 単位を採用し、cache は次 PR に送る

### 段階実装（段階実装サマリー）
single-stage: 今回の PR で完結

### ズレ確認（後戻りが大きいものだけ）
完了条件の変換: source evidence が保存されることを完了条件に読み替えています。

<gdd-stop reason="human-check-waiting">
HITL_DISPLAY_OK_EOF
cat > "$TMP_HITL_DISPLAY_BAD" <<'HITL_DISPLAY_BAD_EOF'
## 🔍 確認

### やること
AWS inventory の事前学習を拡張します。

### 前提
| 項目 | 内容 |
|---|---|
| 設計方針 | AWS graph + Datadog query capability |

### 承認ポイント
**1. 採用 scope**
- **AI の仮決定**: Option B

<gdd-stop reason="human-check-waiting">
HITL_DISPLAY_BAD_EOF
"$PYTHON_BIN" "$ROOT/scripts/lint-hitl-display-integrity.py" "$TMP_HITL_DISPLAY_OK" --quiet
if "$PYTHON_BIN" "$ROOT/scripts/lint-hitl-display-integrity.py" "$TMP_HITL_DISPLAY_BAD" --quiet >/dev/null 2>&1; then
  echo "FAIL: lint-hitl-display-integrity.py should reject stripped final HITL"
  exit 1
fi

echo "VERDICT: hitl-display-integrity-lint: OK"

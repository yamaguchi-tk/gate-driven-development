#!/usr/bin/env bash
# Smoke test: 必須ファイル存在・両 manifest 整合・frontmatter・README/技能の最小契約トークンと軽量 grader 出力を検証する。
# 挙動・trigger 精度・handoff の品質保証は evals/evals.json と eval ループで行う。このスクリプトは肥大化させない。
set -euo pipefail

export ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHON_BIN=""
export NODE_BIN=""

for cmd in python3 python; do
  if command -v "$cmd" >/dev/null 2>&1; then
    PYTHON_BIN="$cmd"
    break
  fi
done

if [[ -z "$PYTHON_BIN" ]]; then
  echo "MISSING: python runtime (python3 or python)"
  exit 1
fi

if command -v node >/dev/null 2>&1; then
  NODE_BIN="node"
fi

while IFS=$'\t' read -r check_name check_blocking check_script; do
  [[ -z "$check_name" || "$check_name" =~ ^[[:space:]]*# ]] && continue
  # 独立レビュー指摘（独立-8・low）: check_name を未エスケープで後段の ERE
  # (VERDICT 行の検査) に埋め込むため、正規表現メタ文字を含む名前だと誤受理
  # の余地がある。安全な文字種だけを許可し、後段の grep -E を固定文字列
  # 相当に閉じる。
  if [[ ! "$check_name" =~ ^[A-Za-z0-9_-]+$ ]]; then
    echo "MANIFEST_ERROR: check '$check_name' has an unsafe name (must match [A-Za-z0-9_-]+)"
    exit 1
  fi
  if [[ -z "$check_script" || "$check_script" == /* || "$check_script" == *".."* ]]; then
    echo "MANIFEST_ERROR: check '$check_name' has an unsafe script path (must be plugin-relative, no '..'): '$check_script'"
    exit 1
  fi
  if [[ ! -f "$ROOT/$check_script" ]]; then
    echo "MANIFEST_ERROR: check '$check_name' has missing or invalid script path: '$check_script'"
    exit 1
  fi
  # 判定を宣言したか（VERDICT: <check_name>: OK|SKIP）を機械的に検査する番兵。
  # rc=0 の呼び出し自体を保護するのではなく、「宣言のない成功」を一律で拒否
  # する。動的ロードしたモジュールへの呼び出し中に SystemExit(0) が送出され、
  # fail() に到達せず rc=0 で静かに成功する経路（PR #93 のクラスタ指摘）を、
  # 呼び出し箇所を個別に塞ぐのではなく、この宣言必須化で構造的に閉じる。
  # 独立レビュー指摘（独立-8・medium）: check の stdin が manifest.tsv の
  # read ループのリダイレクトを継承したままだと、stdin を読む check が
  # manifest の残り行を食い、while が EOF で抜けて後続の check が一度も
  # 実行されずに rc=0 で完走する（「走らなかった check」を番兵は検出
  # できない）。</dev/null で切る。
  if check_output="$(bash "$ROOT/$check_script" </dev/null)"; then
    check_status=0
  else
    check_status=$?
  fi
  if [[ "$check_status" -ne 0 ]]; then
    printf '%s\n' "$check_output"
    exit "$check_status"
  fi
  printf '%s\n' "$check_output"
  if ! printf '%s\n' "$check_output" | grep -qE "^VERDICT: ${check_name}: (OK|SKIP)\$"; then
    echo "VERDICT_MISSING: check '$check_name' exited 0 without emitting 'VERDICT: $check_name: OK' or 'VERDICT: $check_name: SKIP'"
    exit 1
  fi
done < "$ROOT/tests/checks/manifest.tsv"

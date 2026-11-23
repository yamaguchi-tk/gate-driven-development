#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# shellcheck source=../hooks/scripts/lib/classify-intent.sh
source "$ROOT/hooks/scripts/lib/classify-intent.sh"

assert_intent() {
  local expected="$1"
  local text="$2"
  local actual
  actual="$(gdd_classify_intent "$text")"
  if [[ "$actual" != "$expected" ]]; then
    echo "expected=${expected} actual=${actual} text=${text}" >&2
    exit 1
  fi
}

assert_intent "new" "AWS調査系で、Gitコード、CI/CDの状況、社内 wiki の情報、AWSのリソース、設定を確認して、それを加味して調査できるようにする。gdd-dev側の改善が必要かも含めて判断したい"
assert_intent "new" "ユーザー一覧にページネーションを追加したい"
assert_intent "new" "https://example.com の内容を参考にログ出力を改善したい"
assert_intent "ambiguous" "https://example.com"
assert_intent "ambiguous" ""
assert_intent "resume" "前回の続きから再開して"
assert_intent "new" "別件でSlack通知を改善したい"
assert_intent "ambiguous" "新規だけど前回の続きから再開して"

echo "OK"

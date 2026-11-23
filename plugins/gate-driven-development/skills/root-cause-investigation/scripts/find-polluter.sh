#!/usr/bin/env bash
# find-polluter.sh — テスト汚染源（test pollution）の特定 helper
#
# 症状: 単体実行 (test A) では PASS、ただし suite 実行 (...test X; test A) で FAIL
# 原因候補: 共有 state / module side effect / global state / fixture が他の test に
#           汚染を残している
#
# 使い方:
#   ./find-polluter.sh <suspect-test-id> [<test-runner-command>]
#
# 引数:
#   suspect-test-id: 汚染を受けて FAIL するテスト ID（テスト ID は test runner の形式に従う）
#   test-runner-command: テストランナーの起動コマンド（既定: pytest）
#
# 環境変数:
#   POLLUTER_TEST_LIST_CMD: テスト一覧を取得するコマンド（既定: 'pytest --collect-only -q'）
#   POLLUTER_TEST_RUN_CMD:  単一テスト実行コマンド（既定: 'pytest -x'）
#   POLLUTER_TIMEOUT_SEC:   各テスト実行のタイムアウト秒数（既定: 120）
#
# アルゴリズム:
#   1. テスト一覧を取得
#   2. <suspect> を最後に置き、他のテスト 1 つを先に実行する binary search 風アプローチ
#      - 全テスト集合 S を 2 分割し、各半分 + <suspect> を実行
#      - FAIL した半分に汚染源がいる
#      - 1 件まで絞り込む
#   3. 特定した polluter を出力
#
# 制限事項:
#   - test runner が CLI 引数順に test を実行することを仮定（pytest は CLI 順、jest は
#     --runInBand + 配列順 等。並列実行 / shuffle が有効だと結果が安定しない）
#   - polluter が複数いる場合は最初の 1 件のみ検出（再実行で次を探す）
#   - timing 依存 / 並列実行依存の汚染は検出できない（serial 実行のみ対象）
#
# Exit code:
#   0: polluter を 1 件特定（POLLUTER: <id> / SUSPECT: <id> + 推奨アクションを stdout）
#   1: 引数欠落 / 前提違反（suspect が単体実行でも FAIL する場合）
#   2: 環境エラー（test 一覧取得失敗、POLLUTER_TEST_LIST_CMD が空 list を返す等）
#   3: 再現せず（汚染が複数 / timing 依存 / 並列依存 / 環境差で確定できない）

set -euo pipefail

SUSPECT="${1:-}"
if [ -z "$SUSPECT" ]; then
    echo "usage: find-polluter.sh <suspect-test-id> [<test-runner-command>]" >&2
    exit 2
fi

TEST_LIST_CMD="${POLLUTER_TEST_LIST_CMD:-pytest --collect-only -q}"
TEST_RUN_CMD="${POLLUTER_TEST_RUN_CMD:-pytest -x}"
TIMEOUT_SEC="${POLLUTER_TIMEOUT_SEC:-120}"

log() { printf '[find-polluter] %s\n' "$*" >&2; }

# テスト一覧を取得（suspect を除く）
log "テスト一覧を取得中..."
mapfile -t ALL_TESTS < <($TEST_LIST_CMD 2>/dev/null | grep -E '::|test_' | grep -v "^$SUSPECT$" || true)

if [ ${#ALL_TESTS[@]} -eq 0 ]; then
    log "テスト一覧が取得できませんでした。POLLUTER_TEST_LIST_CMD を確認してください"
    exit 2
fi

log "全 ${#ALL_TESTS[@]} 件のテストから汚染源を探索"

# 単体実行で suspect が PASS することを確認（前提検証）
log "前提検証: $SUSPECT 単体実行が PASS することを確認..."
if ! timeout "$TIMEOUT_SEC" $TEST_RUN_CMD "$SUSPECT" >/dev/null 2>&1; then
    log "前提違反: $SUSPECT は単体実行でも FAIL します。汚染ではなく単体バグの可能性"
    exit 1
fi
log "前提 OK: $SUSPECT 単体は PASS"

# binary search で汚染源を絞り込む
run_pair() {
    # $1: テスト ID
    # 戻り値: $1 → suspect の順で実行して suspect が PASS なら 0、FAIL なら 1
    local polluter_candidate="$1"
    if timeout "$TIMEOUT_SEC" $TEST_RUN_CMD "$polluter_candidate" "$SUSPECT" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

run_chunk() {
    # $@: テスト ID リスト
    # 全部 + suspect を末尾に実行。suspect が FAIL なら chunk 内に汚染源あり
    if timeout "$TIMEOUT_SEC" $TEST_RUN_CMD "$@" "$SUSPECT" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

candidates=("${ALL_TESTS[@]}")
iteration=0
while [ ${#candidates[@]} -gt 1 ]; do
    iteration=$((iteration + 1))
    half=$((${#candidates[@]} / 2))
    left=("${candidates[@]:0:half}")
    right=("${candidates[@]:half}")
    log "iter $iteration: 候補 ${#candidates[@]} を 2 分割 (left=${#left[@]} / right=${#right[@]})"

    if ! run_chunk "${left[@]}"; then
        log "  → left 半分に汚染源あり"
        candidates=("${left[@]}")
    elif ! run_chunk "${right[@]}"; then
        log "  → right 半分に汚染源あり"
        candidates=("${right[@]}")
    else
        log "両半分とも汚染源なし。timing 依存 / 並列依存 / 複数 polluter の可能性"
        log "left+right 全体で再現するか確認..."
        if ! run_chunk "${candidates[@]}"; then
            log "全体では FAIL するが 2 分割では PASS → ordering 依存または複数 polluter"
        else
            log "全体でも PASS。汚染が再現しません"
        fi
        exit 3
    fi
done

if [ ${#candidates[@]} -eq 1 ]; then
    polluter="${candidates[0]}"
    log "polluter 特定: $polluter"
    # 確認実行
    if ! run_pair "$polluter"; then
        echo "POLLUTER: $polluter"
        echo "SUSPECT: $SUSPECT"
        echo ""
        echo "推奨アクション:"
        echo "  1. $polluter のセットアップ / teardown で残している共有 state を確認"
        echo "  2. global state（process env、シングルトン、static field、module-level cache）を grep"
        echo "  3. $polluter の after hook で teardown を追加"
        echo "  4. \$ $TEST_RUN_CMD $polluter $SUSPECT で再現確認"
        exit 0
    else
        log "確認実行で再現せず。timing / 並列 / 環境依存の可能性"
        exit 3
    fi
fi

log "候補がゼロ件に絞られました。再現しません"
exit 3

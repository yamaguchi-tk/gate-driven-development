#!/usr/bin/env bash
# Notification hook: セッションが入力待ちで止まった事実を、ローカル OS 通知として
# 1 回だけ出す（AC-18）。記録も LLM への注入も行わない。
#
# payload（notification_type / message / title …）は Claude Code が生成する値だが、
# hook から見れば untrusted input。design.md § Sensitive Data / Masking Policy の
# enforcement point 2（通知コマンド呼び出し直前）と enforcement point 4
# （`terminalSequence`）を本ファイルが強制する。
#
# 設計上の不変条件:
#   - 通知本文は `notification_type` の allowlist に対する**固定文言の対応表**だけ。
#     payload の `message` / `title` は 1 バイトも読まない（enforcement point 2）
#   - allowlist 外 / 解釈不能 / 依存不在は**すべて no-op で exit 0**（AC-18）
#   - stdout は空。`Notification` は `decision` / `systemMessage` /
#     `hookSpecificOutput` を破棄するので出力契約が無く、`terminalSequence` に
#     載せてよいのは本ファイル内のリテラル定数のみ。本 hook は現状 1 バイトも
#     出さないので、payload 由来文字列が端末へ抜ける面そのものが無い
#     （enforcement point 4）
#
# **exit 0 の射程について全称は掲げない**（達成不能。AC-16 で繰り返した）。
# 射程の正本は requirements AC-16 / R1.4 と `adr.md` ADR-16。
#
# **測った環境**（**環境も入力空間の 1 軸**。T-18 Attempt 1 の MED-T18-A は、
# 測定基盤に bash のバージョン軸が無かったことから漏れた）:
#   - bash 3.2.57(1) / macOS 26.6.2 arm64（2026-08-26）
#   - bash 5.3.15(1) / Alpine musl aarch64（docker `bash:5`・2026-08-26）
#   - bash 5.2.37(1) / Debian trixie aarch64（docker `python:3.11-slim`・2026-08-26。
#     `tests/test_notification_hook_contract.py` を通した環境）
#
# 実測（**機械検証があるのは下の (i) だけ** ——
# `tests/test_notification_hook_contract.py` の
# `test_nul_in_payload_with_dead_stderr_pipe_keeps_exit_zero` が pin する。**18 形と (ii) は
# harness 実測のみで、出荷テストに pin は無い**）:
#   - 本 hook が扱うデータ I/O は **stdin からの payload の read だけ**（記録先を
#     持たない）。この read は `cat 2>/dev/null || true` が受ける
#   - **hook 本体は stdout / stderr へ 1 バイトも書かない。ただしプロセス全体では
#     fd 2 への write が皆無ではない** —— 解釈器である bash 自身が書く形が 2 つ
#     実在する。(i) bash 5 は NUL を含む payload の command substitution で警告を
#     fd 2 に書く（実測: 警告 1 行。バイト数はスクリプトの絶対パスと行番号を含む
#     ので環境依存 —— bash 5.3.15 で 104B / bash 5.2.37 で 110B。**bash 3.2.57 は
#     0B ＝ 無言で NUL を捨てる**）＝ **射程内 (S)** なので上の
#     `trap '' PIPE` で閉じた。(ii) `RLIMIT_FSIZE=0` 下では heredoc の一時ファイル
#     write が SIGXFSZ を起こし、bash が子の異常終了を fd 2 に報告する ＝ **射程外
#     の第 2 群**として未閉鎖（どちらも payload 由来のバイトは 1 つも載らないので
#     enforcement point 2 / 4 は破れていない）
#   - fd 破壊面: fd 1 / fd 2 / 両方 × 「閉じた fd」「読み手の消えた pipe」「master を
#     閉じた pty」× payload 2 種（allowlist 命中 / 非命中）の **18 形すべてで rc 0**
#     （実測 2026-08-26。**bash 3.2.57 と bash 5.2.37 の両方**で 18 形 / non-zero 0。
#     null control rc 0 / positive control rc 7 を先置き）
#
# **測っていない入力空間**: 上の 18 形は「本 hook 自身の出力 fd の破壊」だけで、
# **シグナル一般・資源制限・端末設定・記録先（本 hook は持たない）は測っていない**。
# bash も上の 3 版しか通していない（**bash 4 系は 1 形も測っていない**）。macOS 以外
# の実機・Windows/WSL も未測定（Linux は container のみ）。
# 射程外は `run-stop-failure-hook.sh` 冒頭の **5 群**と同じで、本 PR では閉じない
# （列挙はそちらだけに書き、ここには写さない）。fd 0 閉塞は本 hook でも同じく
# **HANG**（実測。`$(cat` を持つ hook 共通の pre-existing）。
set -euo pipefail

# 射程 (S) をここで閉じる。**「本 hook には SIGPIPE の発生源が無い」は偽**だった
# （T-18 Attempt 1 / MED-T18-A）: 上の (i) のとおり bash 5 は NUL を含む payload の
# command substitution で fd 2 に警告を書き、line `PAYLOAD="$(cat 2>/dev/null || true)"`
# の `2>/dev/null` は **`cat` の stderr にしか掛からない**ので受け止められない。
# fd 2 が読み手の消えた pipe だと、この write が SIGPIPE を起こして hook は
# **rc 141（128+13）で死ぬ**。引き金は運用者の異常な設定ではなく **payload に NUL が
# 1 バイトあること**で、追加の資源制限も端末設定も要らない ＝ AC-16 (S) の射程内。
# 実測 2026-08-26（null control ＝ NUL 抜きは stderr 0B / rc 0 ＝ 検出力あり）:
#   bash 5.3.15  shipped **rc 141** / `trap '' PIPE` 追加で **rc 0**
#   bash 3.2.57  どちらも rc 0（3.2 は NUL を無言で捨てるため**この軸では検出力 0**）
# **この 1 行が閉じるのは SIGPIPE 1 つだけ**。同じ class の SIGXFSZ / SIGTTOU /
# SIGTTIN は射程外の第 2 群として**未閉鎖のまま**（sibling と同じ限定）。
# 子プロセスへの継承は無害（sibling で実測済み）: python は起動時に自分で SIGPIPE を
# SIG_IGN にし、osascript / notify-send は出力を /dev/null に捨てる。
trap '' PIPE

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 既知の未閉鎖（NEW-1・本 PR では直さない）: この `source` は無防備で、`lib/` を
# 取りこぼす同期が起きると `set -e` が非 0 に倒す。`set -euo pipefail` を持つ
# 複数 hook 横断の pre-existing パターンなので、本 hook だけ塞ぐと規約が割れる
# （正本は `adr.md` ADR-16）。
source "$SCRIPT_DIR/lib/kill-switch.sh"
gdd_kill_switch_active && exit 0

PAYLOAD="$(cat 2>/dev/null || true)"
[[ -n "$PAYLOAD" ]] || exit 0

PYTHON_BIN=""
for _cmd in python3 python; do
  if command -v "$_cmd" >/dev/null 2>&1; then
    PYTHON_BIN="$_cmd"
    break
  fi
done
# python 不在は**無音で** no-op（python 不在の扱いとして決めた判断）。
# `lib/` の欠落は本 plugin の配置ミスなので `run-stop-failure-hook.sh` は理由を
# stderr に残すが、python 不在は環境の性質であって配置ミスではない。Notification
# は入力待ちのたびに発火する高頻度 hook で、環境由来の同じ事実を毎回 stderr に
# 出してもノイズにしかならない。この非対称は意図的で、契約テストで固定してある
# （`test_python_absent_is_a_silent_noop`）。
[[ -n "$PYTHON_BIN" ]] || exit 0

# **payload は stdin で python へ渡す**（env 経由にすると巨大 payload で `execve` が
# E2BIG になり、通知が無症状で消える。T-17 の実測: macOS `ARG_MAX` 1,048,576 /
# Linux `MAX_ARG_STRLEN` 131,072）。python 本体は `-c` のリテラルなので、payload を
# スクリプト本体へ連結しない規約は維持される。
# 解釈できない payload では python が非 0 で抜け、`if !` が受けて通知も出さない
# （`if VAR=$(cmd); then` 形は set -e 下でも非 0 を伝播させない）。
NOTIFICATION_TYPE=""
if ! NOTIFICATION_TYPE="$(printf '%s' "$PAYLOAD" | "$PYTHON_BIN" -c '
import json, sys

try:
    payload = json.loads(sys.stdin.read())
except Exception:
    sys.exit(1)
if not isinstance(payload, dict):
    sys.exit(1)
value = payload.get("notification_type")
# str 以外を文字列化しない。["idle_prompt"] のような値が allowlist に当たる形を作らない。
if isinstance(value, str):
    sys.stdout.write(value)
' 2>/dev/null)"; then
  exit 0
fi

# enforcement point 2: allowlist に対する固定文言の対応表。payload 由来の文字列は
# 右辺に 1 バイトも現れない。allowlist 外はここで no-op に落ちる。
BODY=""
case "$NOTIFICATION_TYPE" in
  idle_prompt) BODY="GDD: セッションが入力待ちで停止しています" ;;
  permission_prompt) BODY="GDD: 権限確認の入力待ちです" ;;
  *) exit 0 ;;
esac

# enforcement point 2: osascript へは文字列連結でスクリプトを組まない。
# `osascript -` に stdin でリテラルを渡し、本文はプロセス環境から読ませる。
# heredoc は必ずクォートする（unquoted だと shell 展開で本文がスクリプト本体に戻る）。
if command -v osascript >/dev/null 2>&1; then
  GDD_NOTIFY_BODY="$BODY" osascript - <<'APPLESCRIPT' >/dev/null 2>&1 || true
display notification (system attribute "GDD_NOTIFY_BODY") with title "GDD"
APPLESCRIPT
elif command -v notify-send >/dev/null 2>&1; then
  # argv 渡し + `--` で option 終端。本文の先頭が `-` でも壊れない。
  notify-send -- "GDD" "$BODY" >/dev/null 2>&1 || true
fi

exit 0

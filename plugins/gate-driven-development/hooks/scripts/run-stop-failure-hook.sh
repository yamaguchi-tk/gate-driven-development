#!/usr/bin/env bash
# StopFailure hook: ターンが API エラー等で異常終了した事実を永続ファイルへ 1 件残し、
# デスクトップ通知を 1 回だけ出す（AC-16 / AC-17）。
#
# payload（error / error_details / session_id / cwd）は Claude Code が生成する値だが、
# hook から見れば untrusted input。design.md § Sensitive Data / Masking Policy の
# enforcement point 1（永続化直前）は lib/stop-failure-record.py が、
# enforcement point 2（通知コマンド呼び出し直前）は本ファイルが強制する。
#
# 設計上の不変条件:
#   - hook は決してターンを壊さない。**射程内のどの経路でも exit 0（fail-open）**。
#     射程は下の「exit 0 の射程」で定義する。**全称ではない**（全称は達成不能）
#   - StopFailure は hook 出力契約（decision / hookSpecificOutput）を使わない。stdout は空
#   - 通知本文は固定文言 + 正規化した error 種別のみ。自由文（error_details）は載せない
#   - 記録の失敗は通知を抑止しない（AC-16 の no-op 条件は「通知コマンドの不在」だけ）
#
# exit 0 の射程（**正本は requirements AC-16 / R1.4**。各形の実測値・網羅の測り方・
# 「測っていない入力空間」は requirements § Correction Log: AC-16 の fail-open 射程を
# 実測で限定（2026-08-26） が正本。**実測値をここへ複写しない**）:
#
#   射程内 ＝ 次の 2 経路だけ
#     (E) **データ I/O の errno 経路**: hook が扱う**データ**の I/O ―― stdin からの
#         payload の read / stdout・stderr への write / 記録先（state dir・record
#         file）への write ―― が errno（EBADF / EPIPE / EIO / ENOSPC 等）で失敗し
#         `set -e` が非 0 に倒す経路 → 書き込み側の `|| true` が受ける
#     (S) シグナル経路: hook 自身の write が原因で届き、**追加の資源制限・端末設定
#         なしの既定環境で成立しうる** trap 可能シグナル → 実測では **SIGPIPE だけ**
#     **プログラム本体（`lib/` 配下のスクリプト）の読み込み失敗は (E) に含めない**
#     （下の射程外「プログラム本体の読み込み失敗」）。この境界は実測に沿う ―― 上の
#     3 種のデータ I/O はどう壊しても exit 0 だが、`source` の失敗だけは `set -e` が
#     非 0 に倒す（NEW-1）
#
#   射程外 ＝ 下の 5 群。**「その他」で済ませず、実測した形は正本に個別列挙する**。
#   ただし射程外は射程内の補集合なので**列挙で尽くせない**（正本が完全性を主張して
#   いるのは `write(2)` / `read(2)` が生成しうるシグナル 4 形についてだけ）
#     1. trap 不能: SIGKILL / SIGSTOP。bash の `trap '' KILL` は**エラーも出さず
#        exit 0 を返す**が、シグナルは止まらない（実測）。＝ 旧字句「どの経路でも
#        exit 0」は**最初から達成不能な全称**であり、trap の書き方では埋められない
#     2. write / read 起因だが**既定では無効な設定**を要する trap 可能シグナル:
#        SIGXFSZ（`RLIMIT_FSIZE`。既定は `RLIM_INFINITY`）/ SIGTTOU（`TOSTOP`。新規
#        pty の既定は off）/ SIGTTIN（background pgrp が ctty から read）
#     3. 外部起因シグナル（**意図的に非対象**）: SIGTERM / SIGINT / SIGHUP / SIGQUIT
#        ほか。ここを exit 0 に倒すと hook が kill 不能になり、ターンの teardown を
#        妨げる
#     4. そもそも終了コードが返らない形（**pre-existing**）: fd 0 閉塞（`$(cat`
#        を持つ 5 hook 共通）/ stderr が full pipe。いずれも block する
#     5. **プログラム本体の読み込み失敗（NEW-1）**: 下の `source` は無防備で、`lib/`
#        を取りこぼす同期が起きると `set -e` が非 0 に倒す。**本 PR では直さない**
#        （複数 hook 横断の規約判断。実測値と横断本数の正本は `adr.md` ADR-16）
#
#   **なぜ限定するか**: 「どの経路でも」と書いていた間、シグナルを 1 つ塞ぐたびに
#   次の 1 つが見つかる形を繰り返した。
#   達成不能な全称を掲げる限りこの追いかけっこは終わらない。射程を列挙に変えると、
#   「閉じた」も「閉じていない」も実測で判定できる。
set -euo pipefail

# 射程 (S) をここで閉じる。SIGPIPE は「終了ステータスが介在しない死」なので、
# 射程 (E) 側の `|| true` では捕まらない（実測: returncode -13）。無視に倒すと
# シグナル死が「ただの write 失敗（EPIPE）」に落ち、`|| true` が受ける形になる。
# **この 1 行が閉じるのは SIGPIPE 1 つだけ**。ファイル全体・全 fd に効くのは
# SIGPIPE についての話であって、「自分の write が原因のシグナル」一般には効かない
# —— 同じ class の SIGXFSZ / SIGTTOU / SIGTTIN は射程外の第 2 群として**未閉鎖のまま**。
# 子プロセスへの継承は無害（実測）: python は起動時に自分で SIGPIPE を SIG_IGN にし、
# subprocess は restore_signals で孫（git）に既定を戻す。osascript / notify-send は
# 出力を /dev/null に捨てるため壊れた書き先を持たない。
trap '' PIPE

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 既知の未閉鎖（NEW-1・本 PR では直さない）: この `source` は無防備で、`lib/` を
# 取りこぼす同期が起きると `set -e` が非 0 に倒す。**冒頭の射程外「プログラム本体の
# 読み込み失敗」であって射程内 (E) ではない** ―― (E) は上のとおりデータ I/O に限る。
# 下の記録 script 欠落の診断ブロックには到達しない。無防備な `source` は
# `set -euo pipefail` を持つ複数 hook 横断の pre-existing パターンで、本 hook だけ
# 塞ぐと規約が割れるため **別 PR** に送る（2026-08-26 ユーザー判断。実測値と横断
# 本数の正本は `adr.md` ADR-16）。
source "$SCRIPT_DIR/lib/kill-switch.sh"
gdd_kill_switch_active && exit 0

RECORD_SCRIPT="$SCRIPT_DIR/lib/stop-failure-record.py"
# 記録本体は外部ファイル。欠落は不完全な配置（lib/ を取りこぼす同期）でしか起きないが、
# 黙って exit 0 すると記録も通知も stderr も 0 バイトで消え、python 自身の診断
# （`can't open file`）まで握り潰される。fail-open は維持したまま理由だけ残す。
# この診断が fail-open を壊さないことは 2 つで担保する。`|| true` が fd 2 の書き込み
# 失敗（fd 2 が閉じた起動の EBADF / 読み手が消えた pipe の EPIPE / ENOSPC）を受け、
# 冒頭の `trap '' PIPE` が SIGPIPE によるプロセス死を受ける。どちらか片方では不足で、
# `|| true` だけだと読み手の消えた pipe で hook がシグナル死する（実測）。
# **これは冒頭で定義した射程内 (E) の話**（この printf は stderr へのデータ I/O）。
# 射程外の第 2 群では、この printf 自体が SIGXFSZ や SIGTTOU を招く ＝ **未閉鎖**。
# ここを「1 形ずつ」塞ぐ方針は採らない（冒頭の理由）。
if [[ ! -f "$RECORD_SCRIPT" ]]; then
  printf 'run-stop-failure-hook: record script missing (%s)\n' "$RECORD_SCRIPT" >&2 || true
  exit 0
fi

PAYLOAD="$(cat 2>/dev/null || true)"
[[ -n "$PAYLOAD" ]] || exit 0

PYTHON_BIN=""
for _cmd in python3 python; do
  if command -v "$_cmd" >/dev/null 2>&1; then
    PYTHON_BIN="$_cmd"
    break
  fi
done
[[ -n "$PYTHON_BIN" ]] || exit 0

# 置き場所は既存 hook state と同じ（design § 論点 3）。repo 内に置くと worktree ごとに
# 分散し、StopFailure 時に cwd が不定だと書き先が割れる。env override は既存 2 実装
# （validate-steering-write.py / lib/self-review-evidence.sh）と同じ名前に揃える。
if [[ -n "${GDD_HOOK_STATE_DIR:-}" ]]; then
  STATE_DIR="$GDD_HOOK_STATE_DIR"
elif [[ -n "${HOME:-}" ]]; then
  STATE_DIR="${HOME}/.claude/.gdd-hook-state"
else
  exit 0
fi

# 抽出 → atomic write → 通知本文の組み立てを python 1 起動でまとめる。
# **payload は stdin で渡す**（env 経由だと巨大 payload で execve が E2BIG になり、
# 記録も通知も無症状で消える。実測: macOS ARG_MAX 1048576 / Linux MAX_ARG_STRLEN 131072）。
# スクリプト本体はファイルなので、payload をスクリプト本体へ連結しない規約は維持される。
# 通知本文は stdout で返る。payload が解釈できないときだけ非 0 で抜けて通知も出さない
# （記録の失敗では非 0 にしない ＝ AC-16 は AC-17 に従属しない）。
# `if VAR=$(cmd); then` の形は set -e 下でも非 0 を伝播させない。
NOTIFY_BODY=""
if NOTIFY_BODY="$(printf '%s' "$PAYLOAD" | STATE_DIR="$STATE_DIR" "$PYTHON_BIN" "$RECORD_SCRIPT")"; then
  # enforcement point 2: osascript へは文字列連結でスクリプトを組まない。
  # `osascript -` に stdin でリテラルを渡し、本文はプロセス環境から読ませる。
  # heredoc は必ずクォートする（unquoted だと shell 展開で本文がスクリプト本体に戻る）。
  if command -v osascript >/dev/null 2>&1; then
    GDD_NOTIFY_BODY="$NOTIFY_BODY" osascript - <<'APPLESCRIPT' >/dev/null 2>&1 || true
display notification (system attribute "GDD_NOTIFY_BODY") with title "GDD"
APPLESCRIPT
  elif command -v notify-send >/dev/null 2>&1; then
    # argv 渡し + `--` で option 終端。本文の先頭が `-` でも壊れない。
    notify-send -- "GDD" "$NOTIFY_BODY" >/dev/null 2>&1 || true
  fi
fi

exit 0

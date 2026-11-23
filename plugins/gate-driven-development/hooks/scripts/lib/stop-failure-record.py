#!/usr/bin/env python3
"""StopFailure の記録 + 通知本文の組み立て（AC-16 / AC-17）。

`run-stop-failure-hook.sh` から起動される。design.md § Sensitive Data / Masking
Policy の enforcement point 1（永続化直前の whitelist + 200 文字切り詰め）と
§ 論点 3（置き場所 / 1 件保持 / mode / project_root / fail-open）をここで強制する。

I/O 契約:

- **payload は stdin** で受け取る。env 経由で渡すと巨大 payload で `execve` が
  E2BIG になり、記録も通知も無症状で消える（実測: macOS `ARG_MAX` 1048576 /
  payload 1,100,080 バイトで exit 0・record 無し。Linux は単一 env 文字列の
  `MAX_ARG_STRLEN` = 131072 とさらに低い）。stdin にはサイズ上限が無い。
- **stdout は通知本文 1 行**（固定文言 + 正規化済み token）。payload を解釈できない
  ときだけ何も書かずに exit 1 で抜け、呼び出し側が通知を抑止する。
- **記録の失敗は通知を抑止しない**。requirements AC-16 の no-op 条件は
  「通知コマンドが存在しない環境」であって「記録の失敗」ではない。ディスクフルや
  `$HOME` が read-only といった記録と無関係な事象で、人間が異常終了に気づく唯一の
  即時シグナルを消さない（AC-16 と AC-17 は独立）。
- 記録できなかった場合は **stderr に理由の型名だけ** を 1 行出す。silent に消さない
  ためだが、例外メッセージは payload 由来の断片を含みうるので本文は載せない。
  この 1 行の write が呼び出し側の hook を壊さない**射程**は
  `run-stop-failure-hook.sh` 冒頭の「exit 0 の射程」に従う ―― この write は
  **射程内 (E)（データ I/O の errno 経路）**に入る。射程内・射程外の内訳と実測値は
  同ヘッダと requirements AC-16（R1.4）/ § Correction Log: AC-16 の fail-open 射程を
  実測で限定（2026-08-26） が正本で、**ここには複写しない**（数値の正本を 1 箇所に
  置く規律。列挙を 4 箇所に複写すると 1 つ直したとき残りが黙って古くなる）。
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

# enforcement point 1: payload から読むキーをホワイトリストに限定する。
# transcript_path の中身・任意の追加キーは読まない。cwd だけは project_root の
# 導出元として読む（design § 論点 3「project キーを持たせる」）。
_LIMITS = {"error": 64, "error_details": 200, "session_id": 64, "cwd": 4096}

# error 種別として妥当な token。通知本文へ載せてよいのはこの形だけ。
# `\Z` は `$` と違い末尾改行を許さないため `fullmatch` と等価。
_TOKEN_RE = re.compile(r"[A-Za-z0-9_.-]{1,64}\Z")

RECORD_NAME = "last-turn-failure.json"
TMP_PREFIX = ".last-turn-failure."


def _scrub(value: str) -> str:
    """UTF-8 にエンコードできない code point（unpaired surrogate）を落とす。

    payload は JSON なので `"\\ud800"` のような単独サロゲートが正当に届きうる
    （API エラー本文が絵文字の途中で切られると自然に起きる）。そのまま
    `json.dump(ensure_ascii=False)` すると **書き込みの途中で** UnicodeEncodeError が
    飛び、記録が丸ごと消える。

    有効な文字列に対しては恒等（実測: `'あ'*5` / 絵文字 / 末尾改行はいずれも不変）で、
    置換しても文字数は変わらないので 200 文字切り詰めの契約に影響しない。
    """
    return value.encode("utf-8", "replace").decode("utf-8")


def _field(payload: dict, key: str) -> str:
    """str 以外は捨てて空文字にする。消費側の shape 検証（各値が str）を書き手側で保証する。

    切り詰めは文字単位。bash の `${var:0:N}` はロケール依存の byte 切りで
    多バイト文字を割り、JSON を壊す（run-session-start-hook.sh に同じ罠の記録あり）。
    """
    value = payload.get(key)
    if not isinstance(value, str):
        return ""
    return _scrub(value[: _LIMITS[key]])


def _project_root(cwd: str) -> str:
    """cwd の git toplevel。導けなければ cwd そのもの（design § 論点 3 M-5）。

    引数リストで渡すので shell は介さない。
    """
    if not cwd or not os.path.isdir(cwd):
        return ""
    git_bin = shutil.which("git")
    if not git_bin:
        return cwd
    try:
        completed = subprocess.run(
            [git_bin, "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True, timeout=10,
        )
    except Exception:
        return cwd
    # bytes で読み、最後の改行だけを落とす（名前の末尾の空白・タブ・CR を残す）。
    out = completed.stdout
    top = os.fsdecode(out[:-1] if out.endswith(b"\n") else out)
    if completed.returncode == 0 and top:
        return top
    return cwd


def _write_record(state_dir: str, record: dict) -> str:
    """記録を atomic に 1 件だけ残す。失敗理由を返し、例外は外に出さない。

    受理する例外を型空間で列挙してから決めている（本 hook のコード経路で実測）:

    - `OSError` 系: makedirs / chmod / mkstemp / write / fsync / replace
      （NotADirectoryError / FileNotFoundError / PermissionError / ENOSPC 等）
    - `ValueError` 系: パスに NUL を含む場合の makedirs / mkstemp / replace と、
      `json.dump` の **UnicodeEncodeError**（UnicodeError -> ValueError）

    （`STATE_DIR` 未設定の `KeyError` は列挙しない。呼び出し側が
    `os.environ.get("STATE_DIR", "")` を渡し、先頭の `if not state_dir` で閉じるため
    この関数には到達しない。）

    `except OSError` は 2 つ目を取りこぼす。取りこぼすと tmp の後始末に到達せず、
    ドットファイルの部分書き込みが state dir に無制限に溜まったまま記録が黙って消える
    （実測: 同一 payload 3 回投入で leftovers 3 / record 無し）。したがってここは
    `except Exception` で受け、**`Exception` 由来のどの経路でも tmp の後始末に到達する**。
    後始末そのものは best-effort（`os.unlink` を `except OSError: pass` で受ける）なので、
    `os.replace` と `os.unlink` が**両方**失敗する経路では tmp が 1 個残る（実測）。

    測っていない外側（限定）: `KeyboardInterrupt` / `SystemExit` / `GeneratorExit` は
    `BaseException` 側なので握り潰さず、**その経路でも tmp が 1 個残る**（実測）。
    `SIGKILL` / `SIGTERM` は例外すら発生しないのでどの `except` でも塞げない。
    残留は 1 起動あたり高々 1 個で、tmp は 0600 なので**他ユーザからの**露出は
    起きない（design § 論点 3 / 消費側の契約 の攻撃者モデルは「同一ユーザ権限の
    任意プロセス」を含み、
    0600 はその読み手を排除しない。ただし残留 tmp が持つデータクラスは正規 record と
    同一なので**新規の攻撃面ではない**）。
    塞いだのは「1 回の失敗で必ず 1 個溜まる」形であって、単調増加そのものではない
    （同じ失敗が続けば溜まりうる。`.last-turn-failure.*` を掃除するコードはツリー内に
    無いため、「溜まらない」という全称の主張にはならない）。
    """
    if not state_dir:
        return "no_state_dir"
    if os.path.islink(state_dir):
        # design § 論点 3 の読み手側 symlink 拒否と同型。state_dir が symlink だと
        # os.chmod と書き込みが追従先に及ぶ（design § 論点 3 / 消費側の契約 が
        # 「同一ユーザ権限の任意プロセス」を攻撃者モデルに含めている以上、
        # 書き手側でも拒否する）。
        return "state_dir_is_symlink"
    tmp_name = None
    try:
        # error_details は API エラー本文のエコー（プロンプト断片 / パス / ID）を
        # 含みうるため、同一ホストの他ユーザから読めない mode に倒す。
        os.makedirs(state_dir, mode=0o700, exist_ok=True)
        try:
            # 既存ディレクトリにも best-effort で適用する（design § 論点 3 / permission）。
            # 同じ state dir を使う既存実装は umask 依存で 0755 を作りうる。
            os.chmod(state_dir, 0o700)
        except OSError:
            pass
        # mkstemp は O_CREAT|O_EXCL かつ mode 0600 で作る（umask 非依存）。
        # tmp は同一ディレクトリに置く（別 FS だと os.replace が失敗する）。
        fd, tmp_name = tempfile.mkstemp(prefix=TMP_PREFIX, suffix=".json", dir=state_dir)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(record, handle, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, os.path.join(state_dir, RECORD_NAME))
    except Exception as exc:  # noqa: BLE001 — 型空間は docstring で列挙済み
        if tmp_name is not None:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
        return type(exc).__name__
    return ""


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except Exception:
        return 1
    if not isinstance(payload, dict):
        return 1

    error = _field(payload, "error")
    record = {
        "error": error,
        "error_details": _field(payload, "error_details"),
        "session_id": _field(payload, "session_id"),
        # timestamp は hook 生成値。payload の timestamp は読まない。
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project_root": _project_root(_field(payload, "cwd")),
    }

    failure = _write_record(os.environ.get("STATE_DIR", ""), record)
    if failure:
        sys.stderr.write("run-stop-failure-hook: record not written (%s)\n" % failure)

    # enforcement point 2: 通知本文は固定文言 + 正規化済み token のみ。
    # error は「種別」であることが payload 側で保証されていないため、token に
    # fullmatch しなければ unknown に置換する（記録側は正規化せず原文を残す）。
    token = error if _TOKEN_RE.match(error) else "unknown"
    sys.stdout.write("GDD: 前回ターンが異常終了しました (%s)" % token)
    return 0


if __name__ == "__main__":
    sys.exit(main())
